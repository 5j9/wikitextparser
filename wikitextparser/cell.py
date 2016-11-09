"""Define the Cell class."""


import regex

from .wikitext import SubWikiText
from .tag import ATTRS_REGEX


# https://regex101.com/r/hB4dX2/17
NEWLINE_CELL_REGEX = regex.compile(
    r"""
    # only for matching, not searching
    \s*
    (?P<sep>[|!](?![+}-]))
    (?:
        # catch the matching pipe (attrs limiter)
        # immediate closure (attrs='')
        \|
        # not a cell separator (||)
        (?!\|)
        |
        (?P<attrs>
            (?:
                [^\n]
                (?!
                    # attrs end with `|`; or `!!` if sep is `!`
                    (?P=sep){2}|\|\|
                )
            )*
        )
        # attribute-data separator
        \|
        (?!
            # not a cell separator (||)
            \||
            # start of a new cell
            \!\!
        )
    )?
    # optional := the 1st sep is a single ! or |.
    (?P<data>[\s\S]*?)
    (?=
        # start of the next inline-cell
        \|\||
        (?P=sep){2}|
        \|!!|
        # start of the next newline-cell
        \n\s*[!|]|
        # end of cell-string
        $
    )
    """,
    regex.VERBOSE
)
# https://regex101.com/r/qK1pJ8/5
# In header rows, any "!!" is treated as "||".
# See: https://github.com/wikimedia/mediawiki/blob/
# 558a6b7372ee3b729265b7e540c0a92c1d936bcb/includes/parser/Parser.php#L1123
INLINE_HAEDER_CELL_REGEX = regex.compile(
    r"""
    (?>
        \|!! # immediate closure
        |
        (?>!{2}|\|{2})
        (?:
            # catch the matching pipe (style holder).
            \| # immediate closure
            # not a cell separator (||)
            (?!\|)
            |
            (?P<attrs>
                (?:
                    # inline header attrs end with `|` (above) or `!!` (below)
                    (?!!{2})
                    [^|\n]
                )*
            )
            (?:
                # attribute-data separator
                \|
                # make sure that it's not a cell separator (||)
                (?!\|)
            )
        )?
    )
    # optional := the 1st sep is a single ! or |.
    (?P<data>.*?)
    (?=
        # start of the next newline-cell
        \n\s*[!|]|
        # start of the next inline-cell
        \|\||
        !!|
        \|!!|
        # end of cell-string
        $
    )
    """,
    regex.VERBOSE | regex.DOTALL
)
# https://regex101.com/r/hW8aZ3/7
INLINE_NONHAEDER_CELL_REGEX = regex.compile(
    r"""
    \|\| # catch the matching pipe (style holder).
    (?:
        # immediate closure (attrs='').
        \|
        # not a cell separator (||)
        (?!\|)
        |
        (?P<attrs>
            [^|\n]*? # non-_header attrs end with a `|`
        )
        # attribute-data separator
        \|
        # not cell a separator (||)
        (?!\|)
    )
    # optional := the 1st sep is a single ! or |.
    ?
    (?P<data>
        [^|]*?
        (?=
            \|\|| # start of the next inline-cell
            \n\s*[!|]| # start of the next newline-cell
            $ # end of cell-string
        )
    )
    """,
    regex.VERBOSE
)


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
        self._header = header
        self._cached_match = match
        self._cached_attrs = attrs if attrs is not None else (
            ATTRS_REGEX.match(match.group('attrs')) if match else None
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
            self._header = m.group('sep') == '!'
        elif self._header:
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
        s, e = self._match.span('data')
        self[s:e] = new_value

    @property
    def attrs(self) -> dict:
        """Return the attributes of self as a dict."""
        string = self.string
        if self._cached_attrs is not None and string == self._cached_string:
            return self._cached_attrs
        attrs_group = self._match.group('attrs')
        if attrs_group:
            m = ATTRS_REGEX.match(attrs_group)
            attrs = dict(zip(
                m.captures('attr_name'), m.captures('attr_value')
            ))
        else:
            attrs = {}
        self._cached_string = string
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
        set the value for the last one.
        If attr_value == '', use the implicit empty attribute syntax.

        """
        cell_match = self._match
        string = cell_match.string
        attrs_start, attrs_end = cell_match.span('attrs')
        if attrs_start != -1:
            attrs_m = ATTRS_REGEX.match(string, attrs_start, attrs_end)
            for i, n in enumerate(reversed(attrs_m.captures('attr_name'))):
                if n == attr_name:
                    vs, ve = attrs_m.spans('attr_value')[-i - 1]
                    q = 1 if attrs_m.string[ve] in '"\'' else 0
                    self[vs - q:ve + q] = '"{}"'.format(
                        attr_value.replace('"', '&quot;')
                    )
                    return
            # We have some attributes, but none of them is attr_name
            attr_end = cell_match.end('attrs')
            fmt = '{}="{}" ' if string[attr_end - 1] == ' ' else ' {}="{}"'
            self.insert(
                attr_end,
                fmt.format(attr_name, attr_value.replace('"', '&#39;')),
            )
            return
        # There is no attributes span in this cell. Create one.
        fmt = ' {}="{}" |' if attr_value else ' {} |'
        string = cell_match.string
        if string.startswith('\n'):
            self.insert(
                cell_match.start('sep') + 1,
                fmt.format(attr_name, attr_value.replace('"', '&quot;'))
            )
            return
        # An inline cell
        self.insert(
            2, fmt.format(attr_name, attr_value.replace('"', '&quot;'))
        )
        return

    def delete(self, attr_name: str) -> None:
        """Delete all the attributes with the given name.

        Pass if the attr_name is not found in self.

        """
        if attr_name not in self.attrs:
            return
        cell_match = self._match
        string = cell_match.string
        attrs_start, attrs_end = cell_match.span('attrs')
        attrs_m = ATTRS_REGEX.match(string, attrs_start, attrs_end)
        # Must be done in reversed order because the spans
        # change after each deletion.
        for i, capture in enumerate(reversed(attrs_m.captures('attr_name'))):
            if capture == attr_name:
                start, stop = attrs_m.spans('attr')[-i - 1]
                del self[start:stop]
