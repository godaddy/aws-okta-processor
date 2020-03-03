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
            "--duration": "AWS_OKTA_DURATION",
            "--key": "AWS_OKTA_KEY",
            "--factor": "AWS_OKTA_FACTOR",
            "--silent": "AWS_OKTA_SILENT",
            "--no-okta-cache": "AWS_OKTA_NO_OKTA_CACHE",
            "--no-aws-cache": "AWS_OKTA_NO_AWS_CACHE"
        }


class Authenticate(Base):
    def run(self):
        cache = JSONFileCache()
        saml_fetcher = SAMLFetcher(
            self,
            cache=cache
        )

        credentials = saml_fetcher.fetch_credentials()

        if self.configuration["AWS_OKTA_ENVIRONMENT"]:
            if os.name == 'nt':
                print(NT_EXPORT_STRING.format(
                    credentials["AccessKeyId"],
                    credentials["SecretAccessKey"],
                    credentials["SessionToken"]
                ))
            else:
                print(UNIX_EXPORT_STRING.format(
                    credentials["AccessKeyId"],
                    credentials["SecretAccessKey"],
                    credentials["SessionToken"]
                ))
        else:
            credentials["Version"] = 1
            print(json.dumps(credentials))

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
            if options[param]:
                configuration[var] = options[param]

            if var not in configuration.keys():
                if var in os.environ:
                    configuration[var] = os.environ[var]
                else:
                    configuration[var] = None

        return configuration
