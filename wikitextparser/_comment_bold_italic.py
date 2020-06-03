"""Define the Comment class."""
from typing import Dict, List, MutableSequence, Optional, Union

from regex import compile as regex_compile

from ._wikitext import SubWikiText
from ._spans import COMMENT_PATTERN


COMMA_COMMENT = "'(?>" + COMMENT_PATTERN + ")*+"
COMMENT_COMMA = "(?>" + COMMENT_PATTERN + ")*+'"
BOLD_FULLMATCH = regex_compile(
    COMMA_COMMENT * 2 + "'(.*)'" + COMMENT_COMMA * 2).fullmatch
ITALIC_FULLMATCH = regex_compile(
    COMMA_COMMENT + "'(.*)'" + COMMENT_COMMA).fullmatch
ITALIC_NOEND_FULLMATCH = regex_compile(
    COMMA_COMMENT + "'(.*)").fullmatch


class Comment(SubWikiText):

    """Create a new <!-- comment --> object."""

    @property
    def contents(self) -> str:
        """Return contents of this comment."""
        return self(4, -3)

    @property
    def comments(self) -> List['Comment']:
        return []


class BoldItalic(SubWikiText):

    @property
    def text(self) -> str:
        """Return text value of self (without triple quotes)."""
        # noinspection PyUnresolvedReferences
        return self._match[1]

    @text.setter
    def text(self, s: str):
        # noinspection PyUnresolvedReferences
        b, e = self._match.span(1)
        self[b:e] = s


class Bold(BoldItalic):

    """Define a class for a '''bold''' objects."""

    @property
    def _match(self):
        return BOLD_FULLMATCH(self.string)

    def get_bolds(self, recursive=True) -> List['Bold']:
        if not recursive:
            return []
        return super().get_bolds(True)[1:]


class Italic(BoldItalic):

    """Define a class for a ''italic'' objects."""

    def __init__(
        self,
        string: Union[str, MutableSequence[str]],
        _type_to_spans: Optional[Dict[str, List[List[int]]]] = None,
        _span: Optional[List[int]] = None,
        _type: Optional[Union[str, int]] = None,
        end_token: bool = True,
    ):
        super().__init__(string, _type_to_spans, _span, _type)
        self.end_token: bool = end_token

    @property
    def _match(self):
        if self.end_token:
            return ITALIC_FULLMATCH(self.string)
        return ITALIC_NOEND_FULLMATCH(self.string)

    def get_italics(self, recursive=True) -> List['Bold']:
        if not recursive:
            return []
        return super().get_italics(True)[1:]
