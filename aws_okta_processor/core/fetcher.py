"""Module to fetch AWS credentials via SAML authentication with Okta."""

import sys
import json
import hashlib
import boto3  # type: ignore[import-untyped]

from botocore.credentials import CachedCredentialFetcher  # type: ignore[import-untyped]

from aws_okta_processor.core.okta import Okta
from aws_okta_processor.core.tty import print_tty
from aws_okta_processor.core import saml, prompt


class SAMLFetcher(CachedCredentialFetcher):
    """Fetches AWS credentials via SAML authentication with Okta.

    This class handles the retrieval and caching of AWS temporary credentials
    by authenticating with Okta and using the SAML assertion to assume AWS roles.
    """

    def __init__(self, authenticate, cache=None, expiry_window_seconds=600):
        """Initialize the SAMLFetcher.

        Args:
            authenticate: An authentication object that provides methods to interact with Okta.
            cache: An optional cache object to store and retrieve cached credentials.
            expiry_window_seconds: The window (in seconds) before expiry to refresh credentials.
        """  # noqa: E501

        self._authenticate = authenticate
        self._configuration = authenticate.configuration
        super().__init__(cache, expiry_window_seconds)

    def _create_cache_key(self):
        """Creates a unique cache key based on the authentication configuration.

        Returns:
            A string that uniquely identifies the authentication session.
        """
        key_dict = self._authenticate.get_key_dict()
        key_string = json.dumps(key_dict, sort_keys=True)
        key_hash = hashlib.sha1(key_string.encode()).hexdigest()
        return self._make_file_safe(key_hash)

    def fetch_credentials(self):
        """Fetches AWS credentials, using cache if available.

        If caching is disabled or credentials are not cached, it will authenticate
        via Okta and retrieve new credentials.

        Returns:
            A dictionary containing AWS credentials and expiration time.
        """
        if self._configuration["AWS_OKTA_NO_AWS_CACHE"]:
            # Fetch new credentials and write them to cache
            response = self._get_credentials()
            self._write_to_cache(response)

        # Fetch credentials from cache
        credentials = super().fetch_credentials()

        return {
            "AccessKeyId": credentials["access_key"],
            "SecretAccessKey": credentials["secret_key"],
            "SessionToken": credentials["token"],
            "Expiration": credentials["expiry_time"],
        }

    def _get_app_roles(self):
        """Retrieves AWS roles available to the user via Okta.

        Authenticates with Okta to get a SAML assertion, and parses it to get available AWS roles.

        Returns:
            A tuple containing:
                - List of AWS roles
                - SAML assertion
                - Application URL
                - User name
                - Organization name
        """  # noqa: E501
        user = self._configuration["AWS_OKTA_USER"]
        user_pass = self._authenticate.get_pass()
        organization = self._configuration["AWS_OKTA_ORGANIZATION"]
        no_okta_cache = self._configuration["AWS_OKTA_NO_OKTA_CACHE"]

        # Initialize Okta authentication
        okta = Okta(
            user_name=user,
            user_pass=user_pass,
            organization=organization,
            factor=self._configuration["AWS_OKTA_FACTOR"],
            silent=self._configuration["AWS_OKTA_SILENT"],
            no_okta_cache=no_okta_cache,
        )

        # Clear sensitive information from configuration
        self._configuration["AWS_OKTA_USER"] = ""
        self._configuration["AWS_OKTA_PASS"] = ""

        if self._configuration["AWS_OKTA_APPLICATION"]:
            # Use specified application URL
            application_url = self._configuration["AWS_OKTA_APPLICATION"]
        else:
            # Prompt user to select an application
            applications = okta.get_applications()
            application_url = prompt.get_item(
                items=applications,
                label="AWS application",
                key=self._configuration["AWS_OKTA_APPLICATION"],
            )

        # Get SAML response from Okta
        saml_response = okta.get_saml_response(application_url=application_url)
        saml_assertion = saml.get_saml_assertion(saml_response=saml_response)

        if not saml_assertion and not no_okta_cache:
            # Retry without using Okta cache
            print_tty("Creating new Okta session.")
            okta = Okta(
                user_name=user,
                user_pass=user_pass,
                organization=organization,
                factor=self._configuration["AWS_OKTA_FACTOR"],
                silent=self._configuration["AWS_OKTA_SILENT"],
                no_okta_cache=True,
            )
            saml_response = okta.get_saml_response(application_url=application_url)
            saml_assertion = saml.get_saml_assertion(saml_response=saml_response)

        if not saml_assertion:
            # Unable to retrieve SAML assertion
            print_tty("ERROR: SAMLResponse tag was not found!")
            sys.exit(1)

        # Parse SAML assertion to get AWS roles
        aws_roles = saml.get_aws_roles(
            saml_assertion=saml_assertion,
            accounts_filter=self._configuration.get("AWS_OKTA_ACCOUNT_ALIAS", None),
            sign_in_url=self._configuration.get("AWS_OKTA_SIGN_IN_URL", None),
        )

        return (
            aws_roles,
            saml_assertion,
            application_url,
            okta.user_name,
            okta.organization,
        )

    def get_app_roles(self):
        """Public method to get available AWS roles.

        Returns:
            A dictionary containing:
                - Application URL
                - List of AWS accounts and roles
                - User name
                - Organization name
        """
        aws_roles, _, application_url, user, organization = self._get_app_roles()
        return {
            "Application": application_url,
            "Accounts": aws_roles,
            "User": user,
            "Organization": organization,
        }

    def _get_credentials(self):
        """Retrieves AWS temporary credentials by assuming an AWS role via SAML.

        Returns:
            A dictionary containing AWS credentials and expiration time.
        """
        # Do NOT load credentials from ENV or ~/.aws/credentials
        client = boto3.client(
            "sts",
            aws_access_key_id="",
            aws_secret_access_key="",
            aws_session_token="",
            region_name=self._configuration["AWS_OKTA_REGION"],
        )

        # Get available AWS roles and SAML assertion
        aws_roles, saml_assertion, _application_url, user, _organization = (
            self._get_app_roles()
        )

        # Prompt user to select an AWS role
        aws_role = prompt.get_item(
            items=aws_roles, label="AWS Role", key=self._configuration["AWS_OKTA_ROLE"]
        )

        print_tty(
            f"Role: {aws_role.role_arn}", silent=self._configuration["AWS_OKTA_SILENT"]
        )

        # Assume the selected role using the SAML assertion
        response = client.assume_role_with_saml(
            RoleArn=aws_role.role_arn,
            PrincipalArn=aws_role.principal_arn,
            SAMLAssertion=saml_assertion,
            DurationSeconds=int(self._configuration["AWS_OKTA_DURATION"]),
        )

        if self._configuration.get("AWS_OKTA_SECONDARY_ROLE", None) is not None:
            # If secondary role is specified, assume it
            role_session_name = user
            secondary_role_arn = self._configuration["AWS_OKTA_SECONDARY_ROLE"]

            print_tty(f"Assuming secondary role {secondary_role_arn}")
            credentials = response["Credentials"]
            client = boto3.client(
                "sts",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=self._configuration["AWS_OKTA_REGION"],
            )
            response = client.assume_role(
                RoleArn=secondary_role_arn,
                DurationSeconds=int(self._configuration["AWS_OKTA_DURATION"]),
                RoleSessionName=role_session_name,
            )

        # Format expiration time
        expiration = (
            response["Credentials"]["Expiration"].isoformat().replace("+00:00", "Z")
        )
        response["Credentials"]["Expiration"] = expiration

        return response
