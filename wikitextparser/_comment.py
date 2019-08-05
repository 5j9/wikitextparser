"""Define the Comment class."""
from typing import List

from ._wikitext import SubWikiText


class Comment(SubWikiText):

    """Create a new <!-- comment --> object."""

    @property
    def contents(self) -> str:
        """Return contents of this comment."""
        return self(4, -3)

    @property
    def comments(self) -> List['Comment']:
        return []
