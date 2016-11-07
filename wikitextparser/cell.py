"""Define the Cell class."""


import regex

from .wikitext import SubWikiText
from .tag import ATTR


ATTR_REGEX = regex.compile(ATTR, flags=regex.DOTALL | regex.VERBOSE)


class Cell(SubWikiText):

    """Create a new Cell object."""

    def __init__(
        self, string: str or list, spans: list or None=None,
        index: int or None=None, type_: str or None=None
    ) -> None:
        """Initialize the object."""
        self._common_init(string, spans)
        if type_ is None:
            self._type = 'cell'
        else:
            self._type = type_
        if spans is None:
            self._type_to_spans[self._type] = [(0, len(string))]
        if index is None:
            self._index = len(self._type_to_spans['cell']) - 1
        else:
            self._index = index

    def __repr__(self) -> str:
        """Return the string representation of self."""
        return 'Cell(' + repr(self.string) + ')'

    def _get_span(self) -> tuple:
        """Return self-span."""
        return self._type_to_spans[self._type][self._index]

    def _get_arrt_span(self) -> tuple:
        """Return the attribute span for self."""
        # Note that attribute span and value span share the same index.
        return self._type_to_spans[self._type + '_attr'][self._index]

    @property
    def value(self) -> str:
        """Return cell's value."""
        s, e = self._get_span()
        return self.string[s:e]

    @value.setter
    def value(self, new_value: str) -> None:
        """Assign new_value to self."""
        s, e = self._get_span()
        self.string[s:e] = new_value

    def get(self, attr_name: str) -> str:
        """Return the value of the last attribute with the given name.

        Return None if the attr_name does not exist in self.
        If there are already multiple attributes with the given name, only
            return the value of the last one.
        Return an empty string if the mentioned name is an empty attribute.

        """
        ATTR_REGEX.match()

    def has(self, attr_name: str) -> bool:
        """Return True if self contains an attribute with the given name."""
        ...

    def set(self, attr_name: str, attr_value: str) -> None:
        """Set the value for the given attribute name.

        If there are already multiple attributes with that name, only
        get the value for the last one.
        If attr_value == '', use the empty attribute syntax. According to the
        standard the value for such attributes is implicitly the empty string.

        """
        raise NotImplementedError

    def delete(self, attr_name: str) -> None:
        """Delete all the attributes with the given name.

        Pass if the attr_name is not found in self.

        """
        raise NotImplementedError
