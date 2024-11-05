"""Module for handling Okta authentication and MFA."""

import abc
import os
import sys
import time
import json
import datetime

from collections import OrderedDict

import getpass
from enum import Enum

import dateutil  # type: ignore[import-untyped]
import requests  # type: ignore[import-untyped]

from six import add_metaclass  # type: ignore[import-untyped]
from aws_okta_processor.core import prompt
from aws_okta_processor.core.tty import print_tty, input_tty


OKTA_AUTH_URL = "https://{}/api/v1/authn"
OKTA_SESSION_URL = "https://{}/api/v1/sessions"
OKTA_REFRESH_URL = "https://{}/api/v1/sessions/me/lifecycle/refresh"
OKTA_APPLICATIONS_URL = "https://{}/api/v1/users/me/appLinks"

ZERO = datetime.timedelta(0)


class UTC(datetime.tzinfo):
    """UTC Timezone class."""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


class Okta:  # pylint: disable=R0902
    """Okta authentication class."""

    def __init__(  # pylint: disable=R0913,R0917
        self,
        user_name=None,
        user_pass=None,
        organization=None,
        factor=None,
        silent=None,
        no_okta_cache=None,
    ):
        """
        Initialize Okta authentication with optional parameters.

        Attempts to use a cached session if available and valid.
        If not, prompts the user for necessary credentials and creates a new session.

        Parameters:
            user_name (str): The Okta username.
            user_pass (str): The Okta password.
            organization (str): The Okta organization domain.
            factor (str): The preferred MFA factor.
            silent (bool): If True, suppresses output.
            no_okta_cache (bool): If True, does not use cached Okta session.
        """
        # Initialize instance variables
        self.user_name = user_name
        self.silent = silent
        self.factor = factor
        self.session = requests.Session()
        self.organization = organization
        self.okta_session_id = None
        self.cache_file_path = self.get_cache_file_path()

        okta_session = None

        if not no_okta_cache:
            # Get session from cache
            okta_session = self.get_okta_session_from_cache_file()

        if okta_session:
            # Refresh the session ID of the cached session
            self.read_aop_from_okta_session(okta_session)
            self.refresh_okta_session_id(okta_session=okta_session)

        if not self.organization:
            # Prompt for organization if not provided
            print_tty(string="Organization: ", newline=False)
            self.organization = input_tty()

        if not self.user_name:
            # Prompt for username if not provided
            print_tty(string="UserName: ", newline=False)
            self.user_name = input_tty()

        if not self.okta_session_id:
            # No valid session ID, proceed to authenticate
            if not self.user_name:
                print_tty(string="UserName: ", newline=False)
                self.user_name = input_tty()

            if not user_pass:
                # Prompt for password if not provided
                user_pass = getpass.getpass("Password: ")

            if not self.organization:
                print_tty(string="Organization: ", newline=False)
                self.organization = input_tty()

            # Obtain a single-use token
            self.okta_single_use_token = self.get_okta_single_use_token(
                user_name=self.user_name, user_pass=user_pass
            )

            # This call sets self.okta_session_id
            self.create_and_store_okta_session()

    def read_aop_from_okta_session(self, okta_session):
        """
        Reads and sets the user_name and organization from the cached Okta session.

        Parameters:
            okta_session (dict): The cached Okta session data.
        """
        if "aws-okta-processor" in okta_session:
            aop_options = okta_session["aws-okta-processor"]
            self.user_name = aop_options.get("user_name", None)
            self.organization = aop_options.get("organization", None)

            del okta_session["aws-okta-processor"]

    def get_cache_file_path(self):
        """Returns the file path for the session cache file:
        ~/.aws-okta-processor/cache/<username>-<organization>-session.json
        """
        home_directory = os.path.expanduser("~")
        cache_directory = os.path.join(home_directory, ".aws-okta-processor", "cache")

        if not os.path.isdir(cache_directory):
            os.makedirs(cache_directory)

        cache_file_name = f"{self.user_name}-{self.organization}-session.json"

        cache_file_path = os.path.join(cache_directory, cache_file_name)

        return cache_file_path

    def set_okta_session(self, okta_session=None):
        """
        Saves the given Okta session in our cache file.

        Parameters:
            okta_session (dict): The Okta session data to be saved.
        """
        session_data = dict(
            okta_session,
            **{
                "aws-okta-processor": {
                    "user_name": self.user_name,
                    "organization": self.organization,
                }
            },
        )
        with open(self.cache_file_path, "w", encoding="utf-8") as file:
            json.dump(session_data, file)

        os.chmod(self.cache_file_path, 0o600)

    def get_okta_session_from_cache_file(self):
        """
        Retrieves the Okta session from the cache file.

        Returns:
            dict: The cached Okta session data, or an empty dict if not found.
        """
        session = {}

        if os.path.isfile(self.cache_file_path):
            with open(self.cache_file_path, encoding="utf-8") as file:
                session = json.load(file)

        return session

    def get_okta_single_use_token(self, user_name=None, user_pass=None):
        """
        Authenticates the user and obtains a single-use Okta session token.

        Parameters:
            user_name (str): The Okta username.
            user_pass (str): The Okta password.

        Returns:
            str: The Okta session token.

        Raises:
            SystemExit: If authentication fails.
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

        json_payload = {"username": user_name, "password": user_pass}

        response = self.call(
            endpoint=OKTA_AUTH_URL.format(self.organization),
            headers=headers,
            json_payload=json_payload,
        )

        response_json = {}

        try:
            response_json = response.json()
        except ValueError:
            return send_error(response=response, _json=False)

        if "sessionToken" in response_json:
            return response_json["sessionToken"]

        if "status" in response_json:
            if response_json["status"] == "MFA_REQUIRED":
                return self.handle_factor(response_json=response_json)

        return send_error(response=response)

    def handle_factor(self, response_json=None):
        """
        Handles multi-factor authentication (MFA) when required.

        Parameters:
            response_json (dict): The response from Okta requiring MFA.

        Returns:
            str: The Okta session token after successful MFA.

        Raises:
            SystemExit: If MFA verification fails.
        """
        state_token = response_json["stateToken"]
        factors = get_supported_factors(factors=response_json["_embedded"]["factors"])

        factor = prompt.get_item(items=factors, label="Factor", key=self.factor)

        return self.verify_factor(factor=factor, state_token=state_token)

    def verify_factor(self, factor=None, state_token=None):
        """
        Verifies the selected MFA factor.

        Parameters:
            factor (FactorBase): The MFA factor object.
            state_token (str): The state token from Okta.

        Returns:
            str: The Okta session token after successful MFA verification.

        Raises:
            SystemExit: If MFA verification fails.
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

        json_payload = factor.payload()
        json_payload.update({"stateToken": state_token})

        response = self.call(
            endpoint=factor.link, headers=headers, json_payload=json_payload
        )

        response_json = {}

        try:
            response_json = response.json()
        except ValueError:
            return send_error(response=response, _json=False)

        if "sessionToken" in response_json:
            return response_json["sessionToken"]

        if factor.retry(response_json):
            factor.link = response_json["_links"]["next"]["href"]
            time.sleep(1)
            return self.verify_factor(factor=factor, state_token=state_token)

        return send_error(response=response)

    def create_and_store_okta_session(self):
        """
        Creates a new Okta session and caches it in our cache file for future use.

        https://developer.okta.com/docs/reference/api/sessions/#get-started

        Raises:
            SystemExit: If session creation fails.
        """
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        json_payload = {"sessionToken": self.okta_single_use_token}

        response = self.call(
            endpoint=OKTA_SESSION_URL.format(self.organization),
            json_payload=json_payload,
            headers=headers,
        )

        try:
            response_json = response.json()
            self.okta_session_id = response_json["id"]
            self.set_okta_session(okta_session=response_json)
        except KeyError:
            send_error(response=response)
        except ValueError:
            send_error(response=response, _json=False)

    def refresh_okta_session_id(self, okta_session=None):
        """
        Refreshes the Okta session ID if the session is still valid.

        Parameters:
            okta_session (dict): The existing Okta session data.

        Raises:
            SystemExit: If session refresh fails.
        """
        session_expires = dateutil.parser.parse(okta_session["expiresAt"])

        if datetime.datetime.now(UTC()) < (
            session_expires - datetime.timedelta(seconds=30)
        ):
            headers = {
                "Cookie": f"sid={okta_session['id']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            response = self.call(
                endpoint=OKTA_REFRESH_URL.format(self.organization),
                headers=headers,
                json_payload={},
            )

            try:
                response_json = response.json()
                self.okta_session_id = okta_session["id"]
                okta_session["expiresAt"] = response_json["expiresAt"]
                self.set_okta_session(okta_session=okta_session)
            except KeyError:
                send_error(response=response, _exit=False)
            except ValueError:
                send_error(response=response, _json=False, _exit=False)

    def get_applications(self):
        """
        Retrieves the list of Okta applications for the user.

        Returns:
            OrderedDict: A mapping of application labels to their URLs.
        """
        applications = OrderedDict()

        headers = {
            "Cookie": f"sid={self.okta_session_id}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        response = self.call(
            endpoint=OKTA_APPLICATIONS_URL.format(self.organization), headers=headers
        )

        for application in response.json():
            if application["appName"] == "amazon_aws":
                label = application["label"].rstrip()
                link_url = application["linkUrl"]
                applications[label] = link_url

        return applications

    def get_saml_response(self, application_url=None):
        """
        Retrieves the SAML response for the specified application URL.

        Parameters:
            application_url (str): The URL of the application to retrieve SAML response from.

        Returns:
            str: The SAML response content.
        """  # noqa: E501
        headers = {"Cookie": f"sid={self.okta_session_id}"}

        response = self.call(application_url, headers=headers)

        return response.content.decode()

    def call(self, endpoint=None, headers=None, json_payload=None):
        """
        Makes an HTTP GET or POST request to the specified endpoint.

        Parameters:
            endpoint (str): The URL to send the request to.
            headers (dict): The HTTP headers to include in the request.
            json_payload (dict): The JSON payload for POST requests.

        Returns:
            Response: The HTTP response object.

        Raises:
            SystemExit: If a connection error or timeout occurs.
        """
        print_tty(f"Info: Calling {endpoint}", silent=self.silent)

        try:
            if json_payload is not None:
                return self.session.post(
                    endpoint, json=json_payload, headers=headers, timeout=10
                )

            return self.session.get(endpoint, headers=headers, timeout=10)

        except requests.ConnectTimeout:
            print_tty("Error: Timed Out")
            sys.exit(1)

        except requests.ConnectionError:
            print_tty("Error: Connection Error")
            sys.exit(1)


