from unittest import TestCase
from mock import patch
from mock import call
from collections import OrderedDict

import aws_okta_processor.core.prompt as prompt


ITEMS = OrderedDict()
ITEMS["ItemOne"] = "ValueOne"
ITEMS["ItemTwo"] = {"ItemTwoNestOne": "ValueTwo"}
ITEMS["ItemThree"] = "ValueThree"
ITEMS["ItemFour"] = {
    "ItemFourNestOne": {
        "ItemFourNestTwo": "ValueFour"
    }
}


class TestPrompt(TestCase):
    def test_get_item(self):
        items = {"ItemOne": "ValueOne"}
        item_value = prompt.get_item(items=items, label="ItemOne")
        self.assertEqual(item_value, "ValueOne")

    @patch('aws_okta_processor.core.prompt.print_tty')
    @patch('aws_okta_processor.core.prompt.sys')
    def test_get_item_no_items(self, mock_sys, mock_print_tty):
        mock_sys.exit.side_effect = SystemExit
        with self.assertRaises(SystemExit):
            prompt.get_item(items={}, label="Item")

        mock_sys.exit.assert_called_once_with(1)
        mock_print_tty.assert_called_with(
            "ERROR: No Items were found!"
        )

    @patch('aws_okta_processor.core.prompt.print_tty')
    @patch('aws_okta_processor.core.prompt.get_options')
    @patch('aws_okta_processor.core.prompt.get_selection')
    def test_get_item_select(self, mock_get_selection, mock_get_options, mock_print_tty): # noqa
        options = ["ValueOne", "ValueTwo"]
        mock_get_options.return_value = options
        prompt.get_item(items=ITEMS, label="Item")
        mock_print_tty.assert_called_once_with("Select Item:")
        mock_get_options.assert_called_once_with(items=ITEMS)
        mock_get_selection.assert_called_once_with(options=options)

    def test_get_item_config(self):
        items = {"item_one": "value_one", "item_two": "value_two"}
        item_value = prompt.get_item(items=items, label="Item", key="item_two") # noqa
        self.assertEqual(item_value, "value_two")

    @patch('aws_okta_processor.core.prompt.print_tty')
    @patch('aws_okta_processor.core.prompt.sys')
    def test_get_item_config_no_match(self, mock_sys, mock_print_tty):
        items = {"item_one": "value_one", "item_two": "value_two"}
        mock_sys.exit.side_effect = SystemExit
        with self.assertRaises(SystemExit):
            prompt.get_item(items=items, label="Item", key="item_three")

        mock_sys.exit.assert_called_once_with(1)
        mock_print_tty.assert_any_call(
            "ERROR: Item item_three not found!"
        )

    @patch('aws_okta_processor.core.prompt.print_tty')
    @patch('aws_okta_processor.core.prompt.input_tty')
    def test_get_selection(self, mock_input, mock_print_tty):
        mock_input.return_value = 1
        options = ["one", "two"]
        item_value = prompt.get_selection(options=options)

        self.assertEqual(item_value, "one")
        mock_print_tty.assert_any_call(
            "Selection: ", newline=False
        )

    @patch('aws_okta_processor.core.prompt.print_tty')
    @patch('aws_okta_processor.core.prompt.input_tty')
    def test_get_selection_bad_input(self, mock_input, mock_print_tty):
        mock_input.side_effect = ["bad_input", 2]
        options = ["one", "two"]
        item_value = prompt.get_selection(options=options)

        self.assertEqual(item_value, "two")
        mock_print_tty.assert_any_call(
            "WARNING: Please supply a value from 1 to 2!"
        )

    @patch('aws_okta_processor.core.prompt.print_tty')
    @patch('aws_okta_processor.core.prompt.input_tty')
    def test_get_selection_bad_int(self, mock_input, mock_print_tty):
        mock_input.side_effect = [0, 2]
        options = ["one", "two"]
        item_value = prompt.get_selection(options=options)

        self.assertEqual(item_value, "two")
        mock_print_tty.assert_any_call(
            "WARNING: Please supply a value from 1 to 2!"
        )

    @patch('aws_okta_processor.core.prompt.print_tty')
    @patch('aws_okta_processor.core.prompt.input_tty')
    def test_get_selection_no_input(self, mock_input, mock_print_tty):
        mock_input.side_effect = [SyntaxError, 2]
        options = ["one", "two"]
        item_value = prompt.get_selection(options=options)

        self.assertEqual(item_value, "two")
        mock_print_tty.assert_any_call(
            "WARNING: Please supply a value from 1 to 2!"
        )

    @patch('aws_okta_processor.core.prompt.print_tty')
    @patch('aws_okta_processor.core.prompt.sys')
    @patch('aws_okta_processor.core.prompt.input_tty')
    def test_get_selection_interrupt(self, mock_input, mock_sys, mock_print_tty): # noqa
        mock_input.side_effect = [KeyboardInterrupt, 2]
        options = ["one"]

        mock_sys.exit.side_effect = SystemExit
        with self.assertRaises(SystemExit):
            prompt.get_selection(options=options)

        mock_print_tty.assert_any_call(
            "Selection: ", newline=False
        )

    @patch('aws_okta_processor.core.prompt.print_tty')
    def test_get_options(self, mock_print_tty):
        print_tty_calls = [
            call("[ 1 ] ItemOne", indents=0),
            call("ItemTwo", indents=0),
            call("[ 2 ] ItemTwoNestOne", indents=1),
            call("[ 3 ] ItemThree", indents=0),
            call("ItemFour", indents=0),
            call("ItemFourNestOne", indents=1),
            call("[ 4 ] ItemFourNestTwo", indents=2)
        ]

        options = prompt.get_options(items=ITEMS)

        self.assertEqual(
            options,
            ["ValueOne", "ValueTwo", "ValueThree", "ValueFour"]
        )

        mock_print_tty.assert_has_calls(print_tty_calls)

    def test_get_deep_value(self):
        value = prompt.get_deep_value(items=ITEMS)
        self.assertEqual(value, "ValueOne")

        value = prompt.get_deep_value(items=ITEMS, key="ItemFourNestTwo")
        self.assertEqual(value, "ValueFour")

        value = prompt.get_deep_value(items=ITEMS, key="DoesNotExist")
        self.assertIs(value, None)

    def test_get_deep_length(self):
        length = prompt.get_deep_length(items=ITEMS)
        self.assertEqual(length, 4)
