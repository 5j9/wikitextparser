"""Define the Parameter class."""


from .wikitext import SubWikiText


class Parameter(SubWikiText):

    """Create a new {{{parameters}}} object."""

    _type = 'Parameter'

    def __init__(
        self,
        string: str or list,
        type_to_spans: list or None = None,
        index: int or None = None,
    ) -> None:
        """Initialize the object."""
        self._common_init(string, type_to_spans)
        self._index = len(
            self._type_to_spans['Parameter']
        ) - 1 if index is None else index

    @property
    def name(self) -> str:
        """Return current parameter's name."""
        return self.string[3:-3].partition('|')[0]

    @name.setter
    def name(self, newname) -> None:
        """Set the new name."""
        name, pipe, default = self.string[3:-3].partition('|')
        self[3:3 + len(name)] = newname

    @property
    def pipe(self) -> str:
        """Return `|` if there is a pipe (default value) in the Parameter.

         Return '' otherwise.
         """
        return self.string[3:-3].partition('|')[1]

    @property
    def default(self) -> str or None:
        """Return the default value."""
        # Todo: Ignore the pipes inside comments.
        string = self.string[3:-3]
        if '|' in string:
            return string.partition('|')[2]

    @default.setter
    def default(self, newdefault: str) -> None:
        """Set the new value. If a default exist, change it. Add ow."""
        olddefault = self.default
        if olddefault is None:
            self.insert(len('{{{' + self.name), '|' + newdefault)
        else:
            name = self.name
            self[len('{{{' + name):len('{{{' + name + '|' + olddefault)] =\
                '|' + newdefault

    def append_default(self, new_default_name: str) -> None:
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
            innermost_param.insert(-3, '|{{{' + new_default_name + '}}}')
        else:
            name = innermost_param.name
            innermost_param[
                len('{{{' + name + '|'):
                len('{{{' + name + '|' + innermost_default)
            ] = '{{{' + new_default_name + '|' + innermost_default + '}}}'