def get_supported_factors(factors=None):
    """
    Filters and returns the supported MFA factors from the given list.

    Parameters:
        factors (list): A list of factor dictionaries from Okta.

    Returns:
        OrderedDict: A mapping of factor keys to FactorBase instances.
    """
    matching_factors = OrderedDict()

    for factor in factors:
        try:
            supported_factor = FactorBase.factory(factor["factorType"])

            key = f"{factor['factorType']}:{factor['provider']}".lower()
            matching_factors[key] = supported_factor(
                link=factor["_links"]["verify"]["href"]
            )
        except NotImplementedError:
            pass

    return matching_factors


def send_error(response=None, _json=True, _exit=True):
    """
    Handles and prints error messages from HTTP responses.

    Parameters:
        response (Response): The HTTP response object.
        _json (bool): Whether to parse and display JSON error details.
        _exit (bool): Whether to exit the program after printing the error.

    Returns:
        None
    """
    print_tty(f"Error: Status Code: {response.status_code}")

    if _json:
        response_json = response.json()

        if "status" in response_json:
            print_tty(f"Error: Status: {response_json['status']}")

        if "errorSummary" in response_json:
            print_tty(f"Error: Summary: {response_json['errorSummary']}")
    else:
        print_tty("Error: Invalid JSON")

    if _exit:
        sys.exit(1)


