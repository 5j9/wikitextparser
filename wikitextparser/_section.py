"""Define the Section class."""


from regex import compile as regex_compile, MULTILINE

from ._wikitext import WS, SubWikiText


HEADER_MATCH = regex_compile(rb'(={1,6})[^\n]+?\1[ \t]*$', MULTILINE).match


class Section(SubWikiText):

    """Section class is used to represent page sections."""

    @property
    def level(self) -> int:
        """Return level of this section.

        Level is in range(1,7) or 0 for the lead section.
        """
        m = HEADER_MATCH(self._shadow)
        if m:
            return len(m[1])
        return 0

    @level.setter
    def level(self, value: int) -> None:
        """Change level of this section."""
        old_level = self.level
        title = self.title
        new_equals = '=' * value
        self[0:old_level + len(title) + old_level] =\
            new_equals + title + new_equals

    @property
    def title(self) -> str:
        """Return title of this section. Return '' for lead sections."""
        level = self.level
        if level == 0:
            return ''
        lf = self._shadow.find(10)
        if lf == -1:
            return self[:].rstrip(WS)[level:-level]
        return self[:lf].rstrip(WS)[level:-level]

    @title.setter
    def title(self, value: str) -> None:
        """Set the new title for this section and update self.lststr."""
        level = self.level
        if level == 0:
            raise RuntimeError(
                "Can't set title for a lead section. "
                "Try adding it to contents.")
        title = self.title
        self[level:level + len(title)] = value

    @property
    def contents(self) -> str:
        """Return contents of this section."""
        if self.level == 0:
            return self[:]
        lf = self._shadow.find(10)
        if lf == -1:
            return ''
        return self[lf + 1:]

    @contents.setter
    def contents(self, value: str) -> None:
        """Set value as the contents of this section."""
        level = self.level
        if level == 0:
            self[:] = value
            return
        start = level + len(self.title) + level + 1
        self[start:start + len(self.contents)] = value
