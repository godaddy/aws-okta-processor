from unittest import TestCase
from mock import patch
from mock import MagicMock
from tests.test_base import SAML_RESPONSE
from tests.test_base import SIGN_IN_RESPONSE

from aws_okta_processor.core import saml


class TestSAMLUtils(TestCase):
    @patch('aws_okta_processor.core.saml.print_tty')
    @patch('aws_okta_processor.core.saml.sys')
    def test_get_saml_assertion(self, mock_sys, mock_print_tty):
        mock_sys.exit.side_effect = SystemExit
        saml.get_saml_assertion(saml_response=SAML_RESPONSE)

        with self.assertRaises(SystemExit):
            saml.get_saml_assertion(saml_response="")

        mock_print_tty.assert_called_once_with("ERROR: SAMLResponse tag was not found!") # noqa
        mock_sys.exit.assert_called_once_with(1)

    @patch('aws_okta_processor.core.saml.requests')
    def test_get_account_roles(self, mock_requests):
        mock_response = MagicMock()
        mock_response.text = SIGN_IN_RESPONSE
        mock_requests.post.return_value = mock_response

        account_roles = saml.get_account_roles(saml_assertion="ASSERTION")

        self.assertEqual(
            account_roles[0].account_name,
            "Account: account-one (1)"
        )

        self.assertEqual(account_roles[0].role_arn, "arn:aws:iam::1:role/Role-One") # noqa
        self.assertEqual(account_roles[1].account_name, "Account: account-one (1)") # noqa
        self.assertEqual(account_roles[1].role_arn, "arn:aws:iam::1:role/Role-Two") # noqa
        self.assertEqual(account_roles[2].account_name, "Account: account-two (2)") # noqa
        self.assertEqual(account_roles[2].role_arn, "arn:aws:iam::2:role/Role-One") # noqa

    @patch('aws_okta_processor.core.saml.requests')
    def test_get_aws_roles(self, mock_requests):
        mock_response = MagicMock()
        mock_response.text = SIGN_IN_RESPONSE
        mock_requests.post.return_value = mock_response

        saml_assertion = saml.get_saml_assertion(saml_response=SAML_RESPONSE)
        aws_roles = saml.get_aws_roles(saml_assertion=saml_assertion)

        self.assertIn("Account: account-one (1)", aws_roles)
        self.assertIn("arn:aws:iam::1:role/Role-One", aws_roles["Account: account-one (1)"]) # noqa
        self.assertIn("arn:aws:iam::1:role/Role-Two", aws_roles["Account: account-one (1)"]) # noqa
        self.assertIn("Account: account-two (2)", aws_roles)
        self.assertIn("arn:aws:iam::2:role/Role-One", aws_roles["Account: account-two (2)"]) # noqa