class FactorType(str, Enum):  # pylint: disable=R0903
    """Factor types supported by Okta."""

    PUSH = "push"
    TOTP = "token:software:totp"
    HARDWARE = "token:hardware"


@add_metaclass(abc.ABCMeta)
class FactorBase:
    """
    Abstract base class for different MFA factor types.
    """

    factor: FactorType

    def __init__(self, link=None):
        """
        Initializes the factor with a verification link.

        Parameters:
            link (str): The verification link for the factor.
        """
        self.link = link

    @classmethod
    def factory(cls, factor):
        """
        Factory method to create a factor instance based on the factor type.

        Parameters:
            factor (str): The factor type.

        Returns:
            FactorBase: An instance of a subclass of FactorBase.

        Raises:
            NotImplementedError: If the factor type is not implemented.
        """
        for impl in cls.__subclasses__():
            if factor == impl.factor:
                return impl
        raise NotImplementedError(f"Factor type not implemented: {factor}")

    @staticmethod
    @abc.abstractmethod
    def payload():
        """
        Returns a dictionary with the payload to verify the factor type.

        Must be implemented by subclasses.
        """

    @abc.abstractmethod
    def retry(self, response):
        """
        Determines whether the factor verification should be retried based on the response.

        Parameters:
            response (dict): The response from the factor verification attempt.

        Returns:
            bool: True if the verification should be retried, False otherwise.

        Must be implemented by subclasses.
        """  # noqa: E501


