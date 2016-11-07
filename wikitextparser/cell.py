"""Define the Cell class."""


import regex

from .wikitext import SubWikiText
from .tag import ATTR


ATTR_REGEX = regex.compile(ATTR, flags=regex.DOTALL | regex.VERBOSE)


class Cell(SubWikiText):

    """Create a new Cell object."""

    def __init__(
        self,
        string: str or list,
        type_to_spans: list or None=None,
        index: int or None=None,
        type_: str or None=None,
        match=None,
        attrs: dict or None=None,
    ) -> None:
        """Initialize the object."""
        self._common_init(string, type_to_spans)
        if type_ is None:
            self._type = 'cells'
        else:
            self._type = type_
        if type_to_spans is None:
            self._type_to_spans[self._type] = [(0, len(string))]
        if index is None:
            self._index = len(self._type_to_spans['cells']) - 1
        else:
            self._index = index
        self._cached_string = (
            string if isinstance(string, str) else self.string
        )
        self._cached_match = match
        self._cached_attrs = attrs if attrs is not None else (
            ATTR_REGEX.fullmatch(match.group('attrs')) if match else None
        )

    def __repr__(self) -> str:
        """Return the string representation of self."""
        return 'Cell(' + repr(self.string) + ')'

    @property
    def _span(self) -> tuple:
        """Return self-span."""
        return self._type_to_spans[self._type][self._index]

    @property
    def value(self) -> str:
        """Return cell's value."""
        match = self._match
        return match.group('data')

    @value.setter
    def value(self, new_value: str) -> None:
        """Assign new_value to self."""
        raise NotImplementedError

    @property
    def _match(self):
        """Return the match object for the current tag. Cache the result."""
        string = self.string
        if self._cached_match and self._cached_string == string:
            return self._cached_match
        # Todo: Compute self._cached_match and self._cached_string.
        ...

    @property
    def attrs(self) -> dict:
        """Return the attributes of self as a dict."""
        string = self.string
        if self._cached_attrs is not None and string == self._cached_string:
            return self._cached_attrs
        match = self._match
        match = ATTR_REGEX.fullmatch(match.group('attrs'))
        self._cached_string = string
        attrs = dict(zip(
            match.captures('attr_name'), match.captures('attr_value')
        ))
        self._cached_attrs = attrs
        return attrs

    def get(self, attr_name: str) -> str:
        """Return the value of the last attribute with the given name.

        Return None if the attr_name does not exist in self.
        If there are already multiple attributes with the given name, only
            return the value of the last one.
        Return an empty string if the mentioned name is an empty attribute.

        """
        return self.attrs[attr_name]

    def has(self, attr_name: str) -> bool:
        """Return True if self contains an attribute with the given name."""
        return attr_name in self.attrs

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
