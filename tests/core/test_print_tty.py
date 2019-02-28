from unittest import TestCase
from mock import patch
from mock import call
from mock import MagicMock

import aws_okta_processor.core.print_tty as print_tty


class Test(TestCase):
    @patch('aws_okta_processor.core.print_tty.import_msvcrt')
    @patch('aws_okta_processor.core.print_tty.contextlib2')
    @patch('aws_okta_processor.core.print_tty.os')
    @patch('aws_okta_processor.core.print_tty.io')
    def test_unix_print_tty(
            self,
            mock_io,
            mock_os,
            mock_conextlib2,
            mock_import_msvcrt
    ):
        mock_import_msvcrt.side_effect = ImportError
        mock_stack = MagicMock()
        mock_conextlib2.ExitStack.return_value = mock_stack
        mock_text_wrapper = MagicMock()
        mock_io.TextIOWrapper.return_value = mock_text_wrapper

        calls = [
            call(u'STRING'),
            call(u'\n')
        ]

        print_tty.print_tty("STRING")
        mock_text_wrapper.write.assert_has_calls(calls)
        mock_os.open.assert_called_once()

    @patch('aws_okta_processor.core.print_tty.import_msvcrt')
    @patch('aws_okta_processor.core.print_tty.contextlib2')
    @patch('aws_okta_processor.core.print_tty.os')
    @patch('aws_okta_processor.core.print_tty.io')
    def test_unix_print_tty_no_newline(
            self,
            mock_io,
            mock_os,
            mock_conextlib2,
            mock_import_msvcrt
    ):
        mock_import_msvcrt.side_effect = ImportError
        mock_stack = MagicMock()
        mock_conextlib2.ExitStack.return_value.__enter__.return_value = mock_stack # noqa
        mock_text_wrapper = MagicMock()
        mock_io.TextIOWrapper.return_value = mock_text_wrapper

        print_tty.print_tty("STRING", newline=False)
        mock_os.open.assert_called_once()
        mock_stack.enter_context.called_once_with(mock_text_wrapper)
        mock_text_wrapper.write.assert_called_once_with(u'STRING')
        mock_text_wrapper.flush.assert_called_once()

    @patch('aws_okta_processor.core.print_tty.import_msvcrt')
    @patch('aws_okta_processor.core.print_tty.contextlib2')
    @patch('aws_okta_processor.core.print_tty.os')
    @patch('aws_okta_processor.core.print_tty.io')
    def test_unix_print_tty_indent(
            self,
            mock_io,
            mock_os,
            mock_conextlib2,
            mock_import_msvcrt
    ):
        mock_import_msvcrt.side_effect = ImportError
        mock_stack = MagicMock()
        mock_conextlib2.ExitStack.return_value.__enter__.return_value = mock_stack # noqa
        mock_text_wrapper = MagicMock()
        mock_io.TextIOWrapper.return_value = mock_text_wrapper

        print_tty.print_tty("STRING", indents=1, newline=False)
        mock_os.open.assert_called_once()
        mock_stack.enter_context.called_once_with(mock_text_wrapper)
        mock_text_wrapper.write.assert_called_once_with(u'  STRING')
        mock_text_wrapper.flush.assert_called_once()

    @patch('aws_okta_processor.core.print_tty.import_msvcrt')
    @patch('aws_okta_processor.core.print_tty.sys.stdout')
    @patch('aws_okta_processor.core.print_tty.contextlib2')
    @patch('aws_okta_processor.core.print_tty.os')
    @patch('aws_okta_processor.core.print_tty.io')
    def test_unix_print_tty_print(
            self,
            mock_io,
            mock_os,
            mock_conextlib2,
            mock_print,
            mock_import_msvcrt
    ):
        mock_import_msvcrt.side_effect = ImportError
        mock_stack = MagicMock()
        mock_conextlib2.ExitStack.return_value.__enter__.return_value = mock_stack # noqa
        mock_text_wrapper = MagicMock()
        mock_io.TextIOWrapper.return_value = mock_text_wrapper
        mock_os.open.side_effect = OSError

        calls = [
            call(u'STRING'),
            call(u'\n')
        ]

        print_tty.print_tty("STRING")
        mock_print.write.assert_has_calls(calls)
        mock_stack.close.assert_called_once()
        mock_text_wrapper.write.assert_not_called()

    @patch('aws_okta_processor.core.print_tty.import_msvcrt')
    @patch('aws_okta_processor.core.print_tty.sys.stdout')
    @patch('aws_okta_processor.core.print_tty.contextlib2')
    @patch('aws_okta_processor.core.print_tty.os')
    @patch('aws_okta_processor.core.print_tty.io')
    def test_unix_print_tty_print_no_newline(
            self,
            mock_io,
            mock_os,
            mock_conextlib2,
            mock_print,
            mock_import_msvcrt
    ):
        mock_import_msvcrt.side_effect = ImportError
        mock_stack = MagicMock()
        mock_conextlib2.ExitStack.return_value.__enter__.return_value = mock_stack # noqa
        mock_text_wrapper = MagicMock()
        mock_io.TextIOWrapper.return_value = mock_text_wrapper
        mock_os.open.side_effect = OSError

        print_tty.print_tty("STRING", newline=False)
        mock_print.write.assert_called_once_with("STRING")
        mock_stack.close.assert_called_once()
        mock_text_wrapper.write.assert_not_called()

    @patch('aws_okta_processor.core.print_tty.import_msvcrt')
    @patch('aws_okta_processor.core.print_tty.sys.stdout')
    @patch('aws_okta_processor.core.print_tty.contextlib2')
    @patch('aws_okta_processor.core.print_tty.os')
    @patch('aws_okta_processor.core.print_tty.io')
    def test_unix_print_tty_print_indent(
            self,
            mock_io,
            mock_os,
            mock_conextlib2,
            mock_print,
            mock_import_msvcrt
    ):
        mock_import_msvcrt.side_effect = ImportError
        mock_stack = MagicMock()
        mock_conextlib2.ExitStack.return_value.__enter__.return_value = mock_stack  # noqa
        mock_text_wrapper = MagicMock()
        mock_io.TextIOWrapper.return_value = mock_text_wrapper
        mock_os.open.side_effect = OSError

        print_tty.print_tty("STRING", indents=1, newline=False)
        mock_print.write.assert_called_once_with("  STRING")
        mock_stack.close.assert_called_once()
        mock_text_wrapper.write.assert_not_called()

    @patch('aws_okta_processor.core.print_tty.import_msvcrt')
    def test_win_print_tty(self, mock_import_msvcrt):
        mock_msvcrt = MagicMock()
        mock_import_msvcrt.return_value = mock_msvcrt
        calls = ([], [])
        for char in list("STRING\r\n"):
            calls[0].append(call(char))
            calls[1].append(call(bytes(char.encode())))

        print_tty.print_tty("STRING")

        try:
            mock_msvcrt.putch.assert_has_calls(calls[0])
        except AssertionError:
            mock_msvcrt.putch.assert_has_calls(calls[1])

    @patch('aws_okta_processor.core.print_tty.import_msvcrt')
    def test_win_print_tty_no_newline(self, mock_import_msvcrt):
        mock_msvcrt = MagicMock()
        mock_import_msvcrt.return_value = mock_msvcrt
        calls = ([], [])
        for char in list("STRING"):
            calls[0].append(call(char))
            calls[1].append(call(bytes(char.encode())))

        print_tty.print_tty("STRING", newline=False)
        mock_import_msvcrt.assert_called()

        try:
            mock_msvcrt.putch.assert_has_calls(calls[0])
        except AssertionError:
            mock_msvcrt.putch.assert_has_calls(calls[1])

    @patch('aws_okta_processor.core.print_tty.import_msvcrt')
    def test_win_print_tty_indent(self, mock_import_msvcrt):
        mock_msvcrt = MagicMock()
        mock_import_msvcrt.return_value = mock_msvcrt
        calls = ([], [])
        for char in list("  STRING"):
            calls[0].append(call(char))
            calls[1].append(call(bytes(char.encode())))

        print_tty.print_tty("STRING", indents=1, newline=False)
        mock_import_msvcrt.assert_called()

        try:
            mock_msvcrt.putch.assert_has_calls(calls[0])
        except AssertionError:
            mock_msvcrt.putch.assert_has_calls(calls[1])
