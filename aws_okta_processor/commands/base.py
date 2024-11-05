"""The base command module.

This module defines the `Base` class, which serves as a foundation for command classes.
It provides common functionalities such as configuration handling and file management.
"""

import configparser
import os

DOTFILE = ".awsoktaprocessor"  # Dotfile name in the current directory
USER_DOTFILE = "~/" + DOTFILE  # Dotfile path in the user's home directory


class Base:
    """A base command class.

    This class provides the structure and common methods for command classes.
    Subclasses should implement the `run` and `get_configuration` methods.
    """

    def __init__(self, options, *args, **kwargs):
        """Initialize the Base command.

        Args:
            options (dict): A dictionary of command options.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.args = args
        self.kwargs = kwargs

        self.configuration = self.get_configuration(options=options)

    def run(self):
        """Execute the command.

        Raises:
            NotImplementedError: Indicates that the method should be implemented by subclasses.
        """  # noqa: E501
        raise NotImplementedError("You must implement the run() method yourself!")

    def get_configuration(self, options=None):
        """Retrieve the configuration for the command.

        Args:
            options (dict, optional): A dictionary of options to be used for configuration.

        Raises:
            NotImplementedError: Indicates that the method should be implemented by subclasses.
        """  # noqa: E501
        raise NotImplementedError(
            "You must implement the get_configuration() method yourself!"
        )

    @staticmethod
    def get_userfile():
        """Get the path to the user's dotfile if it exists.

        Expands the user's home directory and checks if the dotfile exists.

        Returns:
            str or None: The full path to the user's dotfile, or None if it doesn't exist.
        """  # noqa: E501
        user_file = os.path.expanduser(USER_DOTFILE)
        if os.path.exists(user_file):
            return user_file
        return None

    @staticmethod
    def get_cwdfile():
        """Get the path to the dotfile in the current working directory if it exists.

        Returns:
            str or None: The filename of the dotfile, or None if it doesn't exist.
        """
        if os.path.exists(DOTFILE):
            return DOTFILE
        return None

    def extend_configuration(self, configuration, command, mapping):
        """Extend the given configuration with options from dotfiles.

        Reads configuration options from dotfiles in the user's home directory
        and the current directory, and updates the given configuration dictionary accordingly.

        Args:
            configuration (dict): The original configuration dictionary.
            command (str): The name of the command section to read from the config files.
            mapping (dict): A mapping from configuration keys to option names in the config files.

        Returns:
            dict: The updated configuration dictionary.
        """  # noqa: E501
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
            if config.has_section("defaults"):
                options = {**config["defaults"]}

            if config.has_section(command):
                options = dict(options, **config[command])

            for k, v in configuration.items():
                if v is None:
                    option_name = mapping[k]
                    configuration[k] = options.get(option_name, None)

        return configuration
