"""Define the Comment class."""


from .wikitext import SubWikiText


class Comment(SubWikiText):

    """Create a new <!-- comment --> object."""

    _type = 'Comment'

    def __init__(
        self,
        string: str or list,
        type_to_spans: list or None=None,
        index: int or None=None,
    ) -> None:
        """Run self._common_init."""
        self._common_init(string, type_to_spans)
        self._index = len(
            self._type_to_spans['Comment']
        ) - 1 if index is None else index

    @property
    def contents(self) -> str:
        """Return contents of this comment."""
        return self.string[4:-3]
