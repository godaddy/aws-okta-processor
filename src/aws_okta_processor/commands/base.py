"""The base command."""

import configparser
import os

DOTFILE = '.awsoktaprocessor'
USER_DOTFILE = '~/' + DOTFILE


class Base(object):
    """A base command."""

    def __init__(self, options, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        self.configuration = self.get_configuration(
            options=options
        )

    def run(self):
        raise NotImplementedError(
            'You must implement the run() method yourself!'
        )

    def get_configuration(self, options=None):
        raise NotImplementedError(
            'You must implement the get_configuration() method yourself!'
        )

    @staticmethod
    def get_userfile():
        user_file = os.path.expanduser(USER_DOTFILE)
        if os.path.exists(user_file):
            return user_file
        return None

    @staticmethod
    def get_cwdfile():
        if os.path.exists(DOTFILE):
            return DOTFILE
        return None

    def extend_configuration(self, configuration, command, mapping):
        files = []
        user_file = Base.get_userfile()
        if user_file is not None:
            files.append(user_file)

        cwd_file = Base.get_cwdfile()
        if cwd_file is not None:
            files.append(cwd_file)

        if files:
            config = configparser.ConfigParser()
            config.read(files)

            options = {}
            if config.has_section('defaults'):
                options = dict(**config['defaults'])

            if config.has_section(command):
                options = dict(options, **config[command])

            for k, v in configuration.items():
                if v is None:
                    option_name = mapping[k]
                    configuration[k] = options.get(option_name, None)

        return configuration
