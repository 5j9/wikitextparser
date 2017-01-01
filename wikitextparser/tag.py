"""Define the Tag class."""

from typing import Dict, Optional, Match
from warnings import warn

import regex

from .wikitext import SubWikiText


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
    r'(?P<attr_value>[^{SPACE_CHARS}"\'=<>`]+)'
).format(**locals())
QUOTED_ATTR_VAL = r'(?P<quote>[\'"])(?P<attr_value>.+?)(?P=quote)'
# May include character references, but for now, ignore the fact that they
# cannot contain an ambiguous ampersand.
ATTR_VAL = (
    r'''
    (?:
        # If an empty attribute is to be followed by the optional
        # "/" character, then there must be a space character separating
        # the two. This rule is ignored here.
        {WS_EQ_WS}{UNQUOTED_ATTR_VAL}[{SPACE_CHARS}]*|
        {WS_EQ_WS}{QUOTED_ATTR_VAL}[{SPACE_CHARS}]*|
        [{SPACE_CHARS}]*(?P<attr_value>) # empty attribute
    )
    '''
).format(**locals())
# Ignore ambiguous ampersand for the sake of simplicity.
ATTR = r'(?P<attr>[{SPACE_CHARS}]+{ATTR_NAME}{ATTR_VAL})'.format(**locals())
ATTRS_REGEX = regex.compile(
    # Leading space is not required at the start of the attribute string.
    r'(?P<attr>[{SPACE_CHARS}]*{ATTR_NAME}{ATTR_VAL})*'
    .format(**locals()).encode(),
    flags=regex.VERBOSE
)
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
        <{TAG_NAME}(?:{ATTR})*
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
        <{TAG_NAME}{ATTR}*
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


class SubWikiTextWithAttrs(SubWikiText):

    """Define a class for SubWikiText objects that have attributes.

    Any class that is going to inherit from SubWikiTextWithAttrs should provide
    _attrs_match property. Note that matching should be done on shadow.
    It's usually a good idea to cache the _attrs_match property.

    """

    _attrs_match = None  # type: Match

    @property
    def attrs(self) -> Dict[str, str]:
        """Return self attributes as a dictionary."""
        spans = self._attrs_match.spans
        string = self.string
        return dict(zip(
            (string[s:e] for s, e in spans('attr_name')),
            (string[s:e] for s, e in spans('attr_value')),
        ))

    def has_attr(self, attr_name: str) -> bool:
        """Return True if self contains an attribute with the given name."""
        string = self.string
        return attr_name in (
            string[s:e] for s, e in self._attrs_match.spans('attr_name')
        )

    def has(self, attr_name: str) -> bool:
        """Deprecated alias for has_attr."""
        warn('`has` is depracated, use `has_attr` instead', DeprecationWarning)
        return self.has_attr(attr_name)

    def get_attr(self, attr_name: str) -> Optional[str]:
        """Return the value of the last attribute with the given name.

        Return None if the attr_name does not exist in self.
        If there are already multiple attributes with the given name, only
            return the value of the last one.
        Return an empty string if the mentioned name is an empty attribute.

        """
        spans = self._attrs_match.spans
        string = self.string
        for i, (s, e) in enumerate(reversed(spans('attr_name'))):
            if string[s:e] == attr_name:
                s, e = spans('attr_value')[-i - 1]
                return string[s:e]

    def get(self, attr_name: str) -> Optional[str]:
        """Deprecated alias for get_attr."""
        warn('`get` is depracated, use `get_attr` instead', DeprecationWarning)
        return self.get_attr(attr_name)

    def set_attr(self, attr_name: str, attr_value: str) -> None:
        """Set the value for the given attribute name.

        If there are already multiple attributes with the given name, only
        set the value for the last one.
        If attr_value == '', use the implicit empty attribute syntax.

        """
        match = self._attrs_match
        string = self.string
        for i, (s, e) in enumerate(reversed(match.spans('attr_name'))):
            if string[s:e] == attr_name:
                vs, ve = match.spans('attr_value')[-i - 1]
                q = 1 if match.string[ve] in '"\'' else 0
                self[vs - q:ve + q] = '"{}"'.format(
                    attr_value.replace('"', '&quot;')
                )
                return
        # The attr_name is new, add a new attribute.
        fmt = ' {}="{}"' if attr_value else ' {}'
        self.insert(
            match.span('start')[1],
            fmt.format(attr_name, attr_value.replace('"', '&quot;'))
        )
        return

    def set(self, attr_name: str, attr_value: str) -> None:
        """Deprecated alias for set_attr."""
        warn('`set` is depracated, use `set_attr` instead', DeprecationWarning)
        return self.set_attr(attr_name, attr_value)

    def del_attr(self, attr_name: str) -> None:
        """Delete all the attributes with the given name.

        Pass if the attr_name is not found in self.

        """
        # Todo: Cell match may have an offset?
        match = self._attrs_match
        string = self.string
        # Must be done in reversed order because the spans
        # change after each deletion.
        for i, (s, e) in enumerate(reversed(match.spans('attr_name'))):
            if string[s:e] == attr_name:
                start, stop = match.spans('attr')[-i - 1]
                del self[start:stop]

    def delete(self, attr_name: str) -> None:
        """Deprecated alias for del_attr."""
        warn(
            '`delete` is depracated, use `del_attr` instead',
            DeprecationWarning
        )
        return self.del_attr(attr_name)


