"""
aws-okta-processor

Usage:
  aws-okta-processor [options] <command> [<args>...]

Options:
  -h, --help     Show this screen.
  --version      Show version.

Command:
  authenticate  used to authenticate into AWS using Okta
  get-roles     used to get AWS roles

Help:
  For help using this tool, please reach out to our Slack channel:
  https://godaddy-oss-slack.herokuapp.com/

See 'aws-okta-processor help <command>' for more information on a specific command.
"""  # noqa


#from inspect import getmembers, isclass

from docopt import docopt

from . import __version__ as VERSION

import six

from . import commands

def get_command(commands=None):
    for command in commands:
        command_name = command[0]

        if command_name != 'Base':
            command_class = command[1]
            return command_class


def main():
    """Main CLI entrypoint."""
    args = docopt(__doc__, version=VERSION, options_first=True)

    argv = [args['<command>']] + args['<args>']
    if args['<command>'] == 'authenticate':
        options = docopt(commands.authenticate.__doc__, argv=argv)
        command = commands.authenticate.Authenticate(options)
        command.run()
    elif args['<command>'] == 'get-roles':
        options = docopt(commands.get_roles.__doc__, argv=argv)
        command = commands.get_roles.GetRolesCommand(options)
        command.run()
    else:
        exit("%r is not a aws-okta-processor command. See 'aws-okta-processor help'." % args['<command>'])

    # Here we'll try to dynamically match the command the user is trying to run
    # with a pre-defined command class we've already created.
    # for (k, v) in six.iteritems(options):
    #     if not k.startswith('--'):
    #         command = k.replace('-', '_')
    #         if hasattr(commands, command) and v:
    #             module = getattr(commands, command)
    #             commands = getmembers(module, isclass)
    #             command_class = get_command(commands=commands)
    #             command = command_class(options)
    #             command.run()
