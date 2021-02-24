from __future__ import unicode_literals

from six.moves import range

import contextlib2
import io
import os
import sys


def unix_print_tty(string='', indents=0, newline=True):
    with contextlib2.ExitStack() as stack:
        string = indent(indents) + string
        fd = None

        try:
            # Always try reading and writing directly on the tty first.
            fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY)
            tty = io.FileIO(fd, 'w+')
            stack.enter_context(tty)
            text_input = io.TextIOWrapper(tty)
            stack.enter_context(text_input)
            stream = text_input
        except OSError:
            sys.stdout.write(string)

            if newline:
                sys.stdout.write('\n')

            stack.close()

        if fd is not None:
            try:
                stream.write(string)

                if newline:
                    stream.write('\n')
            finally:
                stream.flush()


def win_print_tty(string='', indents=0, newline=True, msvcrt=None):
    string = str(indent(indents) + string)
    for c in string:
        try:
            msvcrt.putch(bytes(c.encode()))
        except TypeError:
            msvcrt.putchc(c)

    if newline:
        try:
            msvcrt.putch(bytes('\r'.encode()))
            msvcrt.putch(bytes('\n'.encode()))
        except TypeError:
            msvcrt.putch('\r')
            msvcrt.putch('\n')


def indent(indents=None):
    indent = ''

    for i in range(indents):
        indent += '  '

    return indent


def import_msvcrt():
    import msvcrt
    return msvcrt


def print_tty(string='', indents=0, newline=True, silent=False):
    try:
        msvcrt = import_msvcrt()
    except ImportError:
        if not silent:
            unix_print_tty(
                string=string,
                indents=indents,
                newline=newline
            )
    else:
        if not silent:
            win_print_tty(
                string=string,
                indents=indents,
                newline=newline,
                msvcrt=msvcrt
            )
