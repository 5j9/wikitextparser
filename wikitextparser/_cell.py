"""Define the Cell class."""


from typing import Match, MutableSequence, Union, Dict, List

from regex import compile as regex_compile, VERBOSE, DOTALL

from ._tag import ATTRS_MATCH, SubWikiTextWithAttrs


# https://regex101.com/r/hB4dX2/17
NEWLINE_CELL_MATCH = regex_compile(
    rb"""
    # only for matching, not search
    \s*+
    (?P<sep>[|!](?![+}-]))
    (?>
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
            )*  # Todo: why can't be made possessive?
        )
        # attribute-data separator
        \|
        (?!
            # not a cell separator (||)
            \||
            # start of a new cell
            \!\!
        )
    )?+
    # optional := the 1st sep is a single ! or |.
    (?P<data>[\s\S]*?)
    (?=
        # start of the next inline-cell
        \|\||
        (?P=sep){2}|
        \|!!|
        # start of the next newline-cell
        \n\s*+[!|]|
        # end of cell-string
        $
    )
    """,
    VERBOSE
).match
# https://regex101.com/r/qK1pJ8/5
# In header rows, any "!!" is treated as "||".
# See: https://github.com/wikimedia/mediawiki/blob/
# 558a6b7372ee3b729265b7e540c0a92c1d936bcb/includes/parser/Parser.php#L1123
INLINE_HAEDER_CELL_MATCH = regex_compile(
    rb"""
    (?>
        # immediate closure of attrs
        \|!(?P<attrs>)!
        |
        # attrs start is with a double ! or |
        (?>!{2}|\|{2})
        # find the matching pipe that ends attrs
        (?>
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
                )*+
            )
            # attrs-data separator
            \|
            # make sure that it's not a cell separator (||)
            (?!\|)
        )?+
    )
    # optional := the 1st sep is a single ! or |.
    (?P<data>.*?)
    (?=
        # start of the next newline-cell
        \n\s*+[!|]|
        # start of the next inline-cell
        \|\||
        !!|
        \|!!|
        # end of cell-string
        $
    )
    """,
    VERBOSE | DOTALL
).match
# https://regex101.com/r/hW8aZ3/7
INLINE_NONHAEDER_CELL_MATCH = regex_compile(
    rb"""
    \|\| # catch the matching pipe (style holder).
    (?>
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
    ?+
    (?P<data>
        [^|]*?
        (?=
            \|\|| # start of the next inline-cell
            \n\s*+[!|]| # start of the next newline-cell
            $ # end of cell-string
        )
    )
    """,
    VERBOSE
).match


class Cell(SubWikiTextWithAttrs):

    """Create a new Cell object."""

    def __init__(
        self,
        string: Union[str, MutableSequence[str]],
        header: bool = False,
        _type_to_spans: Dict[str, List[List[int]]] = None,
        _span: int = None,
        _type: int = None,
        _match: Match = None,
        _attrs_match: Match = None,
    ) -> None:
        """Initialize the object."""
        super().__init__(string, _type_to_spans, _span, _type)
        self._header = header
        if _match:
            string = self.string
            self._match_cache = _match, string
            if _attrs_match:
                self._attrs_match_cache = _attrs_match, string
            else:
                self._attrs_match_cache = \
                    ATTRS_MATCH(_match['attrs']), string
        else:
            self._attrs_match_cache = self._match_cache = None, None

    @property
    def _match(self):
        """Return the match object for the current tag. Cache the result.

        Be extra careful when using this property. The position of match
        may be something other than zero if the match is cached from the
        parent object (the initial value).
        """
        cache_match, cache_string = self._match_cache
        string = self.string
        if cache_string == string:
            return cache_match
        shadow = self._shadow
        if shadow[0] == 10:  # ord('\n')
            m = NEWLINE_CELL_MATCH(shadow)
            self._header = m['sep'] == 33  # ord('!')
        elif self._header:
            m = INLINE_HAEDER_CELL_MATCH(shadow)
        else:
            m = INLINE_NONHAEDER_CELL_MATCH(shadow)
        self._match_cache = m, string
        self._attrs_match_cache = None, None
        return m

    @property
    def value(self) -> str:
        """Return cell's value."""
        m = self._match
        offset = m.start()
        s, e = m.span('data')
        return self[s - offset:e - offset]

    @value.setter
    def value(self, new_value: str) -> None:
        """Assign new_value to self."""
        m = self._match
        offset = m.start()
        s, e = m.span('data')
        self[s - offset:e - offset] = new_value

    @property
    def _attrs_match(self):
        """Return the match object for attributes."""
        cache, cache_string = self._attrs_match_cache
        string = self.string
        if cache_string == string:
            return cache
        s, e = self._match.span('attrs')
        attrs_match = ATTRS_MATCH(self._shadow, s, e)
        self._attrs_match_cache = attrs_match, string
        return attrs_match

    def set_attr(self, attr_name: str, attr_value: str) -> None:
        """Set the value for the given attribute name.

        If there are already multiple attributes with that name, only
        set the value for the last one.
        If attr_value == '', use the implicit empty attribute syntax.
        """
        # Note: The set_attr method of the parent class cannot be used instead
        # of this method because a cell could be without any attrs placeholder
        # which means the appropriate piping should be added around attrs by
        # this method. Also ATTRS_MATCH does not have any 'start' group.
        cell_match = self._match
        shadow = cell_match.string
        attrs_start, attrs_end = cell_match.span('attrs')
        if attrs_start != -1:
            encoded_attr_name = attr_name.encode()
            attrs_m = ATTRS_MATCH(shadow, attrs_start, attrs_end)
            for i, n in enumerate(reversed(attrs_m.captures('attr_name'))):
                if n == encoded_attr_name:
                    vs, ve = attrs_m.spans('attr_value')[-i - 1]
                    q = 1 if attrs_m.string[ve] in b'"\'' else 0
                    self[vs - q:ve + q] = '"{}"'.format(attr_value)
                    return
            # We have some attributes, but none of them is attr_name
            attr_end = cell_match.end('attrs')
            fmt = '{}="{}" ' if shadow[attr_end - 1] == 32 else ' {}="{}"'
            self.insert(attr_end, fmt.format(attr_name, attr_value))
            return
        # There is no attributes span in this cell. Create one.
        fmt = ' {}="{}" |' if attr_value else ' {} |'
        if shadow[0] == 10:  # ord('\n')
            self.insert(
                cell_match.start('sep') + 1,
                fmt.format(attr_name, attr_value)
            )
            return
        # An inline cell
        self.insert(2, fmt.format(attr_name, attr_value))
        return
