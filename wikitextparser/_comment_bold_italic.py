"""Define the Comment class."""
from typing import List

from regex import compile as regex_compile

from ._wikitext import SubWikiText
from ._spans import COMMENT_PATTERN


COMMA_COMMENT = "'(?>" + COMMENT_PATTERN + ")*+"
COMMENT_COMMA = "(?>" + COMMENT_PATTERN + ")*+'"
BOLD_FULLMATCH = regex_compile(
    COMMA_COMMENT * 2 + "'(.*)'" + COMMENT_COMMA * 2).fullmatch
ITALIC_FULLMATCH = regex_compile(
    COMMA_COMMENT + "'(.*)'" + COMMENT_COMMA).fullmatch


class Comment(SubWikiText):

    """Create a new <!-- comment --> object."""

    @property
    def contents(self) -> str:
        """Return contents of this comment."""
        return self(4, -3)

    @property
    def comments(self) -> List['Comment']:
        return []


class Bold(SubWikiText):

    """Define a class for a '''bold''' objects."""

    @property
    def text(self) -> str:
        """Return text value of self (without triple quotes)."""
        return BOLD_FULLMATCH(self.string)[1]


class Italic(SubWikiText):

    """Define a class for a ''italic'' objects."""

    @property
    def text(self) -> str:
        """Return text value of self (without double quotes)."""
        return ITALIC_FULLMATCH(self.string)[1]
