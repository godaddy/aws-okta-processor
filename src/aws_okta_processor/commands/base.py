"""The base command."""


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
