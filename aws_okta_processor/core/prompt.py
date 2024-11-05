"""Module for prompting the user for input."""

import sys
from collections.abc import Mapping

import six  # type: ignore[import-untyped]
from aws_okta_processor.core.tty import print_tty, input_tty


def get_item(items=None, label=None, key=None):
    """
    Retrieves a specific item or prompts the user to select one from multiple options.

    Args:
        items (dict): The collection of items to search within.
        label (str): Descriptive label of the items (e.g., "Account", "Role").
        key (str, optional): Specific key to look up in items.

    Returns:
        object: The value associated with the provided key, or the user-selected item.

    Exits:
        If items is empty or the key is not found, exits with an error message.
    """
    if not items:
        # Display error if items are empty and exit
        print_tty(f"ERROR: No {label}s were found!")
        sys.exit(1)

    if key:
        # Attempt to get the specific item value for the given key
        item_value = get_deep_value(items=items, key=key)
        if item_value:
            return item_value

        # If the key does not exist, display error and exit
        print_tty(f"ERROR: {label} {key} not found!")
        sys.exit(1)

    # If there are multiple items, prompt user to select one
    if get_deep_length(items=items) > 1:
        print_tty(f"Select {label}:")
        options = get_options(items=items)
        return get_selection(options=options)

    # Return single item value if only one exists
    return get_deep_value(items=items)


def get_deep_length(items=None, length=0):
    """
    Recursively calculates the number of items in a nested dictionary.

    Args:
        items (dict): Dictionary with nested dictionaries.
        length (int): Running count of items found.

    Returns:
        int: Total count of non-dictionary items.
    """
    for item_value in items.values():
        if isinstance(item_value, Mapping):
            # Recursively count items in nested dictionaries
            length += get_deep_length(items=item_value)
        else:
            # Increment length for each non-dictionary item
            length += 1

    return length


def get_deep_value(items=None, key=None, results=None):
    """
    Recursively searches for a specific key's value in a nested dictionary.

    Args:
        items (dict): Dictionary with nested dictionaries.
        key (str, optional): Key to search for.
        results (list, optional): Accumulated results from recursive calls.

    Returns:
        object: The first found value associated with the key, or None if not found.
    """
    if results is None:
        results = []
    else:
        if not key and results:
            # Return early if results are already accumulated and no key specified
            return results

    for item_key, item_value in six.iteritems(items):
        if isinstance(item_value, Mapping):
            # Recursively search in nested dictionaries
            get_deep_value(items=item_value, key=key, results=results)
        elif key:
            if item_key == key:
                # Append item to results if key matches
                results.append(item_value)
        else:
            # Append item to results if no specific key is provided
            results.append(item_value)

    if results:
        # Return the first found result
        return results[0]

    return None


def get_selection(options=None):
    """
    Prompts the user to select an option from a list.

    Args:
        options (list): List of available options to choose from.

    Returns:
        object: The selected option based on user input.

    Exits:
        If user interrupts the input process with Ctrl+C.
    """
    print_tty("Selection: ", newline=False)

    try:
        # Wait for user input
        selection = input_tty()
    except KeyboardInterrupt:
        # Handle user interrupt gracefully
        print_tty()
        sys.exit(1)
    except SyntaxError:
        # Handle syntax error and re-prompt the user
        print_tty(f"WARNING: Please supply a value from 1 to {len(options)}!")
        return get_selection(options=options)

    try:
        # Convert selection to an integer and validate range
        selection = int(selection)
        if 0 < selection <= len(options):
            return options[selection - 1]

        # If out of range, display error and re-prompt
        print_tty(f"WARNING: Please supply a value from 1 to {len(options)}!")
        return get_selection(options=options)

    except ValueError:
        # Handle non-integer input and re-prompt
        print_tty(f"WARNING: Please supply a value from 1 to {len(options)}!")
        return get_selection(options=options)


def get_options(items=None, options=None, depth=0):
    """
    Displays options from a nested dictionary and accumulates them for selection.

    Args:
        items (dict): Dictionary with items to display.
        options (list, optional): List to accumulate options for selection.
        depth (int): Current depth of recursion for indentation.

    Returns:
        list: List of accumulated options for user selection.
    """
    if options is None:
        options = []

    for key, value in six.iteritems(items):
        if isinstance(value, Mapping):
            # Print category label at current indentation level
            print_tty(key, indents=depth)
            # Recursively add sub-options
            options = get_options(items=value, options=options, depth=depth + 1)
        else:
            # For specific values, adjust key display if it contains an ARN
            key = key.split("/")[-1]
            # Print option with an index
            print_tty(f"[ {len(options) + 1} ] {key}", indents=depth)
            options.append(value)

    return options