class FactorPush(FactorBase):
    """
    Handles Okta Verify Push MFA factor.
    """

    factor = FactorType.PUSH

    def __init__(self, link=None):
        super().__init__(link=link)
        self.RETRYABLE_RESULTS = ["WAITING"]  # pylint: disable=C0103

    @staticmethod
    def payload():
        """
        Returns an empty payload for push verification.
        """
        return {}

    def retry(self, response):
        """
        Checks if the push verification should be retried.

        Parameters:
            response (dict): The response from the factor verification attempt.

        Returns:
            bool: True if the factor result is 'WAITING', False otherwise.
        """
        return response.get("factorResult") in self.RETRYABLE_RESULTS


class FactorTOTP(FactorBase):
    """
    Handles TOTP MFA factors like Google Authenticator.
    """

    factor = FactorType.TOTP

    def __init__(self, link=None):
        super().__init__(link=link)

    @staticmethod
    def payload():
        """
        Prompts the user for a TOTP passcode.

        Returns:
            dict: The payload containing the passcode.
        """
        return {"passCode": getpass.getpass("Token: ")}

    def retry(self, response):
        """
        TOTP verification does not support retries.

        Parameters:
            response (dict): The response from the factor verification attempt.

        Returns:
            bool: False always.
        """
        return False


class FactorHardwareToken(FactorBase):
    """
    Handles hardware token MFA factors.
    """

    factor = FactorType.HARDWARE

    def __init__(self, link=None):
        super().__init__(link=link)

    @staticmethod
    def payload():
        """
        Prompts the user for a hardware token passcode.

        Returns:
            dict: The payload containing the passcode.
        """
        return {"passCode": getpass.getpass("Hardware Token: ")}

    def retry(self, response):
        """
        Hardware token verification does not support retries.

        Parameters:
            response (dict): The response from the factor verification attempt.

        Returns:
            bool: False always.
        """
        return False
