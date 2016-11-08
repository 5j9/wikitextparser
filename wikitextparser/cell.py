"""Define the Cell class."""


import regex

from .wikitext import SubWikiText
from .tag import ATTR


# https://regex101.com/r/hB4dX2/17
NEWLINE_CELL_REGEX = regex.compile(
    r"""
    # only for matching, not searching
    \s*
    (?P<sep>[|!](?![+}-]))
    (?:
        # catch the matching pipe (style holder).
        \| # immediate closure (attrs='').
        |
        (?P<attrs>
            (?:
                [^|\n]
                (?!(?P=sep){2}) # attrs end with `|`; or `!!` if sep is `!`
            )*?
        )
        # attribute-data separator
        \|
        # not a cell separator (||)
        (?!\|)
    )?
    # optional := the 1st sep is a single ! or |.
    (?P<data>[\s\S]*?)
    (?=
        # start of the next cell
        \n\s*[!|]|
        \|\||
        (?P=sep){2}|
        $
    )
    """,
    regex.VERBOSE
)
# https://regex101.com/r/qK1pJ8/5
INLINE_HAEDER_CELL_REGEX = regex.compile(
    r"""
    [|!]{2}
    (?:
        # catch the matching pipe (style holder).
        \| # immediate closure (attrs='').
        |
        (?P<attrs>
            (?:
                [^|\n]
                # inline header attrs end with `|` (above) or `!!` (below)
                (?!!!)
            )*
        )
        (?:
            # attribute-data separator
            \|
            # make sure that it's not a cell separator (||)
            (?!\|)
            |
            # the other attribute-data separator
            !(?!!)
        )
    )?
    # optional := the 1st sep is a single ! or |.
    (?P<data>[\s\S]*?)
    (?=
        # start of the next cell
        \n\s*[!|]|
        \|\||
        !!|
        $
    )
    """,
    regex.VERBOSE
)
# https://regex101.com/r/hW8aZ3/7
INLINE_NONHAEDER_CELL_REGEX = regex.compile(
    r"""
    \|\| # catch the matching pipe (style holder).
    (?:
        # immediate closure (attrs='').
        \|
        # not cell a separator (||)
        (?!\|)
        |
        (?P<attrs>
            [^|\n]*? # non-header attrs end with a `|`
        )
        # attribute-data separator
        \|
        # not cell a separator (||)
        (?!\|)
    )
    # optional := the 1st sep is a single ! or |.
    ?
    (?P<data>[\s\S]*?)
    # start of the next cell
    (?=
        \|\||
        $|
        \n\s*[!|]
    )
    """,
    regex.VERBOSE
)
# https://regex101.com/r/tH3pU3/6
ATTR_REGEX = regex.compile(ATTR, flags=regex.DOTALL | regex.VERBOSE)


class Cell(SubWikiText):

    """Create a new Cell object."""

    def __init__(
        self,
        string: str or list,
        header: bool=False,
        type_to_spans: list or None=None,
        index: int or None=None,
        type_: str or None=None,
        match=None,
        attrs: dict or None=None,
    ) -> None:
        """Initialize the object."""
        self._common_init(string, type_to_spans)
        self._type = 'cells' if type_ is None else type_
        if type_to_spans is None:
            self._type_to_spans[self._type] = [(0, len(string))]
        self._index = len(
            self._type_to_spans['cells']
        ) - 1 if index is None else index
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
    def _match(self):
        """Return the match object for the current tag. Cache the result."""
        string = self.string
        if self._cached_match and self._cached_string == string:
            return self._cached_match
        if string.startswith('\n'):
            m = NEWLINE_CELL_REGEX.match(string)
            self.header = m.group('sep') == '!'
            return m
        elif self.header:
            m = INLINE_HAEDER_CELL_REGEX.match(string)
        else:
            m = INLINE_NONHAEDER_CELL_REGEX.match(string)
        self._cached_match = m
        self._cached_string = string
        return m

    @property
    def value(self) -> str:
        """Return cell's value."""
        return self._match.group('data')

    @value.setter
    def value(self, new_value: str) -> None:
        """Assign new_value to self."""
        raise NotImplementedError

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
