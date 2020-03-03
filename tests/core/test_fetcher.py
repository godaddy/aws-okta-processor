from test_base import TestBase

from test_base import SAML_RESPONSE

from mock import patch
from mock import call
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
