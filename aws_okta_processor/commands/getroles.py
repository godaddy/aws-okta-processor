# pylint: disable=C0301
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
"""  # noqa: E501

from __future__ import print_function

import os
import json
import re
import sys

from botocore.credentials import JSONFileCache  # type: ignore[import-untyped]

from aws_okta_processor.core.fetcher import SAMLFetcher

from .base import Base

# Command to export AWS credentials in Unix shell
UNIX_EXPORT_STRING = (
    "export AWS_ACCESS_KEY_ID='{}' && "
    "export AWS_SECRET_ACCESS_KEY='{}' && "
    "export AWS_SESSION_TOKEN='{}'"
)

# Command to export AWS credentials in Windows PowerShell
NT_EXPORT_STRING = (
    "$env:AWS_ACCESS_KEY_ID='{}'; "
    "$env:AWS_SECRET_ACCESS_KEY='{}'; "
    "$env:AWS_SESSION_TOKEN='{}'"
)

# Mapping of command-line options to environment variable names
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
    "--output-format": "AWS_OKTA_OUTPUT_FORMAT",
}


class GetRoles(Base):
    """
    Class to handle the 'get-roles' command for aws-okta-processor.
    Retrieves AWS accounts and roles available to the Okta user and outputs them in the specified format.
    """  # noqa: E501

    def get_accounts_and_roles(self):  # pylint: disable=R0914
        """
        Retrieves the list of AWS accounts and roles available to the Okta user by fetching the SAML assertion
        from Okta and parsing the AWS accounts and roles included in it.

        Returns:
            dict: A dictionary containing:
                - 'application_url' (str): The Okta application URL.
                - 'accounts' (list): A list of accounts, each account being a dict with:
                    - 'name' (str): Account name.
                    - 'id' (str): Account ID.
                    - 'name_raw' (str): Raw account name string from Okta.
                    - 'roles' (list): A list of roles, each role being a dict with:
                        - 'name' (str): Full role ARN.
                        - 'suffix' (str): The suffix of the role name, extracted from the full role ARN.
                - 'user' (str): The Okta username.
                - 'organization' (str): The Okta organization domain.
        """  # noqa: E501
        cache = JSONFileCache()
        saml_fetcher = SAMLFetcher(self, cache=cache)

        # Fetch the application and roles from Okta
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
            # Example of name_raw: 'Account: my-account (123456789012)'
            # Extract account name and ID from the raw account name
            account_parts = re.match(
                r"(Account:) ([a-zA-Z0-9-_]+) \(([0-9]+)\)", name_raw
            )
            account = account_parts[2]  # 'my-account'
            account_id = account_parts[3]  # '123456789012'
            roles = accounts[name_raw]
            result_roles = []
            result_account = {
                "name": account,
                "id": account_id,
                "name_raw": name_raw,
                "roles": result_roles,
            }
            result_accounts.append(result_account)
            for role in roles:
                # Get the role suffix based on delimiter (default is '-')
                role_suffix = role.split(
                    os.environ.get("AWS_OKTA_ROLE_SUFFIX_DELIMITER", "-")
                )[-1]
                result_roles.append({"name": role, "suffix": role_suffix})

        return results

    def run(self):
        """
        Executes the 'get-roles' command, fetching accounts and roles and outputting them in the specified format.

        The output format can be JSON, text, or AWS profiles format.

        If the output is 'json', outputs the accounts and roles data as a JSON string.

        If the output is 'profiles', generates AWS CLI profile configurations using the 'credential_process' method.

        Otherwise, formats the output using the specified output format string.
        """  # noqa: E501
        accounts_and_roles = self.get_accounts_and_roles()

        output = self.configuration.get("AWS_OKTA_OUTPUT", "json").lower()
        if output == "json":
            sys.stdout.write(json.dumps(accounts_and_roles))
        else:
            output_format = self.configuration.get(
                "AWS_OKTA_OUTPUT_FORMAT", "{account},{role}"
            )
            if output == "profiles":
                output_format = (
                    "\n[{account}-{role_suffix}]"
                    "\ncredential_process=aws-okta-processor authenticate "
                    '--organization="{organization}" --user="{user}" '
                    '--application="{application_url}" '
                    '--role="{role}" --key="{account}-{role}"'
                )
            # Generate formatted output for each role
            formatted_roles = self.get_formatted_roles(
                accounts_and_roles, output_format
            )
            for role in formatted_roles:
                sys.stdout.write(role + "\n")

    def get_formatted_roles(self, accounts_and_roles, output_format):
        """
        Formats the accounts and roles data according to the specified output format string.

        The output format string can include placeholders:
            - {account}: Account name.
            - {account_id}: Account ID.
            - {account_raw}: Raw account name string from Okta.
            - {role}: Full role ARN.
            - {role_suffix}: Suffix of the role name.
            - {organization}: Okta organization domain.
            - {application_url}: Okta application URL.
            - {user}: Okta username.

        Args:
            accounts_and_roles (dict): The accounts and roles data obtained from get_accounts_and_roles().
            output_format (str): The format string to use for output.

        Yields:
            str: Formatted string for each role in the accounts.
        """  # noqa: E501
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
                    role_suffix=role["suffix"].lower(),
                )

    def get_pass(self):
        """
        Retrieves the Okta user password from the configuration.

        Returns:
            str: The Okta user password if set, otherwise None.
        """
        if self.configuration["AWS_OKTA_PASS"]:
            return self.configuration["AWS_OKTA_PASS"]

        return None

    def get_key_dict(self):
        """
        Builds a dictionary containing the organization, user, and key for caching purposes.

        Returns:
            dict: Dictionary with 'Organization', 'User', and 'Key' keys.
        """  # noqa: E501
        return {
            "Organization": self.configuration["AWS_OKTA_ORGANIZATION"],
            "User": self.configuration["AWS_OKTA_USER"],
            "Key": self.configuration["AWS_OKTA_KEY"],
        }

    def get_configuration(self, options=None):
        """
        Retrieves the configuration by combining command-line options, environment variables, and defaults.

        Args:
            options (dict, optional): Command-line options passed to the script.

        Returns:
            dict: A dictionary of configuration variables.
        """  # noqa: E501
        configuration = {}

        for param, var in CONFIG_MAP.items():
            if options.get(param, None):
                configuration[var] = options[param]

            if var not in configuration:
                if var in os.environ:
                    configuration[var] = os.environ[var]
                else:
                    configuration[var] = None

        return configuration
