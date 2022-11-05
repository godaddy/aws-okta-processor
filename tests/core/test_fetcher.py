from datetime import datetime
from unittest import mock

from tests.test_base import TestBase

from tests.test_base import SAML_RESPONSE

from mock import patch, call
from mock import MagicMock

from aws_okta_processor.commands.authenticate import Authenticate
from aws_okta_processor.core.fetcher import SAMLFetcher


# Need to add actual tests
class TestFetcher(TestBase):
    @patch("botocore.client")
    @patch('aws_okta_processor.core.fetcher.print_tty')
    @patch('aws_okta_processor.core.fetcher.Okta')
    def test_fetcher(
            self,
            mock_okta,
            mock_print_tty,
            mock_client
    ):
        self.OPTIONS["--role"] = "arn:aws:iam::2:role/Role-One"
        mock_okta().get_saml_response.return_value = SAML_RESPONSE
        mock_cache = MagicMock()
        authenticate = Authenticate(self.OPTIONS)
        fetcher = SAMLFetcher(authenticate, cache=mock_cache)

        fetcher.fetch_credentials()

    @patch('aws_okta_processor.core.fetcher.SAMLFetcher._get_app_roles')
    def test_get_app_roles(self, mock_get_app_roles):

        mock_get_app_roles.return_value = ("accounts", None, "app-url", "jdoe", 'test-org')
        authenticate = Authenticate(self.OPTIONS)
        fetcher = SAMLFetcher(authenticate, cache={})
        actual = fetcher.get_app_roles()

        self.assertEqual({
            'Accounts': 'accounts',
            'Application': 'app-url',
            'Organization': 'test-org',
            'User': 'jdoe'
        }, actual)

    @patch("boto3.client")
    @patch('aws_okta_processor.core.fetcher.print_tty')
    @patch('aws_okta_processor.core.fetcher.prompt.print_tty')
    @patch('aws_okta_processor.core.fetcher.prompt.input_tty', return_value='1')
    @patch('aws_okta_processor.core.fetcher.Okta')
    def test_fetcher_should_filter_accounts(
            self,
            mock_okta,
            mock_prompt,
            mock_prompt_print_tty,
            mock_print_tty,
            mock_client
    ):

        def assume_role_side_effect(*args, **kwargs):
            if kwargs['RoleArn'] == 'arn:aws:iam::1:role/Role-One':
                return {
                    'Credentials': {
                        'AccessKeyId': 'test-key1',
                        'SecretAccessKey': 'test-secret1',
                        'SessionToken': 'test-token1',
                        'Expiration': datetime(2020, 4, 17, 12, 0, 0, 0)
                    }
                }
            raise RuntimeError('invalid RoleArn')

        self.OPTIONS["--account-alias"] = '1*'
        self.OPTIONS["--pass"] = 'testpass'

        mock_c = mock.Mock()
        mock_c.assume_role_with_saml.side_effect = assume_role_side_effect
        mock_okta().get_saml_response.return_value = SAML_RESPONSE
        mock_client.return_value = mock_c

        authenticate = Authenticate(self.OPTIONS)
        fetcher = SAMLFetcher(authenticate, cache={})

        creds = fetcher.fetch_credentials()
        self.assertDictEqual({
            'AccessKeyId': 'test-key1',
            'Expiration': '2020-04-17T12:00:00',
            'SecretAccessKey': 'test-secret1',
            'SessionToken': 'test-token1'
        }, creds)

        self.assertEqual(5, mock_prompt_print_tty.call_count)

        MagicMock.assert_has_calls(mock_prompt_print_tty, [
            call('Select AWS Role:'),
            call('Account: 1', indents=0),
            call('[ 1 ] Role-One', indents=1),
            call('[ 2 ] Role-Two', indents=1),
            call('Selection: ', newline=False)
        ])

    @patch("boto3.client")
    @patch('aws_okta_processor.core.fetcher.print_tty')
    @patch('aws_okta_processor.core.fetcher.prompt.print_tty')
    @patch('aws_okta_processor.core.fetcher.prompt.input_tty', return_value='1')
    @patch('aws_okta_processor.core.fetcher.Okta')
    def test_fetcher_should_prompt_all_accounts(
            self,
            mock_okta,
            mock_prompt,
            mock_prompt_print_tty,
            mock_print_tty,
            mock_client
    ):

        def assume_role_side_effect(*args, **kwargs):
            if kwargs['RoleArn'] == 'arn:aws:iam::1:role/Role-One':
                return {
                    'Credentials': {
                        'AccessKeyId': 'test-key1',
                        'SecretAccessKey': 'test-secret1',
                        'SessionToken': 'test-token1',
                        'Expiration': datetime(2020, 4, 17, 12, 0, 0, 0)
                    }
                }
            raise RuntimeError('invalid RoleArn')

        self.OPTIONS["--pass"] = 'testpass'

        mock_c = mock.Mock()
        mock_c.assume_role_with_saml.side_effect = assume_role_side_effect
        mock_okta().get_saml_response.return_value = SAML_RESPONSE
        mock_client.return_value = mock_c

        authenticate = Authenticate(self.OPTIONS)
        fetcher = SAMLFetcher(authenticate, cache={})

        creds = fetcher.fetch_credentials()
        self.assertDictEqual({
            'AccessKeyId': 'test-key1',
            'Expiration': '2020-04-17T12:00:00',
            'SecretAccessKey': 'test-secret1',
            'SessionToken': 'test-token1'
        }, creds)

        self.assertEqual(7, mock_prompt_print_tty.call_count)

        MagicMock.assert_has_calls(mock_prompt_print_tty, [
            call('Select AWS Role:'),
            call('Account: 1', indents=0),
            call('[ 1 ] Role-One', indents=1),
            call('[ 2 ] Role-Two', indents=1),
            call('Account: 2', indents=0),
            call('[ 3 ] Role-One', indents=1),
            call('Selection: ', newline=False)
        ])
