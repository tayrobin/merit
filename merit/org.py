import os
import logging
import datetime

import requests

from .merit import Merit
from . import exceptions


# Get an instance of a logger
logging.basicConfig(format='[Merit %(asctime)s %(levelname)s]: %(message)s')
logger = logging.getLogger(__name__)


class Org(Merit):
    """Merit Organizations

    To properly create an instance, begin with :func:`merit.Merit.link_with_merit` flow, retreive an org_access_token, and exchange it for an org_id

    :param app_id: ID for the app, given during creation
    :param app_secret: secret for the app, given during creation
    :param production: specify the environment for your API calls
    :param org_id: ID for the Merit Organization

    :return: `merit.Org` object
    """


    def __init__(self,
        org_id: str = os.getenv("MERIT_ORG_ID"),
        app_id: str = None,
        app_secret: str = None,
        production: bool = True
    ):
        if app_id and app_secret:
            super(Org, self).__init__(app_id, app_secret, production)
        else:
            super(Org, self).__init__()
        self.org_id = org_id
        self.auth_timeout = 3600 # seconds
        self.authenticated_at = None
        self.org_access_token = self.get_org_access_token()


    def get_org_access_token(self) -> str:
        """Call Merit API for Org Access Token."""

        access_url = f"{self.domain}/orgs/{self.org_id}/access"
        logger.info(f"Calling {access_url}")
        response = requests.post(access_url, auth=(self.app_id, self.app_secret))

        if response.status_code == 200:
            self.authenticated_at = datetime.datetime.now()
            self.org_access_token = response.json().get("orgAccessToken")
            return self.org_access_token
        else:
            logger.error(f"{response.text}")
            return None


    def authenticate(self):
        """Get or refresh org_access_token."""

        if not self.org_access_token:
            self.get_org_access_token()
        if (self.authenticated_at < (datetime.datetime.now() - datetime.timedelta(seconds=self.auth_timeout))):
            self.get_org_access_token()


    def get_api(self, path: str, params: dict = None) -> requests.Response:
        """Unified endpoint for all GET calls out to API.

        :param path: the relative path, appended to `domain`, be sure to include a leading slash
        :param params: a `dict` of query params to include

        :return: `requests.response` object
        """

        # authenticate
        self.authenticate()

        # call api
        url = f"{self.domain}{path}"
        headers = {"Authorization": f"Bearer {self.org_access_token}"}
        logger.info(f"Calling {url}")
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response
        else:
            logger.error(f"({response.status_code}) {response.text}")
            return response


    def post_api(self, path: str, data: dict = None) -> requests.Response:
        """Unified endpoint for all POST calls out to API.

        :param path: the relative path, appended to `domain`, be sure to include a leading slash
        :param data: a `dict` of json data to send along with the POST

        :return: a `requests.response` object
        """

        # authenticate
        self.authenticate()

        # call api
        url = f"{self.domain}{path}"
        headers = {"Authorization": f"Bearer {self.org_access_token}"}
        logger.info(f"Calling {url}")
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response
        else:
            logger.error(f"({response.status_code}) {response.text}")
            return response


    def login_with_merit(self, success_url: str, failure_url: str, permissions: list = ["CanViewPublicProfile"], org_ids: list = None) -> str:
        """Initiate process to Login with Merit for a member.

        :param success_url: relative path where Merit will redirect the user after successful authentication
        :param failure_url: relative path where Merit will redirect the user after unsuccessful authentication
        :param permissions: a list of permissions you wish to request from the member
        :param org_ids: a list of org_ids for which you wish to request permission from the member.  Must be included if `CanViewAllStandardMeritsFromOrg` is included in `permissions`.

        :return: URL to redirect user to to begin link_with_merit flow (https://app.merits.com/link-app/?token=5aa5a3992bfa4e0006c47cdf)
        """

        path = f"/orgs/{self.org_id}/request_loginwithmerit_url"

        # validate params
        valid_permissions = ["CanViewPublicProfile", "CanViewAllStandardMeritsFromOrg", "CanViewAllStandardMerits"]
        requested_permissions = []
        if type(permissions) != list:
            raise TypeError("Permission variable must be a list of strings.")
        for permission in permissions:
            if type(permission) != str:
                raise TypeError("Permission variable must be a list of strings.")
            if permission not in valid_permissions:
                raise exceptions.RequestedPermissionException(f"Requested Permissions ({permissions}) is not valid.  Valid Permissions are: ({valid_permissions})")
            # add to list
            requested_permissions.append({"permissionType": permission})

        # org_ids do not get validated
        if "CanViewAllStandardMeritsFromOrg" in permissions:
            if not org_ids:
                raise exceptions.RequestedPermissionException("Permission CanViewAllStandardMeritsFromOrg requested without specifiying org_ids.")
            if type(org_ids) != list:
                raise TypeError("org_ids variable must be a list of strings.")
            for org_id in org_ids:
                if type(org_id) != str:
                    raise TypeError("org_ids variable must be a list of strings.")
                # add to list
                requested_permissions.append({"permissionType": "CanViewAllStandardMeritsFromOrg", "orgId": org_id })

        data = {
            "requestedPermissions": requested_permissions,
            "successUrl": success_url,
            "failureUrl": failure_url,
            "state": f"<3-from-merit-{datetime.datetime.now():%d-%m-%Y-%H-%M-%S}",
        }

        response = self.post_api(path, data=data)

        # {
        #   "request_loginwithmerit_url": "https://sig.ma/login-with-merit/?token=5aa5a3992bfa4e0006c47cdf"
        #   "expiration": "2019-01-31T18:48:51.000Z",
        #   "state": "initiated-from-merit-registration-%d-%m-%Y-%H-%M-%S"
        # }

        if response.status_code == 200:
            url = response.json().get("request_loginwithmerit_url")
            if url:
                return url
        logger.error(response.text)
        return None


    def get_member_id_from_token(self, member_id_token: str) -> str:
        """Exchange member_id_token from login_with_merit for permanent member_id.

        :param member_id_token: the token to exchange

        :return: member_id
        """

        # validate member_id_token
        if type(member_id_token) != str:
            raise TypeError(f"member_id_token {member_id_token} is not a string.")

        response = self.get_api("/member_id", {"member_id_token": member_id_token})

        if response.status_code == 200:
            data = response.json()
            if "memberId" in data:
                return data.get("memberId")
        logger.error(response.text)
        return None


    def get_member_info(self, member_id: str) -> dict:
        """Get Merit information about Member.

        :param member_id: the ID of the Member you wish to retreive

        :return: {"id": "573564e698ae3b96668fd517","name": {"firstName": "Omer","lastName":"Zach"}}
        """

        response = self.get_api(f"/members/{member_id}")

        if response.status_code == 200:
            data = response.json()
            if "id" in data:
                return data
        logger.error(response.text)
        return None


    def get_member_access_merit(self, member_id: str) -> dict:
        """Get Member's Access merit for this app, which returns more details than `get_member_info`

        :param member_id: the ID of the Member you wish to retreive

        :return: a `Merit` dict
        """

        response = self.get_api(f"/members/{member_id}/access_merit")

        if response.status_code == 200:
            data = response.json()
            if "id" in data:
                return data
        logger.error(response.text)
        return None


    def get_member_merits(self, member_id: str, template_id: str = None, limit: int = 100) -> list:
        """Get all Member merits by specifications.

        :param member_id: the ID of the Member you wish to retreive
        :type member_id: str
        :param template_id: the ID of the MeritTemplate you wish to retreive
        :type template_id: str, optional
        :param limit: the number of results you wish to retreive
        :type limit: int, optional

        :return: a list of merits issued owned by the Member, filtered as specified
        :rtype: list
        """

        # validate params
        params = {}
        if type(member_id) != str:
            raise TypeError(f"member_id ({member_id}) must be a string.")
        if type(limit) != int:
            raise TypeError(f"limit ({limit}) must be an integer.")
        params["limit"] = limit
        if template_id:
            if type(template_id) != str:
                raise TypeError(f"template_id ({template_id}) must be a string.")
            params["merittemplate_id"] = template_id

        # init returned list
        merit_list = []
        next_page = True
        while next_page:

            # call api, parse response
            response = self.get_api(f"/members/{member_id}/merits", params)
            if response.status_code == 200:
                data = response.json()
            else:
                logger.error(response.text)
                return merit_list


            # add merits into list
            merit_list.extend(data.get("merits", []))

            # stop at user provided limit
            if len(merit_list) >= limit:
                print(f"stopping at limit {len(merit_list)}")
                return merit_list

            # loop again if more pages
            next_page = data.get("paging", {}).get("pageInfo", {}).get("hasNextPage", False)
            params["starting_after"] = data.get("paging", {}).get("cursors", {}).get("after", "")

        return merit_list


    def member_has_active_merit(self, member_id: str, template_id: str) -> bool:
        """Check whether Member has an active merit from the Template specified.

        :param member_id: the ID of the Member you wish to check
        :param template_id: the ID of the MeritTemplate you wish to check

        :return: a boolean whether the Member passes the test
        :rtype: bool
        """

        # look for first active merit
        for merit in self.get_member_merits(member_id, template_id):
            if merit.get("active") is True:
                return True
        return False


    def get_org_info(self) -> dict:
        """Get Merit information about Organization.

        :return: {"id": "5b442b02b85f223fffe9e851","title": "Millbrae CERT","description": "This is an example Org","website": "http://www.example.com","address": "1001 Broadway, Millbrae, CA, USA","phone": "+1 650-296-9525","email": "admin@example.com","logoUrl": "https://images.sig.ma/5c4f598f774d570006465f9e?rect=0,0,150,150"}
        """

        response = self.get_api(f"/orgs/{self.org_id}")

        if response.status_code == 200:
            data = response.json()
            if "id" in data:
                return data
        logger.error(response.text)
        return None


    def search_orgs(self, query: str) -> list:
        """Search for Organization by name based on provided query.

        :param query: the name you wish to search for
        :type query: str

        :return: a `list` of `dicts` of all Organizations with a matching name.
        :rtype: list
        """

        if len(query) < 3:
            raise exceptions.SearchQueryException("Search query must be longer than 3 characters.")

        response = self.get_api("/orgs/search", {"limit": 10, "search_string": query})

        if response.status_code == 200:
            data = response.json()
            if "results" in data:
                return data.get("results")
        logger.error(response.text)
        return []


    def get_field(self, field_id: str) -> dict:
        """Return details of specified Field.

        :param field_id: the ID of the field you wish to retreive

        :return: a `dict` of the Field's info
        """

        response = self.get_api(f"/fields/{field_id}")

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(response.text)
            return None


    def get_all_org_merit_templates(self, limit: int = 100, org_id: str = None) -> list:
        """Return a list of all MeritTemplates owned by the Org."""

        if not org_id:
            org_id = self.org_id

        response = self.get_api(f"/orgs/{org_id}/merittemplates?limit={limit}")

        if response.status_code == 200:
            return response.json().get("merittemplates")
        else:
            logger.error(response.text)
            return []


    def get_org_merit_template_choices(self, include_none: bool = True) -> list:
        """Return a formatted tuple of form choices of available MeritTemplates."""

        choices = []
        for template in self.get_all_org_merit_templates():
            choices.append((template.get("id"), template.get("title")))
        choices = sorted(choices, key = lambda x: x[1])
        if include_none:
            choices.insert(0, (None, "-----"))


    def get_merit_template(self, template_id: str) -> dict:
        """Return details of specified MeritTemplate.

        :param template_id: the ID of the MeritTemplate you wish to retreive

        :return: all details about that MeritTemplate
        """

        response = self.get_api(f"/merittemplates/{template_id}")

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(response.text)
            return None


    def get_template_field_choices(self, template_id: str) -> list:
        """Return list of fields used in specified Template.

        :param template_id: the ID of the MeritTemplate you wish to retreive

        :return: a list of Field dicts used in that MeritTemplate
        """

        return [self.get_field(field.get("fieldId")) for field in self.get_merit_template(template_id).get("enabledFieldSettings")]


    def get_merit(self, merit_id: str) -> dict:
        """Return details of specified Merit.

        :param merit_id: the ID of the Merit you wish to retreive

        :return: all details about that Merit
        """

        response = self.get_api(f"/orgs/{self.org_id}/merits/{merit_id}")

        if response.status_code == 200:
            return response.json()
        logger.error(response.text)
        return None


    def get_all_merits(self, template_id: str = None, merit_status: str = None, email: str = None, limit: int = 100) -> list:
        """Get all Org merits by specifications.

        :param template_id: the ID of the MeritTemplate you wish to retreive
        :type template_id: str, optional
        :param merit_status: the status you wish to filter by
        :type merit_status: str, optional
        :param email: a member's email you wish to filter by
        :type email: str, optional
        :param limit: the number of results you wish to retreive
        :type limit: int, optional

        :return: a list of merits issued by the Org, filtered as specified
        :rtype: list
        """

        # valid merit_status values are:
        valid_statuses = ["Accepted", "Forfeited", "Pending", "Rejected", "Reported", "Revoked", "Transferred", "TransferredUnverified", "Unapproved", "UnapprovedUnverified", "Unverified"]

        # TODO: allow user to provide a list of statuses
        if merit_status and merit_status not in valid_statuses:
            raise exceptions.MeritStatusException(f"Merit Status ({merit_status}) is not valid.  Valid statuses are: ({valid_statuses})")

        params = {"limit": limit,}
        if merit_status:
            params["merit_status"] = merit_status
        # TODO: allow user to provide a list of template_ids
        if template_id:
            params["merittemplate_id"] = template_id
        # TODO: allow user to provide a list of template_ids
        if email:
            params["recipient_email"] = email

        # init returned list
        merit_list = []
        next_page = True
        while next_page:

            # call api, parse response
            response = self.get_api(f"/orgs/{self.org_id}/merits", params)
            if response.status_code == 200:
                data = response.json()
            else:
                logger.error(response.text)
                return merit_list

            # add merits into list
            merit_list.extend(data.get("merits", []))

            # stop at user provided limit
            if len(merit_list) >= limit:
                return merit_list

            # loop again if more pages
            next_page = data.get("paging", {}).get("pageInfo", {}).get("hasNextPage", False)
            params["starting_after"] = data.get("paging", {}).get("cursors", {}).get("after", "")

        return merit_list


    def get_template_pending_merits(self, template_id: str) -> list:
        """Return all proposed merits from site MeritTemplate.

        :param template_id: the ID of the MeritTemplate you wish to retreive

        :return: a `list` of all merits matching criteria
        """

        return self.get_all_org_merits(template_id, "Unapproved")


    def propose_merit(self, data: dict) -> str:
        """Propose a merit as specified.

        :param data: a full `dict` ready to be proposed as a merit

        :return: the ID of the proposed merit
        """

        response = self.post_api("/merits/propose", data)

        if response.status_code == 200:
            id = response.json().get("id")
            if id:
                return id
        else:
            logger.error(response.text)
            return None


    def send_merit(self, data: dict) -> str:
        """Send merit as specified.

        :param data: a full `dict` ready to be sent as a merit

        :return: the ID of the sent merit
        """

        response = self.post_api("/merits/send", data)

        if response.status_code == 200:
            id = response.json().get("id")
            if id:
                return id
        else:
            logger.error(response.text)
            return None


    def edit_merit(self, merit_id: str, data: dict) -> bool:
        """Edit specified merit.

        :param merit_id: the ID of the merit to edit
        :param data: a `dict` with the edits you wish to make

        :return: a `bool` indicating the status of the edit
        """

        response = self.post_api(f"/merits/{merit_id}", data)

        if response.status_code == 200:
            return True
        else:
            logger.error(response.text)
            return False


    def revoke_merit(self, merit_id: str, reason: str) -> bool:
        """Revoke specified merit.

        :param merit_id: the ID of the merit to edit
        :param reason: the reason for revoking the merit

        :return: a `bool` indicating the status of the revocation
        """

        response = self.post_api(f"/merits/{merit_id}/revoke", {"revocationReason": reason})

        if response.status_code == 200:
            return True
        else:
            logger.error(response.text)
            return False


    def uuid_translation(self, merit_id: str, email: str) -> str:
        """Translated a given Member's email into a static QR URL

        :param merit_id: the ID of the merit to translate
        :param email: the email of the Member to translate

        :return: a `URL` of the static lookup link
        """

        response = self.post_api(f"/uuidTranslation/merit/{merit_id}/email/{email}")

        if response.status_code == 200:
            return response.json().get("translationUrl")
        else:
            logger.error(response.text)
            return None


    def update_email(self, merit_id: str, email: str) -> str:
        """Transfer merit to new email address.

        :param merit_id: the ID of the merit to transfer
        :param email: the new email for the Member

        :return: the ID of the new merit
        """

        response = self.post_api(f"/merits/{merit_id}/transfer", {"newRecipientEmail": email})

        if response.status_code == 200:
            new_merit = response.json().get("newMerit")
            if new_merit:
                return new_merit.get("id")
            return None
        else:
            logger.error(response.text)
            return None
