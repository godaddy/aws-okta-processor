import boto3
import json
import aws_okta_processor.core.saml as saml
import aws_okta_processor.core.prompt as prompt

from hashlib import sha1
from aws_okta_processor.core.okta import Okta
from botocore.credentials import CachedCredentialFetcher
from aws_okta_processor.core.print_tty import print_tty


class SAMLFetcher(CachedCredentialFetcher):
    def __init__(self, authenticate, cache=None, expiry_window_seconds=600):
        self._authenticate = authenticate
        self._configuration = authenticate.configuration
        self._cache = cache
        self._stored_cache_key = None
        self._expiry_window_seconds = expiry_window_seconds

    @property
    def _cache_key(self):
        if self._stored_cache_key is None:
            self._stored_cache_key = self._create_cache_key()
        return self._stored_cache_key

    def _create_cache_key(self):
        key_dict = self._authenticate.get_key_dict()
        key_string = json.dumps(key_dict, sort_keys=True)
        key_hash = sha1(key_string.encode()).hexdigest()
        return self._make_file_safe(key_hash)

    def fetch_credentials(self):
        if self._configuration["AWS_OKTA_NO_AWS_CACHE"]:
            response = self._get_credentials()
            self._write_to_cache(response)

        credentials = super(SAMLFetcher, self).fetch_credentials()

        return {
            'AccessKeyId': credentials['access_key'],
            'SecretAccessKey': credentials['secret_key'],
            'SessionToken': credentials['token'],
            'Expiration': credentials['expiry_time']
        }

    def _get_credentials(self):
        # Do NOT load credentials from ENV or ~/.aws/credentials
        client = boto3.client(
            'sts',
            aws_access_key_id='',
            aws_secret_access_key='',
            aws_session_token=''
        )

        okta = Okta(
            user_name=self._configuration["AWS_OKTA_USER"],
            user_pass=self._authenticate.get_pass(),
            organization=self._configuration["AWS_OKTA_ORGANIZATION"],
            factor=self._configuration["AWS_OKTA_FACTOR"],
            silent=self._configuration["AWS_OKTA_SILENT"],
            no_okta_cache=self._configuration["AWS_OKTA_NO_OKTA_CACHE"]
        )

        self._configuration["AWS_OKTA_USER"] = ''
        self._configuration["AWS_OKTA_PASS"] = ''

        if self._configuration["AWS_OKTA_APPLICATION"]:
            application_url = self._configuration["AWS_OKTA_APPLICATION"]
        else:
            applications = okta.get_applications()

            application_url = prompt.get_item(
                items=applications,
                label="AWS application",
                key=self._configuration["AWS_OKTA_APPLICATION"]
            )

        saml_response = okta.get_saml_response(
            application_url=application_url
        )

        saml_assertion = saml.get_saml_assertion(
            saml_response=saml_response
        )

        aws_roles = saml.get_aws_roles(
            saml_assertion=saml_assertion
        )

        aws_role = prompt.get_item(
            items=aws_roles,
            label="AWS Role",
            key=self._configuration["AWS_OKTA_ROLE"]
        )

        print_tty(
            "Role: {}".format(aws_role.role_arn),
            silent=self._configuration["AWS_OKTA_SILENT"]
        )

        response = client.assume_role_with_saml(
            RoleArn=aws_role.role_arn,
            PrincipalArn=aws_role.principal_arn,
            SAMLAssertion=saml_assertion,
            DurationSeconds=int(self._configuration["AWS_OKTA_DURATION"])
        )

        expiration = (response['Credentials']['Expiration']
                      .isoformat().replace("+00:00", "Z"))

        response['Credentials']['Expiration'] = expiration

        return response
