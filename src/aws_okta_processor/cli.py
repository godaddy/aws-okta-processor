"""
aws-okta-processor

Usage:
  aws-okta-processor authenticate [--environment] [--organization=<okta_organization>]
                                  [--user=<user_name>] [--pass=<user_pass>]
                                  [--application=<okta_application>]
                                  [--role=<role_name>]
                                  [--duration=<duration_seconds>]
                                  [--key=<key>]
                                  [--factor=<factor>]
                                  [--silent] [--no-okta-cache] [--no-aws-cache]

  aws-okta-processor -h | --help
  aws-okta-processor --version

Options:
  -h --help                                                  Show this screen.
  --version                                                  Show version.
  --no-okta-cache                                            Do not read okta cache.
  --no-aws-cache                                             Do not read aws cache.
  -e --environment                                           Dump auth into ENV variables.
  -u <user_name> --user=<user_name>                          Okta user name.
  -p <user_pass> --pass=<user_pass>                          Okta user password.
  -o <okta_organization> --organization=<okta_organization>  Okta organization domain.
  -a <okta_application> --application=<okta_application>     Okta application url.
  -r <role_name> --role=<role_name>                          AWS role ARN.
  -d <duration_seconds> --duration=<duration_seconds>        Duration of role session [default: 3600].
  -k <key> --key=<key>                                       Key used for generating and accessing cache.
  -f <factor> --factor=<factor>                              Factor type for MFA.
  -s --silent                                                Run silently.

Help:
  For help using this tool, please reach out to our Slack channel:
  https://godaddy-oss-slack.herokuapp.com/
"""  # noqa


from inspect import getmembers, isclass

from docopt import docopt

from . import __version__ as VERSION

import six


def get_command(commands=None):
    for command in commands:
        command_name = command[0]

        if command_name != 'Base':
            command_class = command[1]
            return command_class


def main():
    """Main CLI entrypoint."""
    from . import commands
    options = docopt(__doc__, version=VERSION)

    # Here we'll try to dynamically match the command the user is trying to run
    # with a pre-defined command class we've already created.
    for (k, v) in six.iteritems(options):
        if hasattr(commands, k) and v:
            module = getattr(commands, k)
            commands = getmembers(module, isclass)
            command_class = get_command(commands=commands)
            command = command_class(options)
            command.run()
