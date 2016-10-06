"""Define the Tag class."""


import regex

from .wikitext import IndexedWikiText


regex.DEFAULT_VERSION = regex.VERSION1
# HTML elements all have names that only use alphanumeric ASCII characters
# https://www.w3.org/TR/html5/syntax.html#syntax-tag-name
TAG_NAME = r'(?P<name>[A-Za-z0-9]+)'
# https://www.w3.org/TR/html5/infrastructure.html#space-character
SPACE_CHARS = r' \t\n\u000C\r'
# http://stackoverflow.com/a/93029/2705757
# chrs = (chr(i) for i in range(sys.maxunicode))
# control_chars = ''.join(c for c in chrs if unicodedata.category(c) == 'Cc')
CONTROL_CHARACTERS = r'\x00-\x1f\x7f-\x9f'
# https://www.w3.org/TR/html5/syntax.html#syntax-attributes
ATTR_NAME = (
    r'(?P<attr_name>[^{SPACE_CHARS}{CONTROL_CHARACTERS}\u0000"\'>/=]+)'
).format(**locals())
WS_EQ_WS = r'[{SPACE_CHARS}]*=[{SPACE_CHARS}]*'.format(**locals())
UNQUOTED_ATTR_VAL = (
    r'(?P<uq_attr_val>[^{SPACE_CHARS}"\'=<>`]+)'
).format(**locals())
QUOTED_ATTR_VAL = r'(?P<quote>[\'"])(?P<q_attr_val>.+?)(?P=quote)'
# May include character references, but for now, ignore the fact that they
# cannot contain an ambiguous ampersand.
ATTR_VAL = (
    r'''
    (?:
        # If an empty attribute is to be followed by the optional
        # "/" character, then there must be a space character separating
        # the two. This rule is ignored here.
        (?P<empty_attr>)[{SPACE_CHARS}]*|
        {WS_EQ_WS}{UNQUOTED_ATTR_VAL}[{SPACE_CHARS}]*|
        {WS_EQ_WS}{QUOTED_ATTR_VAL}[{SPACE_CHARS}]*
    )
    '''
).format(**locals())
# Ignore ambiguous ampersand for the sake of simplicity.
ATTR = r'(?P<attr>{ATTR_NAME}{ATTR_VAL})'.format(**locals())
# VOID_ELEMENTS = (
#     'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'keygen',
#     'link', 'meta', 'param', 'source', 'track', 'wbr'
# )
# RAW_TEXT_ELEMENTS = ('script', 'style')
# ESCAPABLE_RAW_TEXT_ELEMENTS = ('textarea', 'title')
# Detecting foreign elements in MathML and SVG namespaces is not implemented
# yet. See
# https://developer.mozilla.org/en/docs/Web/SVG/Namespaces_Crash_Course
# for an overview.
START_TAG = (
    r'''
    (?P<start>
        <{TAG_NAME}(?:[{SPACE_CHARS}]+{ATTR})*
        [{SPACE_CHARS}]*
        (?:(?P<self_closing>/>)|>)
    )
    '''
).format(**locals())
START_TAG_REGEX = regex.compile(START_TAG, regex.VERBOSE)
END_OF_START_TAG = (
    r'(?P<end></(?P<end_name>(?P=name))[{SPACE_CHARS}]*>)'.format(**locals())
)
END_TAG = r'(?P<end></{TAG_NAME}[{SPACE_CHARS}]*>)'.format(**locals())
END_TAG_REGEX = regex.compile(END_TAG)
# Note that the following regex won't check for nested tags
TAG_REGEX = regex.compile(
    r'''
    (?P<start>
        <{TAG_NAME}(?:[{SPACE_CHARS}]+{ATTR})*
    )
    # After the attributes, or after the tag name if there are no attributes,
    # there may be one or more space characters. This is sometimes required but
    # ignored here.
    [{SPACE_CHARS}]*
    (?:
        (?P<self_closing>/>)|
        >(?P<contents>.*?){END_OF_START_TAG}|
        (?P<start_only>>)
    )
    '''.format(**locals()),
    flags=regex.DOTALL | regex.VERBOSE
)


class Tag(IndexedWikiText):

    """Create a new Tag object."""

    def __init__(self, string, spans=None, index=None, match=None):
        """Initialize the Tag object.

        Run self._common_init. Set self._spans['extlinks'] if spans is None.

        """
        self._common_init(string, spans)
        if spans is None:
            self._spans['tags'] = [(0, len(string))]
        if index is None:
            self._index = len(self._spans['tags']) - 1
        else:
            self._index = index
        self._cache = string
        self._match = match

    def __repr__(self):
        """Return the string representation of self."""
        return 'Tag(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the span of this object."""
        return self._spans['tags'][self._index]

    def _get_match(self):
        """Return the match object for the current tag. Cache the result."""
        string = self.string
        if not self._match or not self._cache == string:
            # Compute the match
            self._match = TAG_REGEX.fullmatch(string)
            self._cache = string
        return self._match

    @property
    def name(self) -> str:
        """Return tag name."""
        return self._get_match()['name']

    @name.setter
    def name(self, name) -> None:
        """Set a new tag name."""
        # The name in the end tag should be replaced first because the spans
        # of the match object change after each replacement.
        match = self._get_match()
        start, end = match.span('end_name')
        if start != -1:
            self.replace_slice(start, end, name)
        start, end = match.span('name')
        self.replace_slice(start, end, name)

    @property
    def contents(self) -> str:
        """Return tag contents."""
        return self._get_match()['contents']

    @contents.setter
    def contents(self, contents) -> None:
        """Set new contents.

        Note that if the tag is self-closing, then it will be expanded to
        have a start tag and an end tag. For example:
        >>> t = Tag('<t/>')
        >>> t.contents = 'n'
        >>> t.string
        '<t>n</t>'

        """
        match = self._get_match()
        start, end = match.span('contents')
        if start != -1:
            self.replace_slice(start, end, contents)
        else:
            # This is a self-closing tag.
            start, end = match.span('self_closing')
            self.replace_slice(
                start, end, '>{0}</{1}>'.format(contents, match['name'])
            )
