from tests.test_base import TestBase
from tests.test_base import SESSION_RESPONSE
from tests.test_base import AUTH_TOKEN_RESPONSE
from tests.test_base import AUTH_MFA_PUSH_RESPONSE
from tests.test_base import AUTH_MFA_TOTP_RESPONSE
from tests.test_base import AUTH_MFA_MULTIPLE_RESPONSE
from tests.test_base import AUTH_MFA_YUBICO_HARDWARE_RESPONSE
from tests.test_base import MFA_WAITING_RESPONSE
from tests.test_base import APPLICATIONS_RESPONSE
from tests.test_base import SAML_RESPONSE

from mock import patch
from mock import call
from mock import MagicMock
from mock import mock_open
from datetime import datetime
from collections import OrderedDict
from requests import ConnectionError
from requests import ConnectTimeout

from aws_okta_processor.core.okta import Okta

import responses
import json


class StubDate(datetime):
    pass


class TestOkta(TestBase):
    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_TOKEN_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions',
            json=json.loads(SESSION_RESPONSE)
        )

        okta = Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization.okta.com"
        )

        self.assertEqual(okta.okta_single_use_token, "single_use_token")
        self.assertEqual(okta.organization, "organization.okta.com")
        self.assertEqual(okta.okta_session_id, "session_token")

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.getpass')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_no_pass(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_getpass,
            mock_open,
            mock_chmod
    ):
        mock_getpass.getpass.return_value = "user_pass"

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_TOKEN_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions',
            json=json.loads(SESSION_RESPONSE)
        )

        okta = Okta(
            user_name="user_name",
            organization="organization.okta.com"
        )

        mock_getpass.getpass.assert_called_once()
        self.assertEqual(okta.okta_single_use_token, "single_use_token")
        self.assertEqual(okta.organization, "organization.okta.com")
        self.assertEqual(okta.okta_session_id, "session_token")

    @patch('aws_okta_processor.core.okta.Okta.read_aop_from_okta_session')
    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.datetime', StubDate)
    @patch('aws_okta_processor.core.okta.os.path.isfile')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_cached_session(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_isfile,
            mock_open,
            mock_chmod,
            mock_read_aop_session
    ):
        StubDate.now = classmethod(lambda cls, tz: datetime(1, 1, 1, 0, 0, tzinfo=tz))

        mock_isfile.return_value = True
        mock_enter = MagicMock()
        mock_enter.read.return_value = SESSION_RESPONSE
        mock_open().__enter__.return_value = mock_enter

        session_refresh = json.loads(SESSION_RESPONSE)

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions/me/lifecycle/refresh',
            json=session_refresh
        )

        okta = Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization.okta.com"
        )

        self.assertEqual(okta.okta_session_id, "session_token")
        self.assertEqual(okta.organization, "organization.okta.com")

        mock_read_aop_session.assert_called_once_with(session_refresh)

    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_auth_value_error(
            self,
            mock_print_tty,
            mock_makedirs
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            body="NOT JSON",
            status=500
        )

        with self.assertRaises(SystemExit):
            Okta(
                user_name="user_name",
                user_pass="user_pass",
                organization="organization.okta.com"
            )

        print_tty_calls = [
            call("Error: Status Code: 500"),
            call("Error: Invalid JSON")
        ]

        mock_print_tty.assert_has_calls(print_tty_calls)

    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_auth_send_error(
            self,
            mock_print_tty,
            mock_makedirs
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json={
                "status": "foo",
                "errorSummary": "bar"
            },
            status=500
        )

        with self.assertRaises(SystemExit):
            Okta(
                user_name="user_name",
                user_pass="user_pass",
                organization="organization.okta.com"
            )

        print_tty_calls = [
            call("Error: Status Code: 500"),
            call("Error: Status: foo"),
            call("Error: Summary: bar")
        ]

        mock_print_tty.assert_has_calls(print_tty_calls)

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_mfa_push_challenge(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_MFA_PUSH_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn/factors/id/verify',
            json=json.loads(MFA_WAITING_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn/factors/id/lifecycle/activate/poll',
            json=json.loads(AUTH_TOKEN_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions',
            json=json.loads(SESSION_RESPONSE)
        )

        okta = Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization.okta.com"
        )

        self.assertEqual(okta.okta_single_use_token, "single_use_token")
        self.assertEqual(okta.organization, "organization.okta.com")
        self.assertEqual(okta.okta_session_id, "session_token")

    @patch('aws_okta_processor.core.okta.input_tty')
    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_mfa_totp_challenge(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod,
            mock_input
    ):
        mock_input.return_value = "123456"

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_MFA_TOTP_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn/factors/id/verify',
            json=json.loads(AUTH_TOKEN_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions',
            json=json.loads(SESSION_RESPONSE)
        )

        okta = Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization.okta.com"
        )

        self.assertEqual(okta.okta_single_use_token, "single_use_token")
        self.assertEqual(okta.organization, "organization.okta.com")
        self.assertEqual(okta.okta_session_id, "session_token")

    @patch('aws_okta_processor.core.okta.Okta.get_okta_single_use_token')
    @patch('aws_okta_processor.core.okta.Okta.create_and_store_okta_session')
    @patch('aws_okta_processor.core.okta.input_tty')
    def test_read_aop_from_okta_session_should_read_aop_options(
        self,
        mock_input,
        mock_get_session_id,
        mock_get_token
    ):
        okta = Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization.okta.com",
            no_okta_cache=False
        )
        okta.read_aop_from_okta_session({
            "aws-okta-processor": {
                "user_name": "user2_name",
                "organization": "organization2.okta.com"
            }
        })

        self.assertEqual(okta.user_name, "user2_name")
        self.assertEqual(okta.organization, "organization2.okta.com")


    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.Okta.get_cache_file_path', return_value='/tmp/test.json')
    @patch('aws_okta_processor.core.okta.Okta.get_okta_single_use_token')
    @patch('aws_okta_processor.core.okta.Okta.create_and_store_okta_session')
    @patch('aws_okta_processor.core.okta.input_tty')
    @patch('builtins.open', new_callable=mock_open)
    def test_set_okta_session_should_write_session_data(
        self,
        mock_open_file,
        mock_input,
        mock_get_session_id,
        mock_get_token,
        mock_get_cache_file,
        mock_chmod
    ):
        okta = Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization.okta.com",
            no_okta_cache=False
        )
        okta.set_okta_session({
            "session_stuff": "yes"
        })

        mock_open_file.assert_called_once_with('/tmp/test.json', 'w')
        mock_open_file().write.assert_has_calls([
            call('{'),
            call('"session_stuff"'),
            call(': '),
            call('"yes"'),
            call(', '),
            call('"aws-okta-processor"'),
            call(': '),
            call('{'),
            call('"user_name"'),
            call(': '),
            call('"user_name"'),
            call(', '),
            call('"organization"'),
            call(': '),
            call('"organization.okta.com"'),
            call('}'),
            call('}')
        ])

    @patch('aws_okta_processor.core.okta.input_tty')
    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_mfa_hardware_token_challenge(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod,
            mock_input
    ):
        mock_input.return_value = "123456"

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_MFA_YUBICO_HARDWARE_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn/factors/id/verify',
            json=json.loads(AUTH_TOKEN_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions',
            json=json.loads(SESSION_RESPONSE)
        )

        okta = Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization.okta.com"
        )

        self.assertEqual(okta.okta_single_use_token, "single_use_token")
        self.assertEqual(okta.organization, "organization.okta.com")
        self.assertEqual(okta.okta_session_id, "session_token")

    @patch('aws_okta_processor.core.prompt.input_tty')
    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty', new=MagicMock())
    @patch('aws_okta_processor.core.prompt.print_tty', new=MagicMock())
    @responses.activate
    def test_okta_mfa_push_multiple_factor_challenge(
            self,
            mock_makedirs,
            mock_open,
            mock_chmod,
            mock_input
    ):
        mock_input.return_value = "2"

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_MFA_MULTIPLE_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn/factors/id/verify',
            json=json.loads(MFA_WAITING_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn/factors/id/lifecycle/activate/poll',
            json=json.loads(AUTH_TOKEN_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions',
            json=json.loads(SESSION_RESPONSE)
        )

        okta = Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization.okta.com"
        )

        self.assertEqual(okta.okta_single_use_token, "single_use_token")
        self.assertEqual(okta.organization, "organization.okta.com")
        self.assertEqual(okta.okta_session_id, "session_token")

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_mfa_verify_value_error(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_MFA_PUSH_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn/factors/id/verify',
            body="NOT JSON",
            status=500
        )

        with self.assertRaises(SystemExit):
            Okta(
                user_name="user_name",
                user_pass="user_pass",
                organization="organization.okta.com"
            )

        print_tty_calls = [
            call("Error: Status Code: 500"),
            call("Error: Invalid JSON")
        ]

        mock_print_tty.assert_has_calls(print_tty_calls)

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_mfa_verify_send_error(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_MFA_PUSH_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn/factors/id/verify',
            json={
                "status": "foo",
                "errorSummary": "bar"
            },
            status=500
        )

        with self.assertRaises(SystemExit):
            Okta(
                user_name="user_name",
                user_pass="user_pass",
                organization="organization.okta.com"
            )

        print_tty_calls = [
            call("Error: Status Code: 500"),
            call("Error: Status: foo"),
            call("Error: Summary: bar")
         ]

        mock_print_tty.assert_has_calls(print_tty_calls)

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_session_id_key_error(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_TOKEN_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions',
            json={
                "status": "foo",
                "errorSummary": "bar"
            },
            status=500
        )

        with self.assertRaises(SystemExit):
            Okta(
                user_name="user_name",
                user_pass="user_pass",
                organization="organization.okta.com"
            )

        print_tty_calls = [
            call("Error: Status Code: 500"),
            call("Error: Status: foo"),
            call("Error: Summary: bar")
        ]

        mock_print_tty.assert_has_calls(print_tty_calls)

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_session_id_value_error(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_TOKEN_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions',
            body="NOT JSON",
            status=500
        )

        with self.assertRaises(SystemExit):
            Okta(
                user_name="user_name",
                user_pass="user_pass",
                organization="organization.okta.com"
            )

        print_tty_calls = [
            call("Error: Status Code: 500"),
            call("Error: Invalid JSON")
        ]

        mock_print_tty.assert_has_calls(print_tty_calls)

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.datetime', StubDate)
    @patch('aws_okta_processor.core.okta.os.path.isfile')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_refresh_key_error(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_isfile,
            mock_open,
            mock_chmod
    ):
        StubDate.now = classmethod(lambda cls, tz: datetime(1, 1, 1, 0, 0, tzinfo=tz))

        mock_isfile.return_value = True
        mock_enter = MagicMock()
        mock_enter.read.return_value = SESSION_RESPONSE
        mock_open().__enter__.return_value = mock_enter

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions/me/lifecycle/refresh',
            json={
                "status": "foo",
                "errorSummary": "bar"
            },
            status=500
        )

        Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization.okta.com"
        )

        print_tty_calls = [
            call("Error: Status Code: 500"),
            call("Error: Status: foo"),
            call("Error: Summary: bar")
        ]

        mock_print_tty.assert_has_calls(print_tty_calls)

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.datetime', StubDate)
    @patch('aws_okta_processor.core.okta.os.path.isfile')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_refresh_value_error(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_isfile,
            mock_open,
            mock_chmod
    ):
        StubDate.now = classmethod(lambda cls, tz: datetime(1, 1, 1, 0, 0, tzinfo=tz))

        mock_isfile.return_value = True
        mock_enter = MagicMock()
        mock_enter.read.return_value = SESSION_RESPONSE
        mock_open().__enter__.return_value = mock_enter

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions/me/lifecycle/refresh',
            body="bob",
            status=500
        )

        with self.assertRaises(SystemExit):
            Okta(
                user_name="user_name",
                user_pass="user_pass",
                organization="organization.okta.com"
            )

        print_tty_calls = [
            call("Error: Status Code: 500"),
            call("Error: Invalid JSON")
        ]

        mock_print_tty.assert_has_calls(print_tty_calls)

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_get_applications(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_TOKEN_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions',
            json=json.loads(SESSION_RESPONSE)
        )

        responses.add(
            responses.GET,
            'https://organization.okta.com/api/v1/users/me/appLinks',
            json=json.loads(APPLICATIONS_RESPONSE)
        )

        okta = Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization.okta.com"
        )

        applications = okta.get_applications()
        expected_applications = OrderedDict(
            [
                ('AWS', 'https://organization.okta.com/home/amazon_aws/0oa3omz2i9XRNSRIHBZO/270'),
                ('AWS GOV', 'https://organization.okta.com/home/amazon_aws/0oa3omz2i9XRNSRIHBZO/272')
            ]
        )

        self.assertEqual(applications, expected_applications)

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_get_saml_response(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            json=json.loads(AUTH_TOKEN_RESPONSE)
        )

        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/sessions',
            json=json.loads(SESSION_RESPONSE)
        )

        responses.add(
            responses.GET,
            'https://organization.okta.com/home/amazon_aws/0oa3omz2i9XRNSRIHBZO/270',
            body=SAML_RESPONSE
        )

        okta = Okta(
            user_name="user_name",
            user_pass="user_pass",
            organization="organization.okta.com"
        )

        saml_response = okta.get_saml_response(
            application_url='https://organization.okta.com/home/amazon_aws/0oa3omz2i9XRNSRIHBZO/270'
        )

        self.assertEqual(saml_response, SAML_RESPONSE)

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_connection_timeout(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            body=ConnectTimeout()
        )

        with self.assertRaises(SystemExit):
            Okta(
                user_name="user_name",
                user_pass="user_pass",
                organization="organization.okta.com"
            )

        print_tty_calls = [
            call("Error: Timed Out")
        ]

        mock_print_tty.assert_has_calls(print_tty_calls)

    @patch('aws_okta_processor.core.okta.os.chmod')
    @patch('aws_okta_processor.core.okta.open')
    @patch('aws_okta_processor.core.okta.os.makedirs')
    @patch('aws_okta_processor.core.okta.print_tty')
    @responses.activate
    def test_okta_connection_error(
            self,
            mock_print_tty,
            mock_makedirs,
            mock_open,
            mock_chmod
    ):
        responses.add(
            responses.POST,
            'https://organization.okta.com/api/v1/authn',
            body=ConnectionError()
        )

        with self.assertRaises(SystemExit):
            Okta(
                user_name="user_name",
                user_pass="user_pass",
                organization="organization.okta.com"
            )

        print_tty_calls = [
            call("Error: Connection Error")
        ]

        mock_print_tty.assert_has_calls(print_tty_calls)
