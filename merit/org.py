import logging
import datetime

import requests


from .merit import Merit


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


    def __init__(self, app_id: str, app_secret: str, org_id: str, production: bool = True):
        super(Org, self).__init__(app_id, app_secret, production=production)
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


    def get_org_info(self) -> dict:
        """Get Merit information about Organization.

        :return: ..code-block:: json
        {
            "id": "5b442b02b85f223fffe9e851",
            "title": "Millbrae CERT",
            "description": "This is an example Org",
            "website": "http://www.example.com",
            "address": "1001 Broadway, Millbrae, CA, USA",
            "phone": "+1 650-296-9525",
            "email": "admin@example.com",
            "logoUrl": "https://images.sig.ma/5c4f598f774d570006465f9e?rect=0,0,150,150"
        }
        """

        response = self.get_api(f"/orgs/{self.org_id}")

        if response.status_code == 200:
            data = response.json()
            if "id" in data:
                return data
        logger.error(response.text)
        return None


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


    def get_all_org_merit_templates(self, limit: int = 100) -> list:
        """Return a list of all MeritTemplates owned by the Org."""

        response = self.get_api(f"/orgs/{self.org_id}/merittemplates?limit={limit}")

        if response.status_code == 200:
            return response.json().get("merittemplates")
        else:
            logger.error(response.text)
            return []


    def get_org_merit_template_choices(self, include_none: bool = True) -> list:
        """Return a formatted tuple of form choices of available MeritTemplates."""

        choices = []
        if include_none:
            choices.append((None, "-----"))
        for template in self.get_all_org_merit_templates():
            choices.append((template.get("id"), template.get("title")))
        return choices


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


    def get_all_merits(self, template_id: str = None, merit_status: str = None) -> list:
        """Get all Org merits by specifications.

        :param template_id: the ID of the MeritTemplate you wish to retreive
        :param merit_status: the status you wish to filter by

        :return: a `list` of merits issued by the Org, from MeritTemplate `template_id`, with status `merit_status`
        """

        # valid merit_status values are:
        valid_statuses = ["Accepted", "Forfeited", "Pending", "Rejected", "Reported", "Revoked", "Transferred", "TransferredUnverified", "Unapproved", "UnapprovedUnverified", "Unverified"]

        if not merit_status in valid_statuses:
            raise Error(f"Merit Status ({merit_status}) is not valid.  Valid statuses are: ({valid_statuses})")

        params = {
            "merittemplate_id": template_id,
            "merit_status": merit_status,
            "limit": 100,
        }

        response = self.get_api(f"/orgs/{self.org_id}/merits", params)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(response.text)
            return []


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
