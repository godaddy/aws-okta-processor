from unittest.mock import patch

import tests
import os

from aws_okta_processor.commands.authenticate import Authenticate
from tests.test_base import TestBase


CREDENTIALS = {
    "AccessKeyId": "access_key_id",
    "SecretAccessKey": "secret_access_key",
    "SessionToken": "session_token"
}


class TestAuthenticate(TestBase):
    @patch("aws_okta_processor.commands.authenticate.JSONFileCache")
    @patch("aws_okta_processor.commands.authenticate.SAMLFetcher")
    def test_authenticate(self, mock_saml_fetcher, mock_json_file_cache):
        mock_saml_fetcher().fetch_credentials.return_value = CREDENTIALS
        auth = Authenticate(self.OPTIONS)
        credentials = auth.authenticate()

        mock_json_file_cache.assert_called_once_with()
        assert credentials == CREDENTIALS

    @patch("aws_okta_processor.commands.authenticate.print")
    def test_run(self, mock_print):
        auth = Authenticate(self.OPTIONS)
        auth.authenticate = (lambda: CREDENTIALS)
        auth.run()

        mock_print.assert_called_once_with(
            '{"AccessKeyId": "access_key_id", '
            '"SecretAccessKey": "secret_access_key", '
            '"SessionToken": "session_token", '
            '"Version": 1}'
        )

    @patch("aws_okta_processor.commands.authenticate.os")
    @patch("aws_okta_processor.commands.authenticate.print")
    def test_run_nt(self, mock_print, mock_os):
        mock_os.name = "nt"
        self.OPTIONS["--environment"] = True
        auth = Authenticate(self.OPTIONS)
        auth.authenticate = (lambda: CREDENTIALS)
        auth.run()

        mock_print.assert_called_once_with(
            "$env:AWS_ACCESS_KEY_ID='access_key_id'; "
            "$env:AWS_SECRET_ACCESS_KEY='secret_access_key'; "
            "$env:AWS_SESSION_TOKEN='session_token'"
        )

    @patch("aws_okta_processor.commands.authenticate.os")
    @patch("aws_okta_processor.commands.authenticate.print")
    def test_run_linux(self, mock_print, mock_os):
        mock_os.name = "linux"
        self.OPTIONS["--environment"] = True
        auth = Authenticate(self.OPTIONS)
        auth.authenticate = (lambda: CREDENTIALS)
        auth.run()

        mock_print.assert_called_once_with(
            "export AWS_ACCESS_KEY_ID='access_key_id' && "
            "export AWS_SECRET_ACCESS_KEY='secret_access_key' && "
            "export AWS_SESSION_TOKEN='session_token'"
        )

    def test_get_configuration_env(self):
        os.environ["AWS_OKTA_ENVIRONMENT"] = "1"
        auth = Authenticate(self.OPTIONS)
        del os.environ["AWS_OKTA_ENVIRONMENT"]

        assert auth.configuration["AWS_OKTA_ENVIRONMENT"] == "1"

    def test_output_export_command_with_fish_as_target_shell(self):
        """ Tests the export command for fish shell """

        self.OPTIONS["--target-shell"] = "fish"
        auth = Authenticate(self.OPTIONS)
        credentials = {
            "AccessKeyId": "XXXXX",
            "SecretAccessKey": "YYYYY",
            "SessionToken": "ZZZZZ"
        }
        self.assertNotIsInstance(
            auth.unix_output(credentials).index("set --export"),
            ValueError
        )

    def test_output_export_command_with_default_target_shell(self):
        """ Tests the export command for bash (default target shell) """

        auth = Authenticate(self.OPTIONS)
        credentials = {
            "AccessKeyId": "XXXXX",
            "SecretAccessKey": "YYYYY",
            "SessionToken": "ZZZZZ"
        }
        self.assertNotIsInstance(
            auth.unix_output(credentials).index("export "),
            ValueError
        )
        self.assertNotIsInstance(
            auth.unix_output(credentials).index(" && "),
            ValueError
        )

    def test_output_export_command_for_windows(self):
        """ Tests the export command for windows operating system """

        auth = Authenticate(self.OPTIONS)
        credentials = {
            "AccessKeyId": "XXXXX",
            "SecretAccessKey": "YYYYY",
            "SessionToken": "ZZZZZ"
        }
        self.assertNotIsInstance(
            auth.nt_output(credentials).index("$env:"),
            ValueError
        )

    def test_get_pass_config(self):
        self.OPTIONS["--pass"] = "user_pass_two"
        authenticate = Authenticate(self.OPTIONS)
        assert authenticate.get_pass() == "user_pass_two"

    def test_get_key_dict(self):
        authenticate = Authenticate(self.OPTIONS)
        key_dict = authenticate.get_key_dict()

        self.assertEqual(
            key_dict,
            {
                "Organization": self.OPTIONS["--organization"],
                "User": self.OPTIONS["--user"],
                "Key": self.OPTIONS["--key"],
            }
        )


    @patch('aws_okta_processor.commands.base.Base.get_userfile',
           return_value=tests.get_fixture('userhome/.awsoktaprocessor'))
    @patch('aws_okta_processor.commands.base.Base.get_cwdfile',
           return_value=tests.get_fixture('.awsoktaprocessor'))
    def test_extends_by_file(self, mock_userfile, mock_cwdfile):
        authenticate = Authenticate(self.OPTIONS)

        config = authenticate.get_configuration(options={})

        self.assertEqual('okta-env1', config['AWS_OKTA_ENVIRONMENT'])
        self.assertEqual('okta-user1', config['AWS_OKTA_USER'])
        self.assertEqual('okta-pass1', config['AWS_OKTA_PASS'])
        self.assertEqual('org1-from-home', config['AWS_OKTA_ORGANIZATION'])
