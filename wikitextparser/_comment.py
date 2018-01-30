"""Define the Comment class."""


from ._wikitext import SubWikiText


class Comment(SubWikiText):

    """Create a new <!-- comment --> object."""

    @property
    def contents(self) -> str:
        """Return contents of this comment."""
        return self.string[4:-3]
