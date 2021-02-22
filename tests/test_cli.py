import os
import sys

from aws_okta_processor import cli

from unittest.mock import patch
from unittest import TestCase

class TestCli(TestCase):
    def test_main_should_run_authenticate(self):
        sys.argv = ["aws-okta-processor", "authenticate"]
        with patch("aws_okta_processor.commands.authenticate.Authenticate.run") as mock_run:
            cli.main()
        mock_run.assert_called_once()

    def test_main_should_run_getroles(self):
        sys.argv = ["aws-okta-processor", "get-roles"]
        with patch("aws_okta_processor.commands.getroles.GetRoles.run") as mock_run:
            cli.main()
        mock_run.assert_called_once()

    def test_main_should_raise_exception_on_missing_command(self):
        sys.argv = ["aws-okta-processor", "not-found"]
        self.assertRaises(SystemExit, cli.main)
