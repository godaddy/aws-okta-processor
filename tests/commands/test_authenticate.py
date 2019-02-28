from test_base import TestBase

from aws_okta_processor.commands.authenticate import Authenticate


class TestAuthenticate(TestBase):
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
