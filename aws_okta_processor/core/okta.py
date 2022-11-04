import abc
import os
import sys
import time
import json
import requests
import dateutil
import getpass
import aws_okta_processor.core.prompt as prompt

from datetime import datetime
from datetime import timedelta
from datetime import tzinfo
from requests import ConnectTimeout
from requests import ConnectionError
from collections import OrderedDict
from aws_okta_processor.core.tty import print_tty, input_tty
from six import add_metaclass


OKTA_AUTH_URL = "https://{}/api/v1/authn"
OKTA_SESSION_URL = "https://{}/api/v1/sessions"
OKTA_REFRESH_URL = "https://{}/api/v1/sessions/me/lifecycle/refresh"
OKTA_APPLICATIONS_URL = "https://{}/api/v1/users/me/appLinks"

ZERO = timedelta(0)


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


class Okta:
    def __init__(
            self,
            user_name=None,
            user_pass=None,
            organization=None,
            factor=None,
            silent=None,
            no_okta_cache=None
    ):
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

            self.refresh_okta_session_id(
                okta_session=okta_session
            )

        if not self.organization:
            print_tty(string="Organization: ", newline=False)
            self.organization = input_tty()

        if not self.user_name:
            print_tty(string="UserName: ", newline=False)
            self.user_name = input_tty()

        if not self.okta_session_id:
            if not self.user_name:
                print_tty(string="UserName: ", newline=False)
                self.user_name = input_tty()

            if not user_pass:
                user_pass = getpass.getpass()

            if not self.organization:
                print_tty(string="Organization: ", newline=False)
                self.organization = input_tty()

            self.okta_single_use_token = self.get_okta_single_use_token(
                user_name=self.user_name,
                user_pass=user_pass
            )

            # This call sets self.okta_session_id
            self.create_and_store_okta_session()

    def read_aop_from_okta_session(self, okta_session):
        if "aws-okta-processor" in okta_session:
            aop_options = okta_session["aws-okta-processor"]
            self.user_name = aop_options.get("user_name", None)
            self.organization = aop_options.get("organization", None)

            del okta_session["aws-okta-processor"]

    def get_cache_file_path(self):
        """ Returns the file path for the session cache file:
        ~/.aws-okta-processor/cache/<username>-<organization>-session.json
        """
        home_directory = os.path.expanduser('~')
        cache_directory = os.path.join(
            home_directory,
            '.aws-okta-processor',
            'cache'
        )

        if not os.path.isdir(cache_directory):
            os.makedirs(cache_directory)

        cache_file_name = "{}-{}-session.json".format(
            self.user_name,
            self.organization
        )

        cache_file_path = os.path.join(cache_directory, cache_file_name)

        return cache_file_path

    def set_okta_session(self, okta_session=None):
        """ Saves the given Okta session in our cache file. """
        session_data = dict(okta_session, **{
            "aws-okta-processor": {
                "user_name": self.user_name,
                "organization": self.organization
            }
        })
        with open(self.cache_file_path, "w") as file:
            json.dump(session_data, file)

        os.chmod(self.cache_file_path, 0o600)

    def get_okta_session_from_cache_file(self):
        session = {}

        if os.path.isfile(self.cache_file_path):
            with open(self.cache_file_path) as file:
                session = json.load(file)

        return session

    def get_okta_single_use_token(self, user_name=None, user_pass=None):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }

        json_payload = {
            "username": user_name,
            "password": user_pass
        }

        response = self.call(
            endpoint=OKTA_AUTH_URL.format(self.organization),
            headers=headers,
            json_payload=json_payload
        )

        response_json = {}

        try:
            response_json = response.json()
        except ValueError:
            send_error(response=response, json=False)

        if "sessionToken" in response_json:
            return response_json["sessionToken"]

        if "status" in response_json:
            if response_json["status"] == "MFA_REQUIRED":
                return self.handle_factor(response_json=response_json)

        send_error(response=response)

    def handle_factor(self, response_json=None):
        state_token = response_json["stateToken"]
        factors = get_supported_factors(
            factors=response_json["_embedded"]["factors"]
        )

        factor = prompt.get_item(
            items=factors,
            label="Factor",
            key=self.factor
        )

        return self.verify_factor(factor=factor, state_token=state_token)

    def verify_factor(self, factor=None, state_token=None):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }

        json_payload = factor.payload()
        json_payload.update({"stateToken": state_token})

        response = self.call(
            endpoint=factor.link,
            headers=headers,
            json_payload=json_payload
        )

        response_json = {}

        try:
            response_json = response.json()
        except ValueError:
            send_error(response=response, json=False)

        if "sessionToken" in response_json:
            return response_json["sessionToken"]

        if factor.retry(response_json):
            factor.link = response_json["_links"]["next"]["href"]
            time.sleep(1)
            return self.verify_factor(
                factor=factor,
                state_token=state_token
            )

        send_error(response=response)

    def create_and_store_okta_session(self):
        """ Creates a new Okta session and caches it in our cache file for future use.
        https://developer.okta.com/docs/reference/api/sessions/#get-started
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        json_payload = {
            "sessionToken": self.okta_single_use_token
        }

        response = self.call(
            endpoint=OKTA_SESSION_URL.format(self.organization),
            json_payload=json_payload,
            headers=headers
        )

        try:
            response_json = response.json()
            self.okta_session_id = response_json["id"]
            self.set_okta_session(okta_session=response_json)
        except KeyError:
            send_error(response=response)
        except ValueError:
            send_error(response=response, json=False)

    def refresh_okta_session_id(self, okta_session=None):
        session_expires = dateutil.parser.parse(
            okta_session["expiresAt"]
        )

        if (datetime.now(UTC()) <
                (session_expires - timedelta(seconds=30))):
            headers = {
                "Cookie": "sid={}".format(okta_session["id"]),
                "Accept": "application/json",
                "Content-Type": "application/json"
            }

            response = self.call(
                endpoint=OKTA_REFRESH_URL.format(self.organization),
                headers=headers,
                json_payload={}
            )

            try:
                response_json = response.json()
                self.okta_session_id = okta_session["id"]
                okta_session["expiresAt"] = response_json["expiresAt"]
                self.set_okta_session(okta_session=okta_session)
            except KeyError:
                send_error(response=response, exit=False)
            except ValueError:
                send_error(response=response, json=False, exit=False)

    def get_applications(self):
        applications = OrderedDict()

        headers = {
            "Cookie": "sid={}".format(self.okta_session_id),
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = self.call(
            endpoint=OKTA_APPLICATIONS_URL.format(self.organization),
            headers=headers
        )

        for application in response.json():
            if application["appName"] == "amazon_aws":
                label = application["label"].rstrip()
                link_url = application["linkUrl"]
                applications[label] = link_url

        return applications

    def get_saml_response(self, application_url=None):
        headers = {
            "Cookie": "sid={}".format(self.okta_session_id)
        }

        response = self.call(application_url, headers=headers)

        return response.content.decode()

    def call(self, endpoint=None, headers=None, json_payload=None):
        print_tty(
            "Info: Calling {}".format(endpoint),
            silent=self.silent
        )

        try:
            if json_payload is not None:
                return self.session.post(
                    endpoint,
                    json=json_payload,
                    headers=headers,
                    timeout=10
                )
            else:
                return self.session.get(
                    endpoint,
                    headers=headers,
                    timeout=10
                )

        except ConnectTimeout:
            print_tty("Error: Timed Out")
            sys.exit(1)

        except ConnectionError:
            print_tty("Error: Connection Error")
            sys.exit(1)


def get_supported_factors(factors=None):
    matching_factors = OrderedDict()

    for factor in factors:
        try:
            supported_factor = FactorBase.factory(factor["factorType"])

            key = '{}:{}'.format(
                factor["factorType"], factor["provider"]).lower()
            matching_factors[key] = supported_factor(
                link=factor["_links"]["verify"]["href"]
            )
        except NotImplementedError:
            pass

    return matching_factors


def send_error(response=None, json=True, exit=True):
    print_tty("Error: Status Code: {}".format(response.status_code))

    if json:
        response_json = response.json()

        if "status" in response_json:
            print_tty("Error: Status: {}".format(
                response_json['status']
            ))

        if "errorSummary" in response_json:
            print_tty("Error: Summary: {}".format(
                response_json['errorSummary']
            ))
    else:
        print_tty("Error: Invalid JSON")

    if exit:
        sys.exit(1)


class FactorType:
    PUSH = "push"
    TOTP = "token:software:totp"
    HARDWARE = "token:hardware"


@add_metaclass(abc.ABCMeta)
class FactorBase(object):
    def __init__(self, link=None):
        self.link = link

    @classmethod
    def factory(cls, factor):
        for impl in cls.__subclasses__():
            if factor == impl.factor:
                return impl
        raise NotImplementedError("Factor type not implemented: %s" % factor)

    @abc.abstractmethod
    def payload():
        """Returns dictionary with payload to verify factor-type."""
        pass

    @abc.abstractmethod
    def retry(self, response):
        """Returns boolean indicating whether response is retryable."""
        pass


class FactorPush(FactorBase):
    factor = FactorType.PUSH

    def __init__(self, link=None):
        super(FactorPush, self).__init__(link=link)

        self.RETRYABLE_RESULTS = [
            "WAITING",
        ]

    @staticmethod
    def payload():
        return {}

    def retry(self, response):
        return response.get("factorResult") in self.RETRYABLE_RESULTS


class FactorTOTP(FactorBase):
    factor = FactorType.TOTP

    def __init__(self, link=None):
        super(FactorTOTP, self).__init__(link=link)

    @staticmethod
    def payload():
        print_tty("Token: ", newline=False)
        return {"passCode": input_tty()}

    def retry(self, response):
        return False


class FactorHardwareToken(FactorBase):
    factor = FactorType.HARDWARE

    def __init__(self, link=None):
        super(FactorHardwareToken, self).__init__(link=link)

    @staticmethod
    def payload():
        print_tty("Hardware Token: ", newline=False)
        return {"passCode": input_tty()}

    def retry(self, response):
        return False
