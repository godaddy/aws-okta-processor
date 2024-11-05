"""Module for interacting with the terminal."""

from __future__ import unicode_literals

import io
import os
import sys

from six.moves import range  # type: ignore[import-untyped]

import contextlib2


def import_msvcrt():
    """
    Imports the msvcrt module, which is specific to Windows systems.

    Returns:
        module: The msvcrt module.
    """
    import msvcrt  # pylint: disable=C0415,E0401

    return msvcrt


def input_tty():
    """
    Handles user input from the terminal, adapting for Windows or Unix systems.

    Returns:
        str: The input string entered by the user.
    """
    try:
        msvcrt = import_msvcrt()
    except ImportError:
        # If msvcrt is not available (non-Windows), use Unix-based input method
        return unix_input_tty()

    # Use Windows-specific input method if msvcrt is available
    return win_input_tty(msvcrt)


def unix_input_tty():
    """
    Handles user input in Unix systems, using the tty for input if available.

    Returns:
        str: The line of input entered by the user.
    """
    with contextlib2.ExitStack() as stack:
        try:
            # Open /dev/tty for reading and writing if available
            fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)  # pylint: disable=E1101
            tty = io.FileIO(fd, "r+")
            stack.enter_context(tty)
            input = io.TextIOWrapper(tty)  # pylint: disable=W0622
            stack.enter_context(input)
        except OSError:
            # Fallback to standard input if /dev/tty is not available
            stack.close()
            input = sys.stdin  # pylint: disable=W0622

        line = input.readline()
        # Remove trailing newline if present
        if line[-1] == "\n":
            line = line[:-1]
        return line


def win_input_tty(msvcrt):
    """
    Handles user input in Windows systems using msvcrt.

    Args:
        msvcrt (module): The Windows msvcrt module.

    Returns:
        str: The input string entered by the user.
    """
    pw = ""
    while 1:
        c = msvcrt.getwch()  # Get a character from the console
        if c in ["\r", "\n"]:
            # Break on Enter key
            break
        if c == "\003":
            # Handle Ctrl+C as KeyboardInterrupt
            raise KeyboardInterrupt
        if c == "\b":
            # Handle backspace
            pw = pw[:-1]
        else:
            pw = pw + c

    return pw


def unix_print_tty(string="", indents=0, newline=True):
    """
    Prints a string to the terminal in Unix systems, with optional indentation.

    Args:
        string (str): The string to print.
        indents (int): Number of indentations to add.
        newline (bool): Whether to add a newline after printing.
    """
    with contextlib2.ExitStack() as stack:
        # Apply indentation
        string = indent(indents) + string
        fd = None

        try:
            # Try printing directly to /dev/tty
            fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)  # pylint: disable=E1101
            tty = io.FileIO(fd, "w+")
            stack.enter_context(tty)
            text_input = io.TextIOWrapper(tty)
            stack.enter_context(text_input)
            stream = text_input
        except OSError:
            # Fallback to sys.stdout if /dev/tty is not available
            sys.stdout.write(string)
            if newline:
                sys.stdout.write("\n")
            stack.close()

        # Print to tty stream if available
        if fd is not None:
            try:
                stream.write(string)
                if newline:
                    stream.write("\n")
            finally:
                # Ensure buffer flushes
                stream.flush()


def win_print_tty(string="", indents=0, newline=True, msvcrt=None):
    """
    Prints a string to the terminal in Windows systems, with optional indentation.

    Args:
        string (str): The string to print.
        indents (int): Number of indentations to add.
        newline (bool): Whether to add a newline after printing.
        msvcrt (module): The Windows msvcrt module.
    """
    # Apply indentation
    string = str(indent(indents) + string)
    for c in string:
        try:
            # Print each character individually
            msvcrt.putch(bytes(c.encode()))
        except TypeError:
            # Fallback if encoding fails
            msvcrt.putchc(c)

    # Print newline if specified
    if newline:
        try:
            msvcrt.putch(bytes("\r".encode()))
            msvcrt.putch(bytes("\n".encode()))
        except TypeError:
            msvcrt.putch("\r")
            msvcrt.putch("\n")


def indent(indents=None):
    """
    Generates a string of spaces for indentation.

    Args:
        indents (int): Number of indentation levels (each level is two spaces).

    Returns:
        str: The indentation string.
    """
    indent = ""  # pylint: disable=W0621
    for _ in range(indents):
        indent += "  "
    return indent


def print_tty(string="", indents=0, newline=True, silent=False):
    """
    Prints a string to the terminal, selecting Unix or Windows method as needed.

    Args:
        string (str): The string to print.
        indents (int): Number of indentations to add.
        newline (bool): Whether to add a newline after printing.
        silent (bool): If True, suppresses printing.
    """
    try:
        msvcrt = import_msvcrt()
    except ImportError:
        # If not silent and not on Windows, use Unix print method
        if not silent:
            unix_print_tty(string=string, indents=indents, newline=newline)
    else:
        # If not silent and on Windows, use Windows print method
        if not silent:
            win_print_tty(
                string=string, indents=indents, newline=newline, msvcrt=msvcrt
            )
