"""Define the Cell class."""


from typing import Match, MutableSequence, Union, Dict, List, Tuple

import regex

from .tag import ATTRS_REGEX, SubWikiTextWithAttrs


# https://regex101.com/r/hB4dX2/17
NEWLINE_CELL_REGEX = regex.compile(
    r"""
    # only for matching, not searching
    \s*
    (?P<sep>[|!](?![+}-]))
    (?:
        # catch the matching pipe (attrs limiter)
        # immediate closure
        (?P<attrs>)
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
        \|!(?P<attrs>)! # immediate closure
        |
        (?>!{2}|\|{2})
        (?:
            # catch the matching pipe (style holder).
            # immediate closure
            (?P<attrs>)
            \|
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
        # immediate closure
        (?P<attrs>)
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


class Cell(SubWikiTextWithAttrs):

    """Create a new Cell object."""

    def __init__(
        self,
        string: Union[str, MutableSequence[str]],
        header: bool=False,
        _type_to_spans: Dict[str, List[Tuple[int, int]]]=None,
        _index: int=None,
        _type: str=None,
        _match: Match=None,
        _attrs_match: Match=None,
    ) -> None:
        """Initialize the object."""
        super().__init__(string, _type_to_spans, _index, _type)
        self._header = header
        self._cached_match = _match
        self._cached_string = self.string if _match else None
        self._cached_attrs_match = (
            _attrs_match if _attrs_match is not None else
            ATTRS_REGEX.match(_match.group('attrs')) if _match else None
        )

    @property
    def _match(self):
        """Return the match object for the current tag. Cache the result.

        Be extra careful when using this property. The position of match
        may be something other than zero if the match is cached from the
        parent object (the initial value).

        """
        cached_string = self._cached_string
        cached_match = self._cached_match
        string = self.string
        if cached_match and cached_string == string:
            return self._cached_match
        shadow = self._shadow
        if shadow.startswith('\n'):
            m = NEWLINE_CELL_REGEX.match(shadow)
            self._header = m.group('sep') == '!'
        elif self._header:
            m = INLINE_HAEDER_CELL_REGEX.match(shadow)
        else:
            m = INLINE_NONHAEDER_CELL_REGEX.match(shadow)
        self._cached_match = m
        self._cached_string = string
        self._cached_attrs_match = None
        return m

    @property
    def value(self) -> str:
        """Return cell's value."""
        m = self._match
        pos = m.start()
        s, e = m.span('data')
        return self[s - pos:e - pos]

    @value.setter
    def value(self, new_value: str) -> None:
        """Assign new_value to self."""
        match = self._match
        s, e = match.span('data')
        pos = match.start()
        if pos:
            self[s - pos:e - pos] = new_value
        else:
            self[s:e] = new_value

    @property
    def _attrs_match(self):
        """Return the match object for attributes."""
        string = self.string
        cache = self._cached_attrs_match
        if cache is not None and self._cached_string == string:
            return cache
        s, e = self._match.span('attrs')
        attrs_match = ATTRS_REGEX.match(string, s, e)
        self._cached_attrs_match = attrs_match
        return attrs_match

    def set(self, attr_name: str, attr_value: str) -> None:
        """Set the value for the given attribute name.

        If there are already multiple attributes with that name, only
        set the value for the last one.
        If attr_value == '', use the implicit empty attribute syntax.

        """
        cell_match = self._match
        pos = cell_match.start()
        shadow = cell_match.string
        attrs_start, attrs_end = cell_match.span('attrs')
        if attrs_start != -1:
            attrs_m = ATTRS_REGEX.match(shadow, attrs_start, attrs_end)
            for i, n in enumerate(reversed(attrs_m.captures('attr_name'))):
                if n == attr_name:
                    vs, ve = attrs_m.spans('attr_value')[-i - 1]
                    q = 1 if attrs_m.string[ve] in '"\'' else 0
                    self[vs - q - pos:ve + q - pos] = '"{}"'.format(
                        attr_value.replace('"', '&quot;')
                    )
                    return
            # We have some attributes, but none of them is attr_name
            attr_end = cell_match.end('attrs') - pos
            fmt = '{}="{}" ' if shadow[attr_end - 1] == ' ' else ' {}="{}"'
            self.insert(
                attr_end,
                fmt.format(attr_name, attr_value.replace('"', '&#39;')),
            )
            return
        # There is no attributes span in this cell. Create one.
        fmt = ' {}="{}" |' if attr_value else ' {} |'
        if shadow.startswith('\n'):
            self.insert(
                cell_match.start('sep') + 1 - pos,
                fmt.format(attr_name, attr_value.replace('"', '&quot;'))
            )
            return
        # An inline cell
        self.insert(
            2, fmt.format(attr_name, attr_value.replace('"', '&quot;'))
        )
        return
