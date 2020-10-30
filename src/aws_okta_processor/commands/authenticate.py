"""The authenticate command."""

from __future__ import print_function

import os
import json

from .base import Base
from aws_okta_processor.core.fetcher import SAMLFetcher
from botocore.credentials import JSONFileCache


UNIX_EXPORT_STRING = ("export AWS_ACCESS_KEY_ID='{}' && "
                      "export AWS_SECRET_ACCESS_KEY='{}' && "
                      "export AWS_SESSION_TOKEN='{}'")

UNIX_FISH_EXPORT_STRING = ("set --export AWS_ACCESS_KEY_ID '{}'; and "
                           "set --export AWS_SECRET_ACCESS_KEY '{}'; and "
                           "set --export AWS_SESSION_TOKEN '{}';")

NT_EXPORT_STRING = ("$env:AWS_ACCESS_KEY_ID='{}'; "
                    "$env:AWS_SECRET_ACCESS_KEY='{}'; "
                    "$env:AWS_SESSION_TOKEN='{}'")

CONFIG_MAP = {
            "--environment": "AWS_OKTA_ENVIRONMENT",
            "--user": "AWS_OKTA_USER",
            "--pass": "AWS_OKTA_PASS",
            "--organization": "AWS_OKTA_ORGANIZATION",
            "--application": "AWS_OKTA_APPLICATION",
            "--role": "AWS_OKTA_ROLE",
            "--region": "AWS_OKTA_REGION",
            "--duration": "AWS_OKTA_DURATION",
            "--key": "AWS_OKTA_KEY",
            "--factor": "AWS_OKTA_FACTOR",
            "--silent": "AWS_OKTA_SILENT",
            "--no-okta-cache": "AWS_OKTA_NO_OKTA_CACHE",
            "--no-aws-cache": "AWS_OKTA_NO_AWS_CACHE",
            "--account-alias": "AWS_OKTA_ACCOUNT_ALIAS",
            "--target-shell": "AWS_OKTA_TARGET_SHELL"
        }

EXTEND_CONFIG_MAP = {
            "AWS_OKTA_ENVIRONMENT": "environment",
            "AWS_OKTA_USER": "user",
            "AWS_OKTA_PASS": "pass",
            "AWS_OKTA_ORGANIZATION": "organization",
            "AWS_OKTA_APPLICATION": "application",
            "AWS_OKTA_ROLE": "role",
            "AWS_OKTA_REGION": "region",
            "AWS_OKTA_DURATION": "duration",
            "AWS_OKTA_KEY": "key",
            "AWS_OKTA_FACTOR": "factor",
            "AWS_OKTA_SILENT": "silent",
            "AWS_OKTA_NO_OKTA_CACHE": "no-okta-cache",
            "AWS_OKTA_NO_AWS_CACHE": "no-aws-cache",
            "AWS_OKTA_ACCOUNT_ALIAS": "account-alias",
            "AWS_OKTA_TARGET_SHELL": "target-shell"
        }


class Authenticate(Base):
    def authenticate(self):
        cache = JSONFileCache()
        saml_fetcher = SAMLFetcher(
            self,
            cache=cache
        )

        credentials = saml_fetcher.fetch_credentials()

        return credentials

    def run(self):

        credentials = self.authenticate()

        if self.configuration["AWS_OKTA_ENVIRONMENT"]:
            if os.name == 'nt':
                print(self.nt_output(credentials))
            else:
                print(self.unix_output(credentials))

        else:
            credentials["Version"] = 1
            print(json.dumps(credentials))

    def nt_output(self, credentials):
        """ Outputs the export command for Windows based systems """

        return NT_EXPORT_STRING.format(
            credentials["AccessKeyId"],
            credentials["SecretAccessKey"],
            credentials["SessionToken"]
        )

    def unix_output(self, credentials):
        """ Checks which shell target we should output the export command """

        # We assume Bash as the default shell target
        export_string = UNIX_EXPORT_STRING

        if self.configuration["AWS_OKTA_TARGET_SHELL"] == "fish":
            export_string = UNIX_FISH_EXPORT_STRING

        return export_string.format(
            credentials["AccessKeyId"],
            credentials["SecretAccessKey"],
            credentials["SessionToken"]
        )

    def get_pass(self):
        if self.configuration["AWS_OKTA_PASS"]:
            return self.configuration["AWS_OKTA_PASS"]

    def get_key_dict(self):
        return {
            "Organization": self.configuration["AWS_OKTA_ORGANIZATION"],
            "User": self.configuration["AWS_OKTA_USER"],
            "Key": self.configuration["AWS_OKTA_KEY"]
        }

    def get_configuration(self, options=None):
        configuration = {}

        for param, var in CONFIG_MAP.items():
            if options.get(param, None):
                configuration[var] = options[param]

            if var not in configuration.keys():
                if var in os.environ:
                    configuration[var] = os.environ[var]
                else:
                    configuration[var] = None

        return self.extend_configuration(configuration, 'authenticate',
                                         EXTEND_CONFIG_MAP)
