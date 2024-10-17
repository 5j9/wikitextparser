from __future__ import annotations

from typing import MutableSequence

from regex import DOTALL, MULTILINE, Match

from ._spans import TypeToSpans
from ._wikitext import SubWikiText, rc

COMMENT_PATTERN = r'<!--[\s\S]*?(?>-->|\Z)'
COMMA_COMMENT = "'(?>" + COMMENT_PATTERN + ')*+'
COMMENT_COMMA = '(?>' + COMMENT_PATTERN + ")*+'"
BOLD_FULLMATCH = rc(
    COMMA_COMMENT * 2 + "'(.*?)(?>'" + COMMENT_COMMA * 2 + '|$)',
    MULTILINE | DOTALL,
).fullmatch
ITALIC_FULLMATCH = rc(
    COMMA_COMMENT + "'(.*?)(?>'" + COMMENT_COMMA + '|$)', DOTALL
).fullmatch
ITALIC_NOEND_FULLMATCH = rc(COMMA_COMMENT + "'(.*)", DOTALL).fullmatch


class Comment(SubWikiText):
    __slots__ = ()

    @property
    def contents(self) -> str:
        """Return contents of this comment."""
        s = self.string
        if s[-3:] == '-->':
            return s[4:-3]
        return s[4:]

    @property
    def comments(self) -> list[Comment]:
        return []


class BoldItalic(SubWikiText):
    __slots__ = ()

    @property
    def _match(self) -> Match[str]: ...

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
    def _content_span(self) -> tuple[int, int]:
        # noinspection PyUnresolvedReferences
        return self._match.span(1)


class Bold(BoldItalic):
    __slots__ = ()

    @property
    def _match(self) -> Match[str]:
        return BOLD_FULLMATCH(self.string)  # type: ignore


class Italic(BoldItalic):
    __slots__ = ('end_token',)

    def __init__(
        self,
        string: str | MutableSequence[str],
        _type_to_spans: TypeToSpans | None = None,
        _span: list[int] | None = None,
        _type: str | int | None = None,
        end_token: bool = True,
    ):
        """Initialize the Italic object.

        :param end_token: set to True if the italic object ends with a '' token
            False otherwise.
        """
        super().__init__(string, _type_to_spans, _span, _type)
        self.end_token = end_token

    @property
    def _match(self) -> Match[str]:
        if self.end_token:
            return ITALIC_FULLMATCH(self.string)  # type: ignore
        return ITALIC_NOEND_FULLMATCH(self.string)  # type: ignore
