import logging
import datetime

import requests


# Get an instance of a logger
logging.basicConfig(format='[Merit %(asctime)s %(levelname)s]: %(message)s')
logger = logging.getLogger(__name__)


class Merit:
    """Handler for basic non-Org-authenticated Merit API calls.

    :param app_id: ID for the app, given during creation
    :param app_secret: secret for the app, given during creation
    :param production: specify the environment for your API calls

    :return: Merit object
    """


    def __init__(self, app_id: str, app_secret: str, production: bool = True):

        self.app_id = app_id
        self.app_secret = app_secret
        if production:
            self.domain = "https://api.merits.com/v2"
        else:
            self.domain = "https://sandbox-api.merits.com/v2"


    def link_with_merit(self, success_url: str, failure_url: str) -> str:
        """Initiate process to link Merit Org to this app.

        :param success_url: relative path where Merit will redirect the user after successful authentication
        :param failure_url: relative path where Merit will redirect the user after unsuccessful authentication

        :return: URL to redirect user to to begin link_with_merit flow (https://app.merits.com/link-app/?token=5aa5a3992bfa4e0006c47cdf)
        """

        url = f"{self.domain}/request_linkapp_url"

        data = {
            "requestedPermissions": [{ "permissionType": "CanManageOrg" }],
            "successUrl": success_url,
            "failureUrl": failure_url,
            "state": f"initiated-from-merit-registration-{datetime.datetime.now():%d-%m-%Y-%H-%M-%S}",
        }

        logger.info(f"calling: {url}")
        response = requests.post(url, json=data, auth=(self.app_id, self.app_secret))

        #{
        #  "request_linkapp_url": "https://app.merits.com/link-app/?token=5aa5a3992bfa4e0006c47cdf"
        #  "expiration": "2019-01-31T18:48:51.000Z"
        #}

        if response.status_code == 200:
            url = response.json().get("request_linkapp_url")
            if url:
                return url
        logger.error(response.text)
        return None


    def get_org_id_from_token(self, org_id_token: str) -> str:
        """Exchange org_id_token from link_with_merit flow for permanent org_id.

        :param org_id_token: Org ID Token returned from :func:`link_with_merit` flow

        :return: Org ID for the properly authenticated Org
        """

        url =  f"{self.domain}/org_id?org_id_token={org_id_token}"

        logger.info(f"calling {url}")
        response = requests.get(url, auth=(self.app_id, self.app_secret))

        if response.status_code == 200:
            org_id = response.json().get("orgId")
            if org_id:
                self.org_id = org_id
                return org_id
        logger.error(response.text)
        return None
