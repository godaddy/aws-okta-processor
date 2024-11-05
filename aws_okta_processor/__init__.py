"""Root Module for the AWS Okta Processor package."""

import importlib.metadata
import tomlkit


def get_version():
    """
    Fetches the current version of the AWS Okta Processor package.

    This function first tries to retrieve the
    version from the installed package distribution.
    If the package is not installed as a distribution (e.g., during development),
    it will instead attempt to load the version directly from the `pyproject.toml` file.

    Returns:
        str: The version string of the package.

    Raises:
        FileNotFoundError: If `pyproject.toml` is
        not found and the package is not installed.
    """
    try:
        # Attempt to get the version from the installed package distribution
        return importlib.metadata.version(__package__)
    except importlib.metadata.PackageNotFoundError:
        # If distribution not found, load the version from pyproject.toml file
        with open("../../pyproject.toml", encoding="utf-8") as pyproject:
            file_contents = pyproject.read()

        # Parse the version from the TOML structure in pyproject.toml
        return tomlkit.parse(file_contents)["tool"]["poetry"]["version"]


# Set the module's __version__ attribute by calling get_version
__version__ = get_version()
