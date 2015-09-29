"""The Parameter class."""


class Parameter():

    """Create a new {{{parameters}}} object."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans)
        if index is None:
            self._index = len(self._spans['p']) -1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the Parameter."""
        return 'Parameter(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['p'][self._index]

    @property
    def name(self):
        """Return current parameter's name."""
        return self.string[3:-3].partition('|')[0]

    @name.setter
    def name(self, newname):
        """Set the new name."""
        name, pipe, default = self.string[3:-3].partition('|')
        self.strins(3, newname)
        self.strdel(3 + len(newname), 3 + len(newname + name))

    @property
    def pipe(self):
        """Return `|` if there is a pipe (default value) in the Parameter.

         Return '' otherwise.
         """
        return self.string[3:-3].partition('|')[1]

    @property
    def default(self):
        """Return value of a keyword argument."""
        string = self.string[3:-3]
        if '|' in string:
            return string.partition('|')[2]

    @default.setter
    def default(self, newdefault):
        """Set the new value. If a default exist, change it. Add ow."""
        olddefault = self.default
        if olddefault is None:
            self.strins(len('{{{' + self.name), '|' + newdefault)
        else:
            name = self.name
            self.strins(len('{{{' + name), '|' + newdefault)
            self.strdel(
                len('{{{' + name + '|' + newdefault),
                len('{{{' + name + '|' + newdefault + '|' + olddefault)
            )
    def append_default(self, new_default_name):
        """Append a new default parameter in the appropriate place.

        Add the new default to the innter-most parameter.
        If the parameter already exists among defaults, don't change anything.

        Example:
            >>> p = Parameter('{{{p1|{{{p2|}}}}}}')
            >>> p.append_default('p3')
            >>> p
            Parameter("'{{{p1|{{{p2|{{{p3|}}}}}}}}}'")
        """
        stripped_default_name = new_default_name.strip()
        if stripped_default_name == self.name.strip():
            return
        dig = True
        innermost_param = self
        while dig:
            dig = False
            default = innermost_param.default
            for p in innermost_param.parameters:
                if p.string == default:
                    if stripped_default_name == p.name.strip():
                        return
                    innermost_param = p
                    dig = True
        innermost_default = innermost_param.default
        if innermost_default is None:
            innermost_param.strins(
                len(innermost_param.string) - 3,
                '|{{{' + new_default_name + '}}}'
            )
        else:
            name = innermost_param.name
            innermost_param.strins(
                len('{{{' + name + '|'),
                '{{{' + new_default_name + '|' + innermost_default + '}}}'
            )
            innermost_param.strdel(
                len(
                    '{{{' + name + '|{{{' + new_default_name +
                    '|' + innermost_default + '}}}'
                ),
                len(
                    '{{{' + name + '|{{{' + new_default_name +
                    '|' + innermost_default + '}}}' + innermost_default
                ),
            )
