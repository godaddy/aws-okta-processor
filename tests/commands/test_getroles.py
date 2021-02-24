import os

from unittest.mock import patch

from tests.test_base import TestBase

from aws_okta_processor.commands.getroles import GetRoles


class TestGetRolesCommand(TestBase):
    @patch("aws_okta_processor.commands.getroles.SAMLFetcher.get_app_roles")
    def test_get_accounts_and_roles_should_return_valid_results(self, mock_get_app_roles):
        self.OPTIONS["--output"] = "json"
        mock_get_app_roles.return_value = {
            "Application": "app-url",
            "User": "jdoe",
            "Organization": "test-org",
            "Accounts": {
                "Account: test-account (1234)": [
                    "role1-deploy"
                ]
            }
        }
        command = GetRoles(self.OPTIONS)
        actual = command.get_accounts_and_roles()

        self.assertEqual({
            'accounts': [
                {
                    'id': '1234',
                    'name': 'test-account',
                    'name_raw': 'Account: test-account (1234)',
                    'roles': [
                        {
                            'name': 'role1-deploy', 'suffix': 'deploy'
                        }
                    ]
                }
            ],
            'application_url': 'app-url',
            'organization': 'test-org',
            'user': 'jdoe'
        }, actual)

    @patch("aws_okta_processor.commands.getroles.GetRoles.get_accounts_and_roles")
    @patch("aws_okta_processor.commands.getroles.sys.stdout.write")
    def test_run_should_return_json(self, mock_sys_stdout_write, mock_get_accounts_and_roles):
        self.OPTIONS["--output"] = "json"
        mock_get_accounts_and_roles.return_value = {
            "application_url": "app-url",
            "accounts": [
                {
                    "name": "test-account",
                    "name_raw": "test-account-raw",
                    "id": "1234",
                    "roles": [
                        {
                            "name": "role1-deploy",
                            "suffix": "deploy"
                        }
                    ]
                }
            ],
            "user": "jdoe",
            "organization": "test-org"
        }
        command = GetRoles(self.OPTIONS)
        command.run()
        mock_sys_stdout_write.assert_called_once_with(
            '{"application_url": "app-url", "accounts": [{"name": "test-account", "name_raw": "test-account-raw", '
            '"id": "1234", "roles": [{"name": "role1-deploy", "suffix": "deploy"}]}], "user": "jdoe", '
            '"organization": "test-org"}'
        )

    @patch("aws_okta_processor.commands.getroles.GetRoles.get_accounts_and_roles")
    @patch("aws_okta_processor.commands.getroles.sys.stdout.write")
    def test_run_should_return_profiles(self, mock_sys_stdout_write, mock_get_accounts_and_roles):
        self.OPTIONS["--output"] = "profiles"
        mock_get_accounts_and_roles.return_value = {
            "application_url": "app-url",
            "accounts": [
                {
                    "name": "test-account",
                    "name_raw": "test-account-raw",
                    "id": "1234",
                    "roles": [
                        {
                            "name": "role1-deploy",
                            "suffix": "deploy"
                        }
                    ]
                }
            ],
            "user": "jdoe",
            "organization": "test-org"
        }
        command = GetRoles(self.OPTIONS)
        command.run()
        mock_sys_stdout_write.assert_called_once_with(
            '\n[test-account-deploy]\ncredential_process=aws-okta-processor authenticate --organization="test-org"'
            ' --user="jdoe" --application="app-url" --role="role1-deploy" --key="test-account-role1-deploy"\n'
        )

    @patch("aws_okta_processor.commands.getroles.GetRoles.get_accounts_and_roles")
    @patch("aws_okta_processor.commands.getroles.sys.stdout.write")
    def test_run_should_return_text(self, mock_sys_stdout_write, mock_get_accounts_and_roles):
        self.OPTIONS["--output"] = "text"
        os.environ["AWS_OKTA_OUTPUT_FORMAT"] = "{account},{role}"

        mock_get_accounts_and_roles.return_value = {
            "application_url": "app-url",
            "accounts": [
                {
                    "name": "test-account",
                    "name_raw": "test-account-raw",
                    "id": "1234",
                    "roles": [
                        {
                            "name": "role1-deploy",
                            "suffix": "deploy"
                        }
                    ]
                }
            ],
            "user": "jdoe",
            "organization": "test-org"
        }
        command = GetRoles(self.OPTIONS)
        command.run()
        mock_sys_stdout_write.assert_called_once_with(
            'test-account,role1-deploy\n'
        )

    def test_get_pass_config(self):
        self.OPTIONS["--pass"] = "user_pass_two"
        authenticate = GetRoles(self.OPTIONS)
        assert authenticate.get_pass() == "user_pass_two"

    def test_get_key_dict(self):
        authenticate = GetRoles(self.OPTIONS)
        key_dict = authenticate.get_key_dict()

        self.assertEqual(
            key_dict,
            {
                "Organization": self.OPTIONS["--organization"],
                "User": self.OPTIONS["--user"],
                "Key": self.OPTIONS["--key"],
            }
        )
