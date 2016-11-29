"""Define the Comment class."""


from .wikitext import SubWikiText


class Comment(SubWikiText):

    """Create a new <!-- comment --> object."""

    def __init__(
        self,
        string: str or list,
        type_to_spans: list or None=None,
        index: int or None=None,
    ) -> None:
        """Run self._common_init."""
        self._common_init(string, type_to_spans)
        self._index = len(
            self._type_to_spans['comments']
        ) - 1 if index is None else index

    @property
    def _span(self) -> tuple:
        """Return the self-span."""
        return self._type_to_spans['comments'][self._index]

    @property
    def contents(self) -> str:
        """Return contents of this comment."""
        return self.string[4:-3]
