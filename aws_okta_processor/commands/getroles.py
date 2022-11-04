"""
Usage: aws-okta-processor get-roles [options]

Options:
    -h --help                                                   Show this screen.
    --version                                                   Show version.
    --no-okta-cache                                             Do not read okta cache.
    --no-aws-cache                                              Do not read aws cache.
    -e --environment                                            Dump auth into ENV variables.
    -u <user_name>, --user=<user_name>                          Okta user name.
    -p <user_pass>, --pass=<user_pass>                          Okta user password.
    -o <okta_organization>, --organization=<okta_organization>  Okta organization domain.
    -a <okta_application>, --application=<okta_application>     Okta application url.
    -r <role_name>, --role=<role_name>                          AWS role ARN.
    -R <region_name>, --region=<region_name>                    AWS region name.
    -U <sign_in_url>, --sign-in-url=<sign_in_url>               AWS Sign In URL.
                                                                    [default: https://signin.aws.amazon.com/saml]
    -A <account>, --account-alias=<account>                     AWS account alias filter (uses wildcards).
    -d <duration_seconds> ,--duration=<duration_seconds>        Duration of role session [default: 3600].
    -k <key>, --key=<key>                                       Key used for generating and accessing cache.
    -f <factor>, --factor=<factor>                              Factor type for MFA.
    -s --silent                                                 Run silently.
    --target-shell <target_shell>                               Target shell to output the export command.
    --output=<output>                                           Output type (json, text, profiles) [default: json]
    --output-format=<format>                                    Format string for the output
                                                                    [default: {account},{role}]
"""

from __future__ import print_function

import os
import json
import re
import sys

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
            "--no-aws-cache": "AWS_OKTA_NO_AWS_CACHE",
            "--output": "AWS_OKTA_OUTPUT",
            "--output-format": "AWS_OKTA_OUTPUT_FORMAT"
        }


class GetRoles(Base):
    def get_accounts_and_roles(self):
        cache = JSONFileCache()
        saml_fetcher = SAMLFetcher(
            self,
            cache=cache
        )

        app_and_role = saml_fetcher.get_app_roles()

        result_accounts = []
        results = {
            "application_url": app_and_role["Application"],
            "accounts": result_accounts,
            "user": app_and_role["User"],
            "organization": app_and_role["Organization"],
        }

        accounts = app_and_role["Accounts"]
        for name_raw in accounts:
            account_parts = re.match(r"(Account:) ([a-zA-Z0-9-_]+) \(([0-9]+)\)", name_raw)
            account = account_parts[2]
            account_id = account_parts[3]
            roles = accounts[name_raw]
            result_roles = []
            result_account = {
                "name": account,
                "id": account_id,
                "name_raw": name_raw,
                "roles": result_roles
            }
            result_accounts.append(result_account)
            for role in roles:
                role_suffix = role.split(os.environ.get("AWS_OKTA_ROLE_SUFFIX_DELIMITER", "-"))[-1]
                result_roles.append({
                    "name": role,
                    "suffix": role_suffix
                })

        return results

    def run(self):

        accounts_and_roles = self.get_accounts_and_roles()

        output = self.configuration.get("AWS_OKTA_OUTPUT", "json").lower()
        if output == "json":
            sys.stdout.write(json.dumps(accounts_and_roles))
        else:
            output_format = self.configuration.get("AWS_OKTA_OUTPUT_FORMAT", "{account},{role}")
            if output == "profiles":
                output_format = '\n[{account}-{role_suffix}]\ncredential_process=aws-okta-processor authenticate ' \
                                '--organization="{organization}" --user="{user}" --application="{application_url}" ' \
                                '--role="{role}" --key="{account}-{role}"'
            formatted_roles = self.get_formatted_roles(accounts_and_roles, output_format)
            for role in formatted_roles:
                sys.stdout.write(role + "\n")

    def get_formatted_roles(self, accounts_and_roles, output_format):
        application_url = accounts_and_roles["application_url"]
        accounts = accounts_and_roles["accounts"]
        organization = accounts_and_roles["organization"]
        user = accounts_and_roles["user"]

        for account in accounts:
            account_name = account["name"]
            account_id = account["id"]
            account_raw = account["name_raw"]
            roles = account["roles"]
            for role in roles:
                yield output_format.format(
                    account=account_name,
                    account_id=account_id,
                    account_raw=account_raw,
                    role=role["name"],
                    organization=organization,
                    application_url=application_url,
                    user=user,
                    role_suffix=role["suffix"].lower()
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

        return configuration
