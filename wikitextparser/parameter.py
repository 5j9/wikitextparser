"""Define the Parameter class."""


from typing import Optional

from .wikitext import SubWikiText


class Parameter(SubWikiText):

    """Create a new {{{parameters}}} object."""

    @property
    def name(self) -> str:
        """Return current parameter's name."""
        name, pipe, default = self._atomic_partition(b'|')
        if pipe:
            return name[3:].decode()
        return name[3:-3].decode()

    @name.setter
    def name(self, newname: str) -> None:
        """Set the new name."""
        braces_name, pipe, default_braces = self._atomic_partition(b'|')
        if not pipe:
            braces_name = braces_name[:-3]
        self[3:len(braces_name)] = newname.encode()

    @property
    def pipe(self) -> str:
        """Return `|` if there is a pipe (default value) in the Parameter.

         Return '' otherwise.

         """
        return self._atomic_partition(b'|')[1].decode()

    @property
    def default(self) -> Optional[str]:
        """Return the default value. Return None if there is no default."""
        name, pipe, default = self._atomic_partition(b'|')
        if pipe:
            return default[:-3].decode()

    @default.setter
    def default(self, newdefault: Optional[str]) -> None:
        """Set a new default value. Use None to remove default."""
        name, pipe, default = self._atomic_partition(b'|')
        if not pipe:
            # olddefault is None
            if newdefault is None:
                return
            self.insert(-3, b'|' + newdefault.encode())
            return
        if newdefault is None:
            # Only newdefault is None
            del self[len(name):-3]
            return
        # olddefault is not None and newdefault is not None
        self[len(name):-3] = b'|' + newdefault.encode()

    def append_default(self, new_default: str) -> None:
        """Append a new default parameter in the appropriate place.

        Add the new default to the innter-most parameter.
        If the parameter already exists among defaults, don't change anything.

        Example:
            >>> p = Parameter('{{{p1|{{{p2|}}}}}}')
            >>> p.append_default('p3')
            >>> p
            Parameter("'{{{p1|{{{p2|{{{p3|}}}}}}}}}'")
        """
        stripped_default_name = new_default.strip()
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
        braces_name, pipe, inndermost_default_braces = \
            innermost_param._atomic_partition(b'|')
        if not pipe:
            innermost_param.insert(
                -3, b'|{{{' + new_default.encode() + b'}}}'
            )
            return
        innermost_param[len(braces_name + pipe):-3] = \
            b'{{{' + new_default.encode() + b'|' + inndermost_default_braces
