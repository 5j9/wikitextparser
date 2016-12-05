"""Define the Parameter class."""


from .wikitext import SubWikiText


class Parameter(SubWikiText):

    """Create a new {{{parameters}}} object."""

    @property
    def name(self) -> str:
        """Return current parameter's name."""
        name, pipe, default = self._not_in_atomic_subspans_partition('|')
        if pipe:
            return name[3:]
        return name[3:-3]

    @name.setter
    def name(self, newname: str) -> None:
        """Set the new name."""
        self[3:3 + len(self.name)] = newname

    @property
    def pipe(self) -> str:
        """Return `|` if there is a pipe (default value) in the Parameter.

         Return '' otherwise.

         """
        return self._not_in_atomic_subspans_partition('|')[1]

    @property
    def default(self) -> str or None:
        """Return the default value. Return None if there is no default."""
        name, pipe, default = self._not_in_atomic_subspans_partition('|')
        if pipe:
            return default[:-3]

    @default.setter
    def default(self, newdefault: str or None) -> None:
        """Set a new default value. Use None to remove default."""
        name, pipe, default = self._not_in_atomic_subspans_partition('|')
        if not pipe:
            # olddefault is None
            if newdefault is None:
                return
            self.insert(-3, '|' + newdefault)
            return
        if newdefault is None:
            # Only newdefault is None
            del self[len(name):-3]
            return
        # olddefault is not None and newdefault is not None
        self[len(name):-3] = '|' + newdefault

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
