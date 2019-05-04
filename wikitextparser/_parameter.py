"""Define the Parameter class."""


from typing import Optional
from warnings import warn

from ._wikitext import SubWikiText, WS


class Parameter(SubWikiText):

    """Create a new {{{parameters}}} object."""

    @property
    def name(self) -> str:
        """Return current parameter's name."""
        pipe = self._shadow.find(124)
        if pipe == -1:
            return self[3:-3]
        return self[3:pipe]

    @name.setter
    def name(self, newname: str) -> None:
        """Set the new name."""
        self[3:3 + len(self.name)] = newname

    @property
    def pipe(self) -> str:
        """Return `|` if there is a pipe (default value) in the Parameter.

        Return '' otherwise.
        """
        return '|' if self._shadow.find(124) != -1 else ''

    @property
    def default(self) -> Optional[str]:
        """Return the default value. Return None if there is no default."""
        pipe = self._shadow.find(124)
        if pipe == -1:
            return None
        return self[pipe + 1:-3]

    @default.setter
    def default(self, newdefault: str) -> None:
        """Set a new default value."""
        if newdefault is None:
            warn('Setting Argument.default to None is deprecated. '
                 'Use `del Argument.default` instead.', DeprecationWarning)
            del self.default
            return
        pipe = self._shadow.find(124)
        if pipe == -1:
            self.insert(-3, '|' + newdefault)
            return
        self[pipe + 1:-3] = newdefault

    @default.deleter
    def default(self) -> None:
        pipe = self._shadow.find(124)
        if pipe == -1:
            return
        del self[pipe:-3]

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
        stripped_default_name = new_default_name.strip(WS)
        if stripped_default_name == self.name.strip(WS):
            return
        dig = True
        innermost_param = self
        while dig:
            dig = False
            default = innermost_param.default
            for p in innermost_param.parameters:
                if p.string == default:
                    if stripped_default_name == p.name.strip(WS):
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
