﻿"""Define the Section class."""


import regex
from typing import Tuple, MutableSequence, Union, List, Dict

from .wikitext import WikiText


SECTION_LEVEL_TITLE = regex.compile(r'^(={1,6})([^\n]+?)\1( *(?:\n|$))')


class Section(WikiText):

    """Create a new Section object."""

    _type = 'Section'

    def __init__(
        self,
        string: Union[str, MutableSequence[str]],
        _type_to_spans: Dict[str, List[List[int]]]=None,
        _span: List[int]=None,
    ) -> None:
        """Initialize the Table object."""
        super().__init__(string, _type_to_spans)
        if _span:
            self._span = _span

    @property
    def level(self) -> int:
        """Return level of this section. Level is in range(1,7)."""
        selfstring = self.string
        m = SECTION_LEVEL_TITLE.match(selfstring)
        if not m:
            return 0
        return len(m[1])

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
            self[:len(contents)] = newcontents
        else:
            title = self.title
            start = level + len(title) + level + 1
            self[start:start + len(contents)] = newcontents
