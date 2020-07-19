"""Define the Comment class."""
from typing import Dict, List, MutableSequence, Optional, Union

from regex import MULTILINE, compile as regex_compile

from ._wikitext import SubWikiText
from ._spans import COMMENT_PATTERN


COMMA_COMMENT = "'(?>" + COMMENT_PATTERN + ")*+"
COMMENT_COMMA = "(?>" + COMMENT_PATTERN + ")*+'"
BOLD_FULLMATCH = regex_compile(
    COMMA_COMMENT * 2 + "'(.*?)(?>'" + COMMENT_COMMA * 2 + "|$)",
    MULTILINE).fullmatch
ITALIC_FULLMATCH = regex_compile(
    COMMA_COMMENT + "'(.*?)(?>'" + COMMENT_COMMA + "|$)").fullmatch
ITALIC_NOEND_FULLMATCH = regex_compile(
    COMMA_COMMENT + "'(.*)").fullmatch


class Comment(SubWikiText):
    __slots__ = ()

    @property
    def contents(self) -> str:
        """Return contents of this comment."""
        return self(4, -3)

    @property
    def comments(self) -> List['Comment']:
        return []


class BoldItalic(SubWikiText):
    __slots__ = ()

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

    @property
    def _relative_contents_end(self) -> tuple:
        # noinspection PyUnresolvedReferences
        return self._match.span(1)


class Bold(BoldItalic):
    __slots__ = ()

    @property
    def _match(self):
        return BOLD_FULLMATCH(self.string)


class Italic(BoldItalic):
    __slots__ = 'end_token',

    def __init__(
        self,
        string: Union[str, MutableSequence[str]],
        _type_to_spans: Optional[Dict[str, List[List[int]]]] = None,
        _span: Optional[List[int]] = None,
        _type: Optional[Union[str, int]] = None,
        end_token: bool = True,
    ):
        """Initialize the Italic object.

        :param end_token: set to True if the italic object ends with a '' token
            False otherwise.
        """
        super().__init__(string, _type_to_spans, _span, _type)
        self.end_token = end_token

    @property
    def _match(self):
        if self.end_token:
            return ITALIC_FULLMATCH(self.string)
        return ITALIC_NOEND_FULLMATCH(self.string)
