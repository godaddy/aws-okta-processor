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
  For help using this tool, please reach out to our Slack channel:
  https://godaddy-oss-slack.herokuapp.com/

See 'aws-okta-processor <command> -h' for more information on a specific command.
"""  # noqa


from docopt import docopt

from . import __version__ as VERSION

from . import commands


def main():
    """Main CLI entrypoint."""
    args = docopt(__doc__, version=VERSION, options_first=True)

    try:
        argv = [args['<command>']] + args['<args>']
        if args['<command>'] == 'authenticate':
            options = docopt(commands.authenticate.__doc__, argv=argv)
            command = commands.authenticate.Authenticate(options)
            command.run()
        elif args['<command>'] == 'get-roles':
            options = docopt(commands.getroles.__doc__, argv=argv)
            command = commands.getroles.GetRoles(options)
            command.run()
        else:
            exit("%r is not a aws-okta-processor command. See 'aws-okta-processor --help'." % args['<command>'])
    except KeyboardInterrupt:
        exit(0)
