import os

from unittest import TestCase

WORKING_DIR = os.path.dirname(__file__)
ABS_PATH = os.path.abspath(WORKING_DIR)
SAML_RESPONSE_PATH = os.path.join(ABS_PATH, "SAML_RESPONSE")
SAML_RESPONSE = open(SAML_RESPONSE_PATH, 'r').read()
SIGN_IN_RESPONSE_PATH = os.path.join(ABS_PATH, "SIGN_IN_RESPONSE")
SIGN_IN_RESPONSE = open(SIGN_IN_RESPONSE_PATH, 'r').read()


class TestBase(TestCase):
    def setUp(self):
        self.OPTIONS = {
            "--environment": False,
            "--user": "user_name",
            "--pass": None,
            "--organization": "org.okta.com",
            "--application": None,
            "--role": None,
            "--key": "key",
            "--duration": "3600",
            "--factor": None,
            "--silent": False
        }
