# pylint: disable=C0301
"""
Module for AWS-Okta authentication processing.

This module defines the 'Authenticate' class, which handles the process of authenticating with Okta
and obtaining AWS credentials via SAML.

Usage:
    aws-okta-processor authenticate [options]

Options:
    -h --help                                                   Show this screen.
    --version                                                   Show version.
    --no-okta-cache                                             Do not read Okta cache.
    --no-aws-cache                                              Do not read AWS cache.
    -e --environment                                            Dump auth into ENV variables.
    -u <user_name>, --user=<user_name>                          Okta user name.
    -p <user_pass>, --pass=<user_pass>                          Okta user password.
    -o <okta_organization>, --organization=<okta_organization>  Okta organization domain.
    -a <okta_application>, --application=<okta_application>     Okta application URL.
    -r <role_name>, --role=<role_name>                          AWS role ARN.
    --secondary-role <secondary_role_arn>                       Secondary AWS role ARN.
    -R <region_name>, --region=<region_name>                    AWS region name.
    -U <sign_in_url>, --sign-in-url=<sign_in_url>               AWS Sign In URL.
                                                                    [default: https://signin.aws.amazon.com/saml]
    -A <account>, --account-alias=<account>                     AWS account alias filter (uses wildcards).
    -d <duration_seconds>, --duration=<duration_seconds>        Duration of role session [default: 3600].
    -k <key>, --key=<key>                                       Key used for generating and accessing cache.
    -f <factor> --factor=<factor>                               Factor type for MFA.
    -s --silent                                                 Run silently.
    --target-shell <target_shell>                               Target shell to output the export command.
"""  # noqa: E501

from __future__ import print_function

import os
import json

from botocore.credentials import JSONFileCache  # type: ignore[import-untyped]

from aws_okta_processor.core.fetcher import SAMLFetcher

from .base import Base

# Shell command templates for exporting AWS credentials in different shells.

# Template for UNIX-like shells (bash, zsh)
UNIX_EXPORT_STRING = (
    "export AWS_ACCESS_KEY_ID='{}' && "
    "export AWS_SECRET_ACCESS_KEY='{}' && "
    "export AWS_SESSION_TOKEN='{}'"
)

# Template for Fish shell
UNIX_FISH_EXPORT_STRING = (
    "set --export AWS_ACCESS_KEY_ID '{}'; and "
    "set --export AWS_SECRET_ACCESS_KEY '{}'; and "
    "set --export AWS_SESSION_TOKEN '{}';"
)

# Template for Windows PowerShell
NT_EXPORT_STRING = (
    "$env:AWS_ACCESS_KEY_ID='{}'; "
    "$env:AWS_SECRET_ACCESS_KEY='{}'; "
    "$env:AWS_SESSION_TOKEN='{}'"
)

# Map command-line options to environment variable names.
CONFIG_MAP = {
    "--environment": "AWS_OKTA_ENVIRONMENT",
    "--user": "AWS_OKTA_USER",
    "--pass": "AWS_OKTA_PASS",
    "--organization": "AWS_OKTA_ORGANIZATION",
    "--application": "AWS_OKTA_APPLICATION",
    "--role": "AWS_OKTA_ROLE",
    "--secondary-role": "AWS_OKTA_SECONDARY_ROLE",
    "--region": "AWS_OKTA_REGION",
    "--sign-in-url": "AWS_OKTA_SIGN_IN_URL",
    "--duration": "AWS_OKTA_DURATION",
    "--key": "AWS_OKTA_KEY",
    "--factor": "AWS_OKTA_FACTOR",
    "--silent": "AWS_OKTA_SILENT",
    "--no-okta-cache": "AWS_OKTA_NO_OKTA_CACHE",
    "--no-aws-cache": "AWS_OKTA_NO_AWS_CACHE",
    "--account-alias": "AWS_OKTA_ACCOUNT_ALIAS",
    "--target-shell": "AWS_OKTA_TARGET_SHELL",
}