class Tag(SubWikiTextWithAttrs):

    """Create a new Tag object."""

    def __init__(
        self,
        string: str or list,
        _type_to_spans: list=None,
        _index: int=None,
        match: Match=None,
    ) -> None:
        """Initialize the Tag object.

        Run _common_init and set _type_to_spans['extlinks'].

        """
        super().__init__(string, _type_to_spans, _index, 'Tag')
        self._cached_match = (
            TAG_REGEX.fullmatch(string) if match is None else match
        )

    @property
    def _match(self) -> Match:
        """Return the match object for the current tag. Cache the result."""
        shadow = self._shadow
        cached_match = self._cached_match
        if cached_match.string != shadow:
            # Compute the match
            cached_match = TAG_REGEX.fullmatch(shadow)
            self._cached_match = cached_match
        return cached_match

    _attrs_match = _match

    @property
    def name(self) -> str:
        """Return tag name."""
        s, e = self._match.span('name')
        return self.string[s:e]

    @name.setter
    def name(self, name: str) -> None:
        """Set a new tag name."""
        # The name in the end tag should be replaced first because the spans
        # of the match object change after each replacement.
        span = self._match.span
        start, end = span('end_name')
        if start != -1:
            self[start:end] = name
        start, end = span('name')
        self[start:end] = name

    @property
    def contents(self) -> Optional[str]:
        """Return tag contents."""
        s, e = self._match.span('contents')
        if s == -1:
            return None
        return self.string[s:e]

    @contents.setter
    def contents(self, contents: str) -> None:
        """Set new contents.

        Note that if the tag is self-closing, then it will be expanded to
        have a start tag and an end tag. For example:
        >>> t = Tag('<t/>')
        >>> t.contents = 'n'
        >>> t.string
        '<t>n</t>'

        """
        match = self._match
        start, end = match.span('contents')
        if start != -1:
            self[start:end] = contents
        else:
            # This is a self-closing tag.
            s, e = match.span('self_closing')
            self[s:e] = '>{0}</{1}>'.format(contents, match['name'])

    @property
    def parsed_contents(self) -> SubWikiText:
        """Return the contents as a SubWikiText object."""
        span = self._match.span('contents')
        spans = self._type_to_spans
        swt_spans = spans.setdefault('SubWikiText', [span])
        index = next((i for i, s in enumerate(swt_spans) if s == span))
        return SubWikiText(self._bytearray, spans, index)


def attrs_parser(attrs: str, pos=0, endpos=-1) -> Dict[str, str]:
    """Return a dict of attribute names and values."""
    m = ATTRS_REGEX.match(attrs, pos=pos, endpos=endpos)
    if m:
        captures = m.captures
        return dict(zip(captures('attr_name'), captures('attr_value')))
