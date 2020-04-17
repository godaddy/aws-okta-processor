import os

from aws_okta_processor.commands.base import Base

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


class TestCommand(Base):
    def __init__(self, options):
        super().__init__(self, options)

    def get_configuration(self, options=None):
        return {}


def get_fixture(path):
    return os.path.join(FIXTURE_PATH, path)


def expand_user_side_effect(*args):
    return args[0].replace('~/', get_fixture('userhome/'))


def get_os_exists_side_effect(effects):
    def side_effect(*args):
        if args[0] in effects:
            return effects[args[0]]
        raise RuntimeError('os_exists path "%s" not handled' % args[0])
    return side_effect
