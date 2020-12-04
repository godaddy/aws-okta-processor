from unittest.mock import patch

import tests
from tests.test_base import TestBase

from aws_okta_processor.commands.base import Base


class TestBase(TestBase):
    def test_get_config(self):
        with self.assertRaises(NotImplementedError) as context:
            Base(self.OPTIONS)

    @patch('os.path.expanduser', side_effect=tests.expand_user_side_effect)
    def test_get_userfile_should_locate_user_file(self, mock_expanduser):
        actual = Base.get_userfile()
        self.assertEqual(tests.get_fixture('userhome/.awsoktaprocessor'), actual)

    @patch('os.path.exists', side_effect=tests.get_os_exists_side_effect({'.awsoktaprocessor': True}))
    def test_get_cwdfile_should_locate_cwd_file(self, mock_os_exists):
        actual = Base.get_cwdfile()
        self.assertEqual('.awsoktaprocessor', actual)

    @patch('aws_okta_processor.commands.base.Base.get_userfile',
           return_value=tests.get_fixture('userhome/.awsoktaprocessor'))
    @patch('aws_okta_processor.commands.base.Base.get_cwdfile',
           return_value=tests.get_fixture('.awsoktaprocessor'))
    def test_extends_configuration_should_extend_user_and_cwd(self, mock_userfile, mock_cwdfile):
        authenticate = tests.TestCommand(self.OPTIONS)

        config = authenticate.extend_configuration({
            'AWS_OKTA_ENVIRONMENT': None,
            'AWS_OKTA_ORGANIZATION': 'org1',
        }, 'authenticate', {
            'AWS_OKTA_ENVIRONMENT': 'environment',
            'AWS_OKTA_ORGANIZATION': 'organization'
        })

        self.assertEqual('okta-env1', config['AWS_OKTA_ENVIRONMENT'])
        self.assertEqual('org1', config['AWS_OKTA_ORGANIZATION'])