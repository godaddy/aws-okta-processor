import sys
import six

from collections import Mapping
from aws_okta_processor.core.print_tty import print_tty


BAD_INPUT_MESSAGE = "WARNING: Please supply a value from 1 to {}!"


def get_item(items=None, label=None, key=None):
    if not items:
        print_tty("ERROR: No {}s were found!".format(label))
        sys.exit(1)

    if key:
        item_value = get_deep_value(items=items, key=key)

        if item_value:
            return item_value

        print_tty("ERROR: {} {} not found!".format(label, key))
        sys.exit(1)

    if get_deep_length(items=items) > 1:
        print_tty("Select {}:".format(label))
        options = get_options(items=items)
        return get_selection(options=options)

    return get_deep_value(items=items)


def get_deep_length(items=None, length=0):
    for item_value in items.values():
        if isinstance(item_value, Mapping):
            length += get_deep_length(items=item_value)
        else:
            length += 1

    return length


def get_deep_value(items=None, key=None, results=None):
    if results is None:
        results = []
    else:
        if not key and results:
            return results

    for item_key, item_value in six.iteritems(items):
        if isinstance(item_value, Mapping):
            get_deep_value(items=item_value, key=key, results=results)
        elif key:
            if item_key == key:
                results.append(item_value)
        else:
            results.append(item_value)

    if results:
        return results[0]

    return None


def get_selection(options=None):
    print_tty("Selection: ", newline=False)

    try:
        selection = input()
    except KeyboardInterrupt:
        print_tty()
        sys.exit(1)

    except SyntaxError:
        print_tty(BAD_INPUT_MESSAGE.format(len(options)))
        return get_selection(options=options)

    try:
        selection = int(selection)

        if 0 < selection <= len(options):
            return options[selection - 1]

        print_tty(BAD_INPUT_MESSAGE.format(len(options)))
        return get_selection(options=options)

    except ValueError:
        print_tty(BAD_INPUT_MESSAGE.format(len(options)))
        return get_selection(options=options)


def get_options(items=None, options=None, depth=0):
    if options is None:
        options = []

    for key, value in six.iteritems(items):
        if isinstance(value, Mapping):
            print_tty(key, indents=depth)

            options = get_options(
                items=value,
                options=options,
                depth=depth + 1
            )

        else:
            # If the key is an ARN just get everything to left of /
            key = key.split('/')[-1]

            print_tty(
                "[ {} ] {}".format(len(options) + 1, key),
                indents=depth
            )

            options.append(value)

    return options
