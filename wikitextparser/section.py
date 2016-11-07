"""Define the Section class."""


import re

from .wikitext import WikiText


SECTION_LEVEL_TITLE = re.compile(r'^(={1,6})([^\n]+?)\1( *(?:\n|$))')


class Section(WikiText):

    """Create a new Section object."""

    def __init__(
        self,
        string: str or list,
        type_to_spans: list or None=None,
        index: int or None=None,
    ) -> None:
        """Initialize the object."""
        self._common_init(string, type_to_spans)
        if type_to_spans is None:
            self._type_to_spans['sections'] = [(0, len(string))]
        if index is None:
            self._index = len(self._type_to_spans['sections']) - 1
        else:
            self._index = index

    def __repr__(self) -> str:
        """Return the string representation of the Argument."""
        return 'Section(' + repr(self.string) + ')'

    def _get_span(self) -> tuple:
        """Return selfspan (span of self.string in self._lststr[0])."""
        return self._type_to_spans['sections'][self._index]

    @property
    def level(self) -> int:
        """Return level of this section. Level is in range(1,7)."""
        selfstring = self.string
        m = SECTION_LEVEL_TITLE.match(selfstring)
        if not m:
            return 0
        return len(m.group(1))

    @level.setter
    def level(self, newlevel: int) -> None:
        """Change level of this section."""
        old_level = self.level
        title = self.title
        new_equals = '=' * newlevel
        self[0:old_level + len(title) + old_level] =\
            new_equals + title + new_equals

    @property
    def title(self) -> str:
        """Return title of this section. Return '' for lead sections."""
        level = self.level
        if level == 0:
            return ''
        return self.string.partition('\n')[0].rstrip()[level:-level]

    @title.setter
    def title(self, newtitle: str) -> None:
        """Set the new title for this section and update self.lststr."""
        level = self.level
        if level == 0:
            raise RuntimeError(
                "Can't set title for a lead section. "
                "Try adding it to the contents."
            )
        title = self.title
        self[level:level + len(title)] = newtitle

    @property
    def contents(self) -> str:
        """Return contents of this section."""
        if self.level == 0:
            return self.string
        return self.string.partition('\n')[2]

    @contents.setter
    def contents(self, newcontents: str) -> None:
        """Set newcontents as the contents of this section."""
        level = self.level
        contents = self.contents
        if level == 0:
            self[0:len(contents)] = newcontents
        else:
            title = self.title
            start = level + len(title) + level + 1
            self[start:start + len(contents)] = newcontents
