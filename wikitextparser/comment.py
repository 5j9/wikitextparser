"""Define the Comment class."""


from .wikitext import SubWikiText


class Comment(SubWikiText):

    """Create a new <!-- comment --> object."""

    def __init__(self, string, spans=None, index=None):
        """Run self._common_init."""
        self._common_init(string, spans)
        if index is None:
            self._index = len(self._spans['comments']) - 1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the Comment."""
        return 'Comment(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['comments'][self._index]

    @property
    def contents(self):
        """Return contents of this comment."""
        return self.string[4:-3]
