from unittest import TestCase
from mock import patch
from mock import MagicMock

from aws_okta_processor.core.okta import Okta


class TestOkta(TestCase):
    @patch('aws_okta_processor.core.okta.print_tty')
    @patch('aws_okta_processor.core.okta.Okta.set_okta_session')
    @patch('aws_okta_processor.core.okta.Okta.get_okta_session')
    @patch('aws_okta_processor.core.okta.Okta.get_okta_single_use_token')
    @patch('aws_okta_processor.core.okta.requests')
    def test_okta(
            self,
            mock_requests,
            mock_get_session_token,
            mock_get_session,
            mock_set_session,
            mock_print_tty
    ):
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session
        mock_get_session_token.return_value = "single_use_token"
        mock_get_session.return_value = {
            'id': 'session_id',
            'expiresAt': '2019-01-22T19:24:24Z'
        }

        okta = Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization_domain",
            factor="factor_type"
        )

        self.assertIs(okta.session, mock_session)
        self.assertEqual(okta.okta_single_use_token, "single_use_token")
        self.assertEqual(okta.organization, "organization_domain")
        self.assertEqual(okta.factor, "factor_type")

        mock_get_session_token.assert_called_once_with(
            user_name="user_name",
            user_pass="user_pass"
        )
