"""Define the Comment class."""


from .wikitext import SubWikiText


class Comment(SubWikiText):

    """Create a new <!-- comment --> object."""

    def __init__(
        self,
        string: str or list,
        spans: list or None=None,
        index: int or None=None,
    ) -> None:
        """Run self._common_init."""
        self._common_init(string, spans)
        if index is None:
            self._index = len(self._type_to_spans['comments']) - 1
        else:
            self._index = index

    def __repr__(self) -> str:
        """Return the string representation of the Comment."""
        return 'Comment(' + repr(self.string) + ')'

    def _get_span(self) -> tuple:
        """Return the self-span."""
        return self._type_to_spans['comments'][self._index]

    @property
    def contents(self) -> str:
        """Return contents of this comment."""
        return self.string[4:-3]
