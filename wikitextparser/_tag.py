"""Define the Tag class and tag-related regular expressions.

Although MediaWiki has a very strict HTML restrictions by default, this regexes
defined in this module don't follow those restrictions and allow most finding
most HTML tags.

For more info see:
* https://www.mediawiki.org/wiki/HTML_restriction

"""

from typing import Dict, Optional, Union, List, MutableSequence, Any
from warnings import warn

from regex import compile as regex_compile, VERBOSE, DOTALL

from ._wikitext import SubWikiText


# HTML elements all have names that only use alphanumeric ASCII characters
# https://www.w3.org/TR/html5/syntax.html#syntax-tag-name
TAG_NAME = rb'(?P<name>[A-Za-z0-9]++)'
# https://www.w3.org/TR/html5/infrastructure.html#space-character
SPACE_CHARS = rb' \t\n\u000C\r'
# http://stackoverflow.com/a/93029/2705757
# chrs = (chr(i) for i in range(sys.maxunicode))
# control_chars = ''.join(c for c in chrs if unicodedata.category(c) == 'Cc')
CONTROL_CHARS = rb'\x00-\x1f\x7f-\x9f'
# https://www.w3.org/TR/html5/syntax.html#syntax-attributes
ATTR_NAME = (
    rb'(?P<attr_name>[^' + SPACE_CHARS + CONTROL_CHARS + rb'\u0000"\'>/=]++)'
)
WS_EQ_WS = rb'[' + SPACE_CHARS + rb']*+=[' + SPACE_CHARS + rb']*+'
UNQUOTED_ATTR_VAL = (
    rb'(?P<attr_value>[^' + SPACE_CHARS + rb'"\'=<>`]++)'
)
QUOTED_ATTR_VAL = rb'(?P<quote>[\'"])(?P<attr_value>.+?)(?P=quote)'
# May include character references, but for now, ignore the fact that they
# cannot contain an ambiguous ampersand.
ATTR_VAL = (
    # If an empty attribute is to be followed by the optional
    # "/" character, then there must be a space character separating
    # the two. This rule is ignored here.
    rb'(?:' + WS_EQ_WS + UNQUOTED_ATTR_VAL + rb'[' + SPACE_CHARS + rb']*|'
    + WS_EQ_WS + QUOTED_ATTR_VAL + rb'[' + SPACE_CHARS + rb']*|'
    + rb'[' + SPACE_CHARS + rb']*+(?P<attr_value>)'  # empty attribute
    + rb')'
)
# Ignore ambiguous ampersand for the sake of simplicity.
ATTR_PATTERN = (
    rb'(?P<attr>[' + SPACE_CHARS + rb']++' + ATTR_NAME + ATTR_VAL + rb')'
)
ATTRS_MATCH = regex_compile(
    # Leading space is not required at the start of the attribute string.
    rb'(?P<attr>[' + SPACE_CHARS + rb']*+' + ATTR_NAME + ATTR_VAL + rb')*+',
).match
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
END_TAG_PATTERN = rb'(?P<end></{name}[' + SPACE_CHARS + rb']*+>)'
END_TAG = END_TAG_PATTERN.replace(rb'{name}', rb'(?P<end_name>(?P=name))')
TAG_CONTENTS = rb'(?P<contents>.*?)'
# Note that the following regex won't check for nested tags
TAG_FULLMATCH = regex_compile(
    rb'''
    # Note that the start group does not include the > character
    (?P<start>
        <''' + TAG_NAME + ATTR_PATTERN + rb'''*  # Todo: Possessive?
    )
    # After the attributes, or after the tag name if there are no attributes,
    # there may be one or more space characters. This is sometimes required but
    # ignored here.
    [''' + SPACE_CHARS + rb''']*+
    (?>
        (?P<self_closing>/>)|
        >''' + TAG_CONTENTS + END_TAG + rb'''|
        (?P<start_only>>)
    )
    ''',
    DOTALL | VERBOSE,
).fullmatch
# Todo: can the tags method be implemented using a TAG_FINDITER? Will
# that be more performant?
# TAG_FINDITER should not find any tag containing other tags.
# TAG_CONTENTS = r'(?P<contents>(?>(?!{TAG}).)*?)'.format(
#     TAG=TAG.format(**locals())
# )
# TAG_FINDITER = regex_compile(
#     TAG.format(**locals()), flags=DOTALL | VERBOSE
# ).finditer
START_TAG_PATTERN = (
    rb'(?P<start>'
    rb'<{name}(?:' + ATTR_PATTERN + rb')*'
    rb'[' + SPACE_CHARS + rb']*+'
    rb'(?:(?P<self_closing>/>)|>)'
    rb')'
)
START_TAG_FINDITER = regex_compile(
    START_TAG_PATTERN.replace(b'{name}', TAG_NAME)
).finditer


class SubWikiTextWithAttrs(SubWikiText):

    """Define a class for SubWikiText objects that have attributes.

    Any class that is going to inherit from SubWikiTextWithAttrs should provide
    _attrs_match property. Note that matching should be done on shadow.
    It's usually a good idea to cache the _attrs_match property.
    """

    _attrs_match = None  # type: Any

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
        return None

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
                q = 1 if match.string[ve] in b'"\'' else 0
                self[vs - q:ve + q] = '"{}"'.format(attr_value)
                return
        # The attr_name is new, add a new attribute.
        fmt = ' {}="{}"' if attr_value else ' {}'
        self.insert(
            match.end('start'),
            fmt.format(attr_name, attr_value)
        )
        return

    def set(self, attr_name: str, attr_value: str) -> None:
        """Deprecated alias for set_attr."""
        warn('`set` is depracated, use `set_attr` instead', DeprecationWarning)
        self.set_attr(attr_name, attr_value)

    def del_attr(self, attr_name: str) -> None:
        """Delete all the attributes with the given name.

        Pass if the attr_name is not found in self.
        """
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
        self.del_attr(attr_name)


class Tag(SubWikiTextWithAttrs):

    """Create a new Tag object."""

    _match_cache = None, None  # type: Any

    @property
    def _match(self) -> Any:
        """Return the match object for the current tag. Cache the result."""
        cached_match, cached_string = self._match_cache
        string = self.string
        if cached_string == string:
            return cached_match
        match = TAG_FULLMATCH(self._shadow)
        self._match_cache = match, string
        return match

    _attrs_match = _match

    @property
    def name(self) -> str:
        """Return tag name."""
        return self._match['name'].decode()

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
            self[s:e] = '>{0}</{1}>'.format(contents, match['name'].decode())

    @property
    def parsed_contents(self) -> SubWikiText:
        """Return the contents as a SubWikiText object."""
        span = self._match.span('contents')
        spans = self._type_to_spans
        swt_spans = spans.setdefault('SubWikiText', [span])
        return SubWikiText(
            self._lststr, spans, next(s for s in swt_spans if s == span)
        )
