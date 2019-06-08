"""Define the Section class."""


from regex import compile as regex_compile, MULTILINE

from ._wikitext import WS, SubWikiText


HEADER_MATCH = regex_compile(rb'(={1,6})[^\n]+?\1[ \t]*(\n|\Z)').match


class Section(SubWikiText):

    """Section class is used to represent page sections."""

    _header_match_cache = (None, None)

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
        old_level = self.level
        title = self.title
        new_equals = '=' * value
        self[0:old_level + len(title) + old_level] =\
            new_equals + title + new_equals

    @property
    def title(self) -> str:
        """The title of this section.

         getter: Return the title, '' for lead sections.
         setter: Set a new title.
         """
        level = self.level
        if level == 0:
            return ''
        lf = self._shadow.find(10)
        if lf == -1:
            return self(0, None).rstrip(WS)[level:-level]
        return self(0, lf).rstrip(WS)[level:-level]

    @title.setter
    def title(self, value: str) -> None:
        level = self.level
        if level == 0:
            raise RuntimeError(
                "Can't set title for a lead section. "
                "Try adding it to contents.")
        title = self.title
        self[level:level + len(title)] = value

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
