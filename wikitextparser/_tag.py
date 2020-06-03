﻿"""Define the Tag class and tag-related regular expressions.

Although MediaWiki has a very strict HTML restrictions by default, regexes
defined in this module don't follow those restrictions and allow most finding
most HTML tags.

For more info see:
* https://www.mediawiki.org/wiki/HTML_restriction

"""

from typing import Dict, List, Optional, Any

from regex import compile as regex_compile, VERBOSE, DOTALL

from ._spans import ATTR_PATTERN, SPACE_CHARS, END_TAG_PATTERN
from ._wikitext import SubWikiText


# HTML elements all have names that only use alphanumeric ASCII characters
# https://www.w3.org/TR/html5/syntax.html#syntax-tag-name
ASCII_TAG_NAME = rb'(?<name>[A-Za-z0-9]++)'
# Todo: can the tags method be implemented using a TAG_FINDITER? Will
# that be more performant?
# TAG_FINDITER should not find any tag containing other tags.
# TAG_CONTENTS = r'(?<contents>(?>(?!{TAG}).)*?)'.format(
#     TAG=TAG.format(**locals())
# )
# TAG_FINDITER = regex_compile(
#     TAG.format(**locals()), flags=DOTALL | VERBOSE
# ).finditer
# Note that the following regex won't check for nested tags
TAG_FULLMATCH = regex_compile(
    rb'''
    # Note that the start group does not include the > character
    <''' + ASCII_TAG_NAME + ATTR_PATTERN + rb'''*  # Todo: Possessive?
    # After the attributes, or after the tag name if there are no attributes,
    # there may be one or more space characters. This is sometimes required but
    # ignored here.
    (?<attr_insert>)
    [''' + SPACE_CHARS + rb''']*+
    (?>
        (?<self_closing>/\s*>)
        |>(?<contents>.*?)'''
    + END_TAG_PATTERN.replace(rb'{name}', rb'(?<end_name>(?P=name))')
    + rb'''|>  # only start; no end tag
    )''',
    DOTALL | VERBOSE,
).fullmatch


class SubWikiTextWithAttrs(SubWikiText):

    """Define a class for SubWikiText objects that have attributes.

    Any class that is going to inherit from SubWikiTextWithAttrs should provide
    _attrs_match property. Note that matching should be done on shadow.
    It's usually a good idea to cache the _attrs_match property.
    """

    __slots__ = '_attrs_match'

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
            match.end('attr_insert'),
            fmt.format(attr_name, attr_value)
        )
        return

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


class Tag(SubWikiTextWithAttrs):

    __slots__ = '_match_cache'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._match_cache = None, None

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
        """Tag's name. Support both get and set operations."""
        return self._match['name'].decode()

    @name.setter
    def name(self, name: str) -> None:
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
        """Tag contents. Support both get and set operations.

        setter:
            Set contents to a new value.
            Note that if the tag is self-closing, then it will be expanded to
            have a start tag and an end tag. For example:
            >>> t = Tag('<t/>')
            >>> t.contents = 'n'
            >>> t.string
            '<t>n</t>'
        """
        s, e = self._match.span('contents')
        return self(s, e)

    @contents.setter
    def contents(self, contents: str) -> None:
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
        se = self._span[0]
        s, e = self._match.span('contents')
        type_to_spans = self._type_to_spans
        span = type_to_spans.setdefault('SubWikiText', [se + s, se + e])
        return SubWikiText(self._lststr, type_to_spans, span, 'SubWikiText')

    @property
    def _extension_tags(self):
        return super()._extension_tags[1:]

    def get_tags(self, name=None) -> List['Tag']:
        return super().get_tags(name)[1:]

    @property
    def _relative_contents_end(self) -> int:
        return self._match.end('contents')
