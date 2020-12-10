import sys
from fnmatch import fnmatch

import six
import base64
import requests
import xml.etree.ElementTree as ElementTree

from bs4 import BeautifulSoup
from collections import OrderedDict
from aws_okta_processor.core.print_tty import print_tty


SAML_ATTRIBUTE = '{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'
SAML_ATTRIBUTE_ROLE = 'https://aws.amazon.com/SAML/Attributes/Role'
SAML_ATTRIBUTE_VALUE = '{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'
AWS_SIGN_IN_URL = "https://signin.aws.amazon.com/saml"


def get_saml_assertion(saml_response=None):
    soup = BeautifulSoup(saml_response, "html.parser")

    for input_tag in soup.find_all('input'):
        if input_tag.get('name') == 'SAMLResponse':
            return input_tag.get('value')

    print_tty("ERROR: SAMLResponse tag was not found!")
    sys.exit(1)


def get_aws_roles(saml_assertion=None, accounts_filter=None):
    aws_roles = OrderedDict()
    role_principals = {}
    decoded_saml = base64.b64decode(saml_assertion)
    xml_saml = ElementTree.fromstring(decoded_saml)
    saml_attributes = xml_saml.iter(SAML_ATTRIBUTE)

    for saml_attribute in saml_attributes:
        if saml_attribute.get('Name') == SAML_ATTRIBUTE_ROLE:
            saml_attribute_values = saml_attribute.iter(
                SAML_ATTRIBUTE_VALUE
            )

            for saml_attribute_value in saml_attribute_values:
                if not saml_attribute_value.text:
                    print_tty("ERROR: No accounts found in SAMLResponse!")
                    sys.exit(1)

                principal_arn, role_arn = saml_attribute_value.text.split(',')

                role_principals[role_arn] = principal_arn

    # Skip get_account_roles if only one role returned.
    if len(role_principals) > 1:
        account_roles = get_account_roles(saml_assertion=saml_assertion)

        for account_role in account_roles:
            account_name = account_role.account_name
            if accounts_filter is not None and len(accounts_filter) > 0:
                account_name_alias = account_name.split(" ")[1]
                if not fnmatch(account_name_alias, accounts_filter):
                    continue

            role_arn = account_role.role_arn
            account_role.principal_arn = role_principals[role_arn]

            if account_name not in aws_roles:
                aws_roles[account_name] = {}

            aws_roles[account_name][role_arn] = account_role
    else:
        account_role = AWSRole()
        for role_arn, principal_arn in six.iteritems(role_principals):
            account_role.role_arn = role_arn
            account_role.principal_arn = principal_arn
            aws_roles["default"] = {}
            aws_roles["default"][role_arn] = account_role

    return aws_roles


def get_account_roles(saml_assertion=None):
    role_accounts = []

    data = {
        "SAMLResponse": saml_assertion,
        "RelayState": ""
    }

    response = requests.post(AWS_SIGN_IN_URL, data=data)
    soup = BeautifulSoup(response.text, "html.parser")
    accounts = soup.find('fieldset').find_all(
        "div",
        attrs={"class": "saml-account"},
        recursive=False
    )

    for account in accounts:
        account_name = account.find(
            "div",
            attrs={"class": "saml-account-name"}
        ).string

        roles = account.find(
            "div",
            attrs={"class": "saml-account"}).find_all(
            "div",
            attrs={"class": "saml-role"}
        )

        for role in roles:
            role_arn = role.input['id']
            role_description = role.label.string
            role_accounts.append(AWSRole(
                account_name=account_name,
                role_description=role_description,
                role_arn=role_arn
            ))

    return role_accounts


class AWSRole:
    def __init__(
            self,
            account_name=None,
            role_description=None,
            role_arn=None,
            principal_arn=None
    ):
        self.account_name = account_name
        self.role_description = role_description
        self.role_arn = role_arn
        self.principal_arn = principal_arn
