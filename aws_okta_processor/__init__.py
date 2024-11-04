import pkg_resources


def get_version():
    """Function for fetching library version from dist or pyproject.toml"""
    try:
        return pkg_resources.get_distribution(__package__).version
    except pkg_resources.DistributionNotFound:
        with open("../../pyproject.toml", encoding="utf-8") as pyproject:
            file_contents = pyproject.read()

        return tomlkit.parse(file_contents)["tool"]["poetry"]["version"]


__version__ = get_version()
