"""
This module provides functionality to extract SAML assertions from Okta responses
and parse AWS roles from SAML assertions for use in AWS authentication.
"""

import base64
from collections import OrderedDict
from fnmatch import fnmatch
import sys

from defusedxml import ElementTree  # type: ignore[import-untyped]
from bs4 import BeautifulSoup  # type: ignore[import-untyped]
import requests  # type: ignore[import-untyped]
import six  # type: ignore[import-untyped]

from aws_okta_processor.core.tty import print_tty

# Constants for SAML namespaces and AWS sign-in URL
SAML_ATTRIBUTE = "{urn:oasis:names:tc:SAML:2.0:assertion}Attribute"
SAML_ATTRIBUTE_ROLE = "https://aws.amazon.com/SAML/Attributes/Role"
SAML_ATTRIBUTE_VALUE = "{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue"
AWS_SIGN_IN_URL = "https://signin.aws.amazon.com/saml"


def get_saml_assertion(saml_response=None):
    """
    Extracts the SAML assertion from the HTML content.

    Searches for the SAMLResponse input field in the provided HTML content
    and returns its value.

    Args:
        saml_response (str): HTML content containing the SAMLResponse.

    Returns:
        str or None: The SAML assertion if found, otherwise None.
    """
    soup = BeautifulSoup(saml_response, "html.parser")

    # Search for the SAMLResponse input field
    for input_tag in soup.find_all("input"):
        if input_tag.get("name") == "SAMLResponse":
            return input_tag.get("value")

    # Check for MFA challenge indicators
    if soup.find("div", {"id": "okta-sign-in"}):
        # The supplied Okta session is not sufficient to get the SAML assertion.
        # Note: This may fail if Okta changes the app-level MFA page.
        print_tty("SAMLResponse tag not found due to MFA challenge.")
        return None

    # Check for password verification challenge indicators
    if soup.find("div", {"id": "password-verification-challenge"}):
        # The supplied Okta session is not sufficient to get the SAML assertion.
        # Note: This may fail if Okta changes the app-level re-auth page.
        print_tty("SAMLResponse tag not found due to password verification challenge.")
        return None

    print_tty("ERROR: SAMLResponse tag was not found!")
    sys.exit(1)


def get_aws_roles(  # pylint: disable=R0914
    saml_assertion=None, accounts_filter=None, sign_in_url=None
):
    """
    Parses the SAML assertion and extracts AWS roles.

    Args:
        saml_assertion (str): Base64-encoded SAML assertion.
        accounts_filter (str): Filter pattern to apply to account names.
        sign_in_url (str): AWS sign-in URL, defaults to AWS_SIGN_IN_URL.

    Returns:
        OrderedDict: Mapping of account names to dictionaries of role ARNs and AWSRole instances.
    """  # noqa: E501
    aws_roles = OrderedDict()
    role_principals = {}
    decoded_saml = base64.b64decode(saml_assertion)
    xml_saml = ElementTree.fromstring(decoded_saml)
    saml_attributes = xml_saml.iter(SAML_ATTRIBUTE)

    # Extract role and principal ARNs from the SAML assertion
    for saml_attribute in saml_attributes:
        if saml_attribute.get("Name") == SAML_ATTRIBUTE_ROLE:
            saml_attribute_values = saml_attribute.iter(SAML_ATTRIBUTE_VALUE)

            for saml_attribute_value in saml_attribute_values:
                if not saml_attribute_value.text:
                    print_tty("ERROR: No accounts found in SAMLResponse!")
                    sys.exit(1)

                # The value is a comma-separated string: "principal_arn,role_arn"
                principal_arn, role_arn = saml_attribute_value.text.split(",")

                role_principals[role_arn] = principal_arn

    # Skip get_account_roles if only one role returned
    if len(role_principals) > 1:
        # Retrieve account roles from AWS sign-in page
        account_roles = get_account_roles(
            saml_assertion=saml_assertion, sign_in_url=sign_in_url
        )

        for account_role in account_roles:
            account_name = account_role.account_name
            # Apply accounts filter if provided
            if accounts_filter and len(accounts_filter) > 0:
                account_name_alias = account_name.split(" ")[1]
                if not fnmatch(account_name_alias, accounts_filter):
                    continue

            role_arn = account_role.role_arn
            account_role.principal_arn = role_principals[role_arn]

            if account_name not in aws_roles:
                aws_roles[account_name] = {}

            aws_roles[account_name][role_arn] = account_role
    else:
        # If only one role, create default AWSRole instance
        account_role = AWSRole()
        for role_arn, principal_arn in six.iteritems(role_principals):
            account_role.role_arn = role_arn
            account_role.principal_arn = principal_arn
            aws_roles["default"] = {}
            aws_roles["default"][role_arn] = account_role

    return aws_roles


def get_account_roles(saml_assertion=None, sign_in_url=None):
    """
    Retrieves AWS account roles from the AWS SAML sign-in page.

    Args:
        saml_assertion (str): Base64-encoded SAML assertion.
        sign_in_url (str): AWS sign-in URL, defaults to AWS_SIGN_IN_URL.

    Returns:
        list: List of AWSRole instances representing available roles.
    """
    role_accounts = []

    data = {"SAMLResponse": saml_assertion, "RelayState": ""}

    # Post the SAML assertion to AWS sign-in URL
    response = requests.post(sign_in_url or AWS_SIGN_IN_URL, data=data, timeout=60)
    soup = BeautifulSoup(response.text, "html.parser")
    accounts = soup.find("fieldset").find_all(
        "div", attrs={"class": "saml-account"}, recursive=False
    )

    for account in accounts:
        # Extract the account name
        account_name = account.find("div", attrs={"class": "saml-account-name"}).string

        # Find all roles within the account
        roles = account.find("div", attrs={"class": "saml-account"}).find_all(
            "div", attrs={"class": "saml-role"}
        )

        for role in roles:
            role_arn = role.input["id"]
            role_description = role.label.string
            role_accounts.append(
                AWSRole(
                    account_name=account_name,
                    role_description=role_description,
                    role_arn=role_arn,
                )
            )

    return role_accounts


class AWSRole:  # pylint: disable=R0903
    """
    Represents an AWS role associated with an account.

    Attributes:
        account_name (str): The name of the AWS account.
        role_description (str): Description of the role.
        role_arn (str): The ARN of the role.
        principal_arn (str): The ARN of the principal (identity provider).
    """

    def __init__(
        self,
        account_name=None,
        role_description=None,
        role_arn=None,
        principal_arn=None,
    ):
        self.account_name = account_name
        self.role_description = role_description
        self.role_arn = role_arn
        self.principal_arn = principal_arn