# Map environment variables to internal configuration keys.
EXTEND_CONFIG_MAP = {
    "AWS_OKTA_ENVIRONMENT": "environment",
    "AWS_OKTA_USER": "user",
    "AWS_OKTA_PASS": "pass",
    "AWS_OKTA_ORGANIZATION": "organization",
    "AWS_OKTA_APPLICATION": "application",
    "AWS_OKTA_ROLE": "role",
    "AWS_OKTA_SECONDARY_ROLE": "secondary-role",
    "AWS_OKTA_REGION": "region",
    "AWS_OKTA_SIGN_IN_URL": "sign_in_url",
    "AWS_OKTA_DURATION": "duration",
    "AWS_OKTA_KEY": "key",
    "AWS_OKTA_FACTOR": "factor",
    "AWS_OKTA_SILENT": "silent",
    "AWS_OKTA_NO_OKTA_CACHE": "no-okta-cache",
    "AWS_OKTA_NO_AWS_CACHE": "no-aws-cache",
    "AWS_OKTA_ACCOUNT_ALIAS": "account-alias",
    "AWS_OKTA_TARGET_SHELL": "target-shell",
}


class Authenticate(Base):
    """
    Authenticates with Okta to obtain AWS credentials via SAML and outputs them
    in the desired format.

    Inherits from:
        Base: The base class that provides common functionality for commands.
    """

    def authenticate(self):
        """
        Authenticates with Okta and fetches AWS credentials.

        Returns:
            dict: A dictionary containing AWS credentials.
        """
        cache = JSONFileCache()
        saml_fetcher = SAMLFetcher(self, cache=cache)

        credentials = saml_fetcher.fetch_credentials()

        return credentials

    def run(self):
        """
        Main entry point for the 'authenticate' command.

        Authenticates with Okta, fetches AWS credentials, and outputs them
        either as environment variables or as JSON, depending on the configuration.
        """
        credentials = self.authenticate()

        if self.configuration["AWS_OKTA_ENVIRONMENT"]:
            if os.name == "nt":
                print(self.nt_output(credentials))
            else:
                print(self.unix_output(credentials))
        else:
            credentials["Version"] = 1
            print(json.dumps(credentials))

    def nt_output(self, credentials):
        """
        Generates the export command for Windows-based systems.

        Args:
            credentials (dict): AWS credentials.

        Returns:
            str: A command string to set environment variables in PowerShell.
        """
        return NT_EXPORT_STRING.format(
            credentials["AccessKeyId"],
            credentials["SecretAccessKey"],
            credentials["SessionToken"],
        )

    def unix_output(self, credentials):
        """
        Generates the export command for UNIX-based systems.

        Determines the target shell from the configuration and formats the
        appropriate export command.

        Args:
            credentials (dict): AWS credentials.

        Returns:
            str: A command string to set environment variables in the shell.
        """
        # Assume Bash as the default shell target
        export_string = UNIX_EXPORT_STRING

        if self.configuration["AWS_OKTA_TARGET_SHELL"] == "fish":
            export_string = UNIX_FISH_EXPORT_STRING

        return export_string.format(
            credentials["AccessKeyId"],
            credentials["SecretAccessKey"],
            credentials["SessionToken"],
        )

    def get_pass(self):
        """
        Retrieves the Okta user password from the configuration.

        Returns:
            str or None: The Okta user password if set, otherwise None.
        """
        if self.configuration["AWS_OKTA_PASS"]:
            return self.configuration["AWS_OKTA_PASS"]

        return None

    def get_key_dict(self):
        """
        Constructs a dictionary key for caching purposes.

        Returns:
            dict: A dictionary containing 'Organization', 'User', and 'Key' entries.
        """
        return {
            "Organization": self.configuration["AWS_OKTA_ORGANIZATION"],
            "User": self.configuration["AWS_OKTA_USER"],
            "Key": self.configuration["AWS_OKTA_KEY"],
        }

    def get_configuration(self, options=None):
        """
        Builds the configuration dictionary from options and environment variables.

        Args:
            options (dict, optional): Command-line options parsed by docopt.

        Returns:
            dict: A configuration dictionary.
        """
        configuration = {}

        for param, var in CONFIG_MAP.items():
            if options.get(param, None):
                configuration[var] = options[param]

            if var not in configuration:
                if var in os.environ:
                    configuration[var] = os.environ[var]
                else:
                    configuration[var] = None

        return self.extend_configuration(
            configuration, "authenticate", EXTEND_CONFIG_MAP
        )
