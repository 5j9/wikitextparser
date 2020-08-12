"""Define the Section class."""
from typing import Optional

from regex import compile as regex_compile

from ._wikitext import SubWikiText

HEADER_MATCH = regex_compile(rb'(={1,6})([^\n]+?)\1[ \t]*(\n|\Z)').match


class Section(SubWikiText):

    __slots__ = '_header_match_cache'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._header_match_cache = None, None

    @property
    def _header_match(self):
        cached_match, cached_shadow = self._header_match_cache
        shadow = self._shadow
        if cached_shadow == shadow:
            return cached_match
        m = HEADER_MATCH(shadow)
        self._header_match_cache = m, shadow
        return m

    @property
    def level(self) -> int:
        """The level of this section.

        getter: Return level which as an int in range(1,7) or 0 for the lead
            section.
        setter: Change the level.
        """
        m = self._header_match
        if m:
            return len(m[1])
        return 0

    @level.setter
    def level(self, value: int) -> None:
        m = self._header_match
        level_diff = len(m[1]) - value
        if level_diff == 0:
            return
        if level_diff < 0:
            new_equals = '=' * abs(level_diff)
            self.insert(0, new_equals)
            self.insert(m.end(2) + 1, new_equals)
            return
        del self[:level_diff]
        del self[m.end(2):m.end(2) + level_diff]

    @property
    def title(self) -> Optional[str]:
        """The title of this section.

         getter: Return the title or None for lead sections or sections that
            don't have any title.
         setter: Set a new title.
         deleter: Remove the title, including the equal sign and the newline
            after it.
         """
        m = self._header_match
        if m is None:
            return None
        return self(m.start(2), m.end(2))

    @title.setter
    def title(self, value: str) -> None:
        m = self._header_match
        if m is None:
            raise RuntimeError(
                "Can't set title for a lead section. "
                "Try adding it to contents.")
        self[m.start(2):m.end(2)] = value

    @title.deleter
    def title(self) -> None:
        m = self._header_match
        if m is None:
            return
        del self[m.start():m.end()]

    @property
    def contents(self) -> str:
        """Contents of this section.

        getter: return the contents
        setter: Set contents to a new string value.
        """
        m = self._header_match
        if m is None:
            return self(0, None)
        return self(m.end(), None)

    @contents.setter
    def contents(self, value: str) -> None:
        m = self._header_match
        if m is None:
            self[:] = value
            return
        self[m.end():] = value
