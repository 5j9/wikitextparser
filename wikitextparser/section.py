"""The Section class."""


import re


SECTION_LEVEL_TITLE = re.compile(r'^(={1,6})([^\n]+?)\1( *(?:\n|$))')


class Section():

    """Create a new Section object."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans)
        if spans is None:
            self._spans['sections'] = [(0, len(string))]
        if index is None:
            self._index = len(self._spans['sections']) - 1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'Section(' + repr(self.string) + ')'

    def _get_span(self):
        """Return selfspan (span of self.string in self._lststr[0])."""
        return self._spans['sections'][self._index]

    @property
    def level(self):
        """Return level of this section. Level is in range(1,7)."""
        selfstring = self.string
        m = SECTION_LEVEL_TITLE.match(selfstring)
        if not m:
            return 0
        return len(m.group(1))

    @level.setter
    def level(self, newlevel):
        """Change leader level of this sectoin."""
        level = self.level
        title = self.title
        equals = '=' * newlevel
        self.strins(0, equals)
        self.strdel(newlevel, newlevel + level)
        self.strins(len(equals + title), equals)
        self.strdel(
            len(equals + title + equals),
            len(equals + title + equals) + level,
        )

    @property
    def title(self):
        """Return title of this section. Return '' for lead sections."""
        level = self.level
        if level == 0:
            return ''
        return self.string.partition('\n')[0].rstrip()[level:-level]

    @title.setter
    def title(self, newtitle):
        """Set the new title for this section and update self.lststr."""
        level = self.level
        if level == 0:
            raise RuntimeError(
                "Can't set title for a lead section. "
                "Try adding it to the contents."
            )
        title = self.title
        self.strins(level, newtitle)
        self.strdel(level + len(newtitle), level + len(newtitle + title))

    @property
    def contents(self):
        """Return contents of this section."""
        if self.level == 0:
            return self.string
        return self.string.partition('\n')[2]

    @contents.setter
    def contents(self, newcontents):
        """Set newcontents as the contents of this section."""
        level = self.level
        contents = self.contents
        if level == 0:
            self.strins(0, newcontents)
            self.strdel(len(newcontents), len(newcontents + contents))
        else:
            title = self.title
            self.strins(level + len(title) + level + 1, newcontents)
            self.strdel(
                level + len(title) + level + len('\n' + newcontents),
                level + len(title) + level + len('\n' + newcontents + contents)
            )
