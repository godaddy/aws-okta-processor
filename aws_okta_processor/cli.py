"""
Usage:
  aws-okta-processor [options] <command> [<args>...]

Options:
  -h, --help     Show this screen.
  --version      Show version.

Commands:
  authenticate  used to authenticate into AWS using Okta
  get-roles     used to get AWS roles

Help:
  For help using this tool, visit here for docs and issues:
  https://github.com/godaddy/aws-okta-processor

See 'aws-okta-processor <command> -h' for more information on a specific command.
"""  # noqa

import sys

from docopt import docopt  # type: ignore[import-untyped]

from . import __version__ as VERSION

from . import commands


def main():
    """Main CLI entrypoint."""
    args = docopt(__doc__, version=VERSION, options_first=True)

    try:
        argv = [args["<command>"]] + args["<args>"]
        if args["<command>"] == "authenticate":
            options = docopt(commands.authenticate.__doc__, argv=argv)
            command = commands.authenticate.Authenticate(options)
            command.run()
        elif args["<command>"] == "get-roles":
            options = docopt(commands.getroles.__doc__, argv=argv)
            command = commands.getroles.GetRoles(options)
            command.run()
        else:
            sys.exit(
                f"{args['<command>']!r} is not an aws-okta-processor "
                "command. See 'aws-okta-processor --help'."
            )
    except KeyboardInterrupt:
        sys.exit(0)
