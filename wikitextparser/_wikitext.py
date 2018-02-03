﻿"""Define the WikiText and SubWikiText classes."""


# Todo: consider using a tree structure (interval or segment tree).
# Todo: Consider using separate strings for each node.

from copy import deepcopy
from typing import (
    MutableSequence, Dict, List, Tuple, Union, Generator, Any, Optional,
)
from warnings import warn

from regex import VERBOSE, DOTALL, MULTILINE, IGNORECASE, search
from regex import compile as regex_compile
from wcwidth import wcswidth

from ._config import _tag_extensions
from ._spans import (
    COMMENT_PATTERN,
    parse_to_spans,
    VALID_EXTLINK_CHARS,
    BARE_EXTLINK_SCHEMES_PATTERN,
)


# External links (comment inclusive)
BRACKET_EXTERNALLINK_PATTERN = (
    rb'\[(?>//|' + BARE_EXTLINK_SCHEMES_PATTERN + rb')'
    + VALID_EXTLINK_CHARS + rb'\ *+[^\]\n]*+\]'
)
BARE_EXTERNALLINK_PATTERN = (
    rb'(?>' + BARE_EXTLINK_SCHEMES_PATTERN + rb')' + VALID_EXTLINK_CHARS
)
EXTERNALLINK_FINDITER = regex_compile(
    rb'(?:' + BARE_EXTERNALLINK_PATTERN
    + rb'|' + BRACKET_EXTERNALLINK_PATTERN + rb')',
    IGNORECASE,
).finditer

# Sections
SECTIONS_FULLMATCH = regex_compile(
    r'''
    (?<section>.*?)
    (?<section>
        ^(?<eq>={1,6})[^\n]+?(?P=eq)[ \t]*+$  # header
        .*?
    )*  # todo: why can't be made possessive?
    ''',
    DOTALL | MULTILINE | VERBOSE,
).fullmatch

# Tables
TABLE_FINDITER = regex_compile(
    rb"""
    # Table-start
    # Always starts on a new line with optional leading spaces or indentation.
    ^
    # Group the leading spaces or colons so that we can ignore them later.
    ([ :]*+)
    {\| # Table contents
    (?:
        # Any character, as long as it is not indicating another table-start
        (?!^\ *+\{\|).
    )*?
    # Table-end
    \n\s*+
    (?> \|} | \Z )
    """,
    DOTALL | MULTILINE | VERBOSE
).finditer

# Types which are detected by the
SPAN_PARSER_TYPES = {
    'Template', 'ParserFunction', 'WikiLink', 'Comment', 'Parameter', 'ExtTag'
}

WS = '\r\n\t '


class WikiText:

    """The WikiText class."""

    # In subclasses of WikiText _type is used as the key for _type_to_spans
    # Therefore: self._span can be found in self._type_to_spans[self._type].
    # The following acts as a default value.
    _type = 'WikiText'

    def __init__(
        self,
        string: Union[MutableSequence[str], str],
        _type_to_spans: Dict[str, List[List[int]]]=None,
    ) -> None:
        """Initialize the object.

        Set the initial values for self._lststr, self._type_to_spans.

        Parameters:
        - string: The string to be parsed or a list containing the string of
            the parent object.
        - _type_to_spans: If the lststr is already parsed, pass its
            _type_to_spans property as _type_to_spans to avoid parsing it
            again.

        """
        if _type_to_spans:
            self._type_to_spans = _type_to_spans
            self._lststr = string  # type: MutableSequence[str]
            return
        self._lststr = [string]
        span = [0, len(string)]
        self._span = span
        byte_array = bytearray(string, 'ascii', 'replace')
        _type = self._type
        if _type not in SPAN_PARSER_TYPES:
            type_to_spans = self._type_to_spans = parse_to_spans(byte_array)
            type_to_spans[_type] = [span]
            self._shadow_cache = string, byte_array, type_to_spans
        else:
            # In SPAN_PARSER_TYPES, we can't pass the original byte_array to
            # parser to generate the shadow because it will replace the whole
            # string with '_'. OTH, we can't modify before passing because
            # the generated _type_to_spans will lack self._span.
            # As a workaround we can add the missed span after parsing.
            head = byte_array[:2]
            tail = byte_array[-2:]
            byte_array[-2:] = byte_array[:2] = b'__'
            type_to_spans = parse_to_spans(byte_array)
            type_to_spans[_type].append(span)
            self._type_to_spans = type_to_spans
            byte_array[:2] = head
            byte_array[-2:] = tail
            self._shadow_cache = string, byte_array, type_to_spans

    def __str__(self) -> str:
        """Return self-object as a string."""
        return self.string

    def __repr__(self) -> str:
        """Return the string representation of self."""
        return '{0}({1})'.format(type(self).__name__, repr(self.string))

    def __contains__(self, value: Union[str, 'WikiText']) -> bool:
        """Return True if parsed_wikitext is inside self. False otherwise.

        Also self and parsed_wikitext should belong to the same parsed
        wikitext object for this function to return True.

        """
        # Is it useful (and a good practice) to also accepts str inputs
        # and check if self.string contains it?
        if isinstance(value, str):
            return value in self.string
        # isinstance(value, WikiText)
        if self._lststr is not value._lststr:
            return False
        ps, pe = value._span
        ss, se = self._span
        if ss <= ps and se >= pe:
            return True
        return False

    def __len__(self):
        return len(self.string)

    def __getitem__(self, key: Union[slice, int]) -> str:
        """Return self.string[item]."""
        return self.string[key]

    def _check_index(self, key: Union[slice, int]) -> (int, int):
        """Return adjusted start and stop index as tuple.

        Used in  __setitem__ and __delitem__.

        """
        ss, se = self._span
        if isinstance(key, int):
            if key < 0:
                key += se - ss
                if key < 0:
                    raise IndexError('index out of range')
            elif key >= se - ss:
                raise IndexError('index out of range')
            start = ss + key
            return start, start + 1
        # isinstance(key, slice)
        if key.step is not None:
            raise NotImplementedError(
                'step is not implemented for string setter.'
            )
        start, stop = key.start or 0, key.stop
        if start < 0:
            start += se - ss
            if start < 0:
                raise IndexError('start index out of range')
        if stop is None:
            stop = se - ss
        elif stop < 0:
            stop += se - ss
        if start > stop:
            raise IndexError(
                'stop index out of range or start is after the stop'
            )
        return start + ss, stop + ss

    def __setitem__(
        self,
        key: Union[slice, int],
        value: str,
    ) -> None:
        """Set a new string for the given slice or character index.

        Use this method instead of calling `insert` and `del` consecutively.
        By doing so only one of the `_extend_span_update` and
        `_shrink_span_update` functions will be called and the performance
        will improve.

        """
        start, stop = self._check_index(key)
        # Update lststr
        lststr = self._lststr
        lststr0 = lststr[0]
        lststr[0] = lststr0[:start] + value + lststr0[stop:]
        # Set the length of all subspans to zero because
        # they are all being replaced.
        self._close_subspans(start, stop)
        # Update the other spans according to the new length.
        len_change = len(value) + start - stop
        if len_change > 0:
            self._extend_span_update(
                estart=start,
                elength=len_change,
            )
        elif len_change < 0:
            self._shrink_span_update(
                rmstart=stop + len_change,  # new stop
                rmstop=stop,  # old stop
            )
        # Add the newly added spans contained in the value.
        type_to_spans = self._type_to_spans
        for type_, spans in parse_to_spans(
            bytearray(value, 'ascii', 'replace')
        ).items():
            spans_append = type_to_spans[type_].append
            for s, e in spans:
                spans_append([s + start, e + start])

    def __delitem__(self, key: Union[slice, int]) -> None:
        """Remove the specified range or character from self.string.

        Note: If an operation involves both insertion and deletion, it'll be
        safer to use the `insert` function first. Otherwise there is a
        possibility of insertion into the wrong spans.

        """
        start, stop = self._check_index(key)
        lststr = self._lststr
        lststr0 = lststr[0]
        # Update lststr
        lststr[0] = lststr0[:start] + lststr0[stop:]
        # Update spans
        self._shrink_span_update(start, stop)

    # Todo: def __add__(self, other) and __radd__(self, other)

    def insert(self, index: int, string: str) -> None:
        """Insert the given string before the specified index.

        This method has the same effect as ``self[index:index] = string``;
        it only avoids some condition checks as it rules out the possibility
        of the key being an slice, or the need to shrink any of the sub-spans.

        If parse is False, don't parse the inserted string.

        """
        ss, se = self._span
        lststr = self._lststr
        lststr0 = lststr[0]
        if index < 0:
            index += se - ss
            if index < 0:
                index = 0
        elif index > se - ss:  # Note that it is not >=. Index can be new.
            index = se - ss
        index += ss
        # Update lststr
        lststr[0] = lststr0[:index] + string + lststr0[index:]
        string_len = len(string)
        # Update spans
        self._extend_span_update(
            estart=index,
            elength=string_len,
        )
        # Remember newly added spans by the string.
        spans_dict = self._type_to_spans
        for k, v in parse_to_spans(
            bytearray(string, 'ascii', 'replace')
        ).items():
            spans_append = spans_dict[k].append
            for s, e in v:
                spans_append([s + index, e + index])

    @property
    def span(self) -> tuple:
        """Return the span of self.string according to the root node."""
        return tuple(self._span)

    @property
    def string(self) -> str:
        """Return str(self)."""
        start, end = self._span
        return self._lststr[0][start:end]

    @string.setter
    def string(self, newstring: str) -> None:
        """Set a new string for this object. Note the old data will be lost."""
        self[:] = newstring

    def _atomic_partition(self, char: int) -> Tuple[str, str, str]:
        """Partition self.string where `char`'s not in atomic sub-spans."""
        s, e = self._span
        index = self._shadow.find(char)
        if index == -1:
            return self._lststr[0][s:e], '', ''
        lststr0 = self._lststr[0]
        return lststr0[s:s + index], chr(char), lststr0[s + index + 1:e]

    def _subspans(self, type_: str) -> List[List[int]]:
        """Return all the sub-span including self._span."""
        return self._type_to_spans[type_]

    def _close_subspans(self, start: int, stop: int) -> None:
        """Close all sub-spans of (start, stop)."""
        ss, se = self._span
        for spans in self._type_to_spans.values():
            p = 0
            for i, (s, e) in enumerate(reversed(spans)):
                if (start <= s and e <= stop) and (ss != s or se != e):
                    spans.pop(len(spans) + p - i - 1)[:] = -1, -1
                    p += 1

    def _shrink_span_update(self, rmstart: int, rmstop: int) -> None:
        """Update self._type_to_spans according to the removed span.

        Warning: If an operation involves both _shrink_span_update and
        _extend_span_update, you might wanna consider doing the
        _extend_span_update before the _shrink_span_update as this function
        can cause data loss in self._type_to_spans.

        """
        # Note: No span should be removed from _type_to_spans.
        for spans in self._type_to_spans.values():
            p = 0
            for i, span in enumerate(reversed(spans)):
                s, e = span
                if e <= rmstart:
                    # s <= e <= rmstart <= rmstop
                    continue
                if rmstop <= s:
                    # rmstart <= rmstop <= s <= e
                    rmlength = rmstop - rmstart
                    span[:] = s - rmlength, e - rmlength
                    continue
                if rmstart <= s:
                    # s needs to be changed.
                    # We already know that rmstop is after the s,
                    # therefore the new s should be located at rmstart.
                    if rmstop >= e:
                        # rmstart <= s <= e < rmstop
                        spans.pop(len(spans) + p - 1 - i)[:] = -1, -1
                        p += 1
                        continue
                    # rmstart < s <= rmstop <= e
                    span[:] = rmstart, e + rmstart - rmstop
                    continue
                # From the previous comparison we know that s is before
                # the rmstart; so s needs no change.
                if rmstop < e:
                    # s <= rmstart <= rmstop <= e
                    span[1] -= rmstop - rmstart
                else:
                    # s <= rmstart <= e < rmstop
                    span[1] = rmstart

    def _extend_span_update(self, estart: int, elength: int) -> None:
        """Update self._type_to_spans according to the added span."""
        ss, se = self._span
        for spans in self._type_to_spans.values():
            for span in spans:
                if estart < span[1] or span[1] == estart == se:
                    span[1] += elength
                    # estart is before s, or at s but not on self_span
                    if estart < span[0] or span[0] == estart != ss:
                        span[0] += elength

    @property
    def nesting_level(self) -> int:
        """Return the nesting level of self.

        The minimum nesting_level is 0. Being part of any Template or
        ParserFunction increases the level by one.
        """
        ss, se = self._span
        level = 0
        type_to_spans = self._type_to_spans
        for s, e in type_to_spans['Template']:
            if s <= ss and se <= e:
                level += 1
        for s, e in type_to_spans['ParserFunction']:
            if s <= ss and se <= e:
                level += 1
        return level

    @property
    def _shadow(self) -> bytearray:
        """Return a copy of self.string with specific sub-spans replaced.

        Comments blocks are replaced by spaces. Other sub-spans are replaced
        by underscores.

        The replaced subspans are:
            ('Template', 'WikiLink', 'ParserFunction', 'ExtTag', 'Comment',)

        This function is called upon extracting tables or extracting the data
        inside them.
        """
        ss, se = self._span
        string = self._lststr[0][ss:se]
        cached_string, shadow, spans_dict = getattr(
            self, '_shadow_cache', (None, None, None))
        if cached_string == string:
            return shadow
        # In the old method the existing spans were used to create the shadow.
        # But it was slow because there can be thousands of spans and iterating
        # over them to find the relevant sub-spans could take a significant
        # amount of time. The new method tries to parse the self.string which
        # is usually much more faster because there are usually far less
        # sub-spans for individual objects.
        shadow = bytearray(string, 'ascii', 'replace')
        if self._type in SPAN_PARSER_TYPES:
            head = shadow[:2]
            tail = shadow[-2:]
            shadow[:2] = shadow[-2:] = b'__'
            spans_dict = parse_to_spans(shadow)
            shadow[:2] = head
            shadow[-2:] = tail
        else:
            spans_dict = parse_to_spans(shadow)
        self._shadow_cache = string, shadow, spans_dict
        return shadow

    @property
    def _dark_shadow(self):
        """Replace templates, parser functions, and comments with underscores.

        Used for external links where the mentioned types are valid but may
        contain invalid link characters characters in them.
        """
        shadow = self._shadow  # set or update _shadow_cache
        spans_dict = self._shadow_cache[2]
        dark_shadow = shadow[:]
        for type_ in 'Template', 'ParserFunction', 'Comment':
            for s, e in spans_dict[type_]:
                dark_shadow[s:e] = b'_' * (e - s)
        return dark_shadow

    def _pp_type_to_spans(self) -> dict:
        """Create the arguments for the parse function used in pformat method.


        Only pass the spans of subspans and change the spans to fit the new
        scope, i.e self.string.

        """
        ss, se = self._span
        if ss == 0 and se == len(self._lststr[0]):
            return deepcopy(self._type_to_spans)
        type_to_spans = {}  # type: Dict[str, List[List[int]]]
        for type_, spans in self._type_to_spans.items():
            newspans = type_to_spans[type_] = []
            for s, e in spans:
                if s < ss or e > se:
                    # This line is actually covered in tests, but
                    # peephole optimization prevents it from being detected.
                    # See: http://bugs.python.org/issue2506
                    continue  # pragma: no cover
                newspans.append([s - ss, e - ss])
        return type_to_spans

    def pprint(self, indent: str= '    ', remove_comments=False):
        """Deprecated, use self.pformat instead."""
        warn(
            'pprint method is deprecated, use pformat instead.',
            DeprecationWarning,
        )
        return self.pformat(indent, remove_comments)

    def pformat(self, indent: str= '    ', remove_comments=False) -> str:
        """Return a pretty-print of self.string as string.

        Try to organize templates and parser functions by indenting, aligning
        at the equal signs, and adding space where appropriate.

        Note that this function will not mutate self.

        """
        ws = WS
        # Do not try to do inplace pformat. It will overwrite on some spans.
        string = self.string
        parsed = WikiText([string], self._pp_type_to_spans())
        span = [0, len(string)]
        parsed._span = span
        parsed._type_to_spans['WikiText'] = [span]
        if remove_comments:
            for c in parsed.comments:
                del c[:]
        else:
            # Only remove comments that contain whitespace.
            for c in parsed.comments:
                if not c.contents.strip(ws):
                    del c[:]
        # First remove all current spacings.
        for template in parsed.templates:
            s_tl_name = template.name.strip(ws)
            template.name = (
                ' ' + s_tl_name + ' '
                if s_tl_name[0] == '{' else s_tl_name
            )
            args = template.arguments
            if not args:
                continue
            if ':' in s_tl_name:
                # Don't use False because we don't know for sure.
                not_a_parser_function = None
            else:
                not_a_parser_function = True
            # Required for alignment
            arg_stripped_names = [a.name.strip(ws) for a in args]
            arg_positionalities = [a.positional for a in args]
            arg_name_lengths = [
                wcswidth(n.replace('لا', '?'))
                if not p else 0
                for n, p in zip(arg_stripped_names, arg_positionalities)
            ]
            max_name_len = max(arg_name_lengths)
            # Format template.name.
            level = template.nesting_level
            newline_indent = '\n' + indent * level
            template.name += newline_indent
            if level == 1:
                last_comment_indent = '<!--\n-->'
            else:
                last_comment_indent = '<!--\n' + indent * (level - 2) + ' -->'
            # Special formatting for the last argument.
            last_arg = args.pop()
            last_is_positional = arg_positionalities.pop()
            last_value = last_arg.value
            last_stripped_value = last_value.strip(ws)
            if last_is_positional and last_value != last_stripped_value:
                stop_conversion = True
                if not last_value.endswith('\n' + indent * (level - 1)):
                    last_arg.value = last_value + last_comment_indent
            elif not_a_parser_function:
                stop_conversion = False
                last_arg.name = (
                    ' ' + arg_stripped_names.pop() + ' ' +
                    ' ' * (max_name_len - arg_name_lengths.pop())
                )
                last_arg.value = (
                    ' ' + last_stripped_value + '\n' + indent * (level - 1)
                )
            elif last_is_positional:
                # (last_value == last_stripped_value
                # and not_a_parser_function is not True)
                stop_conversion = True
                # Can't strip or adjust the position of the value
                # because this could be a positional argument in a template.
                last_arg.value = last_value + last_comment_indent
            else:
                stop_conversion = True
                # This is either a parser function or a keyword
                # argument in a template. In both cases the name
                # can be lstripped and the value can be rstripped.
                last_arg.name = ' ' + last_arg.name.lstrip(ws)
                if not last_value.endswith('\n' + indent * (level - 1)):
                    last_arg.value = (
                        last_value.rstrip(ws) + ' ' + last_comment_indent
                    )
            if not args:
                continue
            comment_indent = '<!--\n' + indent * (level - 1) + ' -->'
            for arg, stripped_name, positional, arg_name_len in zip(
                reversed(args),
                reversed(arg_stripped_names),
                reversed(arg_positionalities),
                reversed(arg_name_lengths),
            ):
                value = arg.value
                stripped_value = value.strip(ws)
                # Positional arguments of templates are sensitive to
                # whitespace. See:
                # https://meta.wikimedia.org/wiki/Help:Newlines_and_spaces
                if stop_conversion:
                    if not value.endswith(newline_indent):
                        arg.value += comment_indent
                elif positional and value != stripped_value:
                        stop_conversion = True
                        if not value.endswith(newline_indent):
                            arg.value += comment_indent
                elif not_a_parser_function:
                    arg.name = (
                        ' ' + stripped_name + ' ' +
                        ' ' * (max_name_len - arg_name_len)
                    )
                    arg.value = ' ' + stripped_value + newline_indent
        i = 0
        functions = parsed.parser_functions
        while i < len(functions):
            func = functions[i]
            i += 1
            name = func.name
            ls_name = name.lstrip(ws)
            lws = len(name) - len(ls_name)
            if lws:
                del func[2:lws + 2]
            if ls_name.lower() in ('#tag', '#invoke', ''):
                # The 2nd argument of `tag` parser function is an exception
                # and cannot be stripped.
                # So in `{{#tag:tagname|arg1|...}}`, no whitespace should be
                # added/removed to/from arg1.
                # See: [[mw:Help:Extension:ParserFunctions#Miscellaneous]]
                # All args of #invoke are also whitespace-sensitive.
                # Todo: Instead use comments to indent.
                continue
            args = func.arguments
            # Whitespace, including newlines, tabs, and spaces is stripped
            # from the beginning and end of all the parameters of
            # parser functions. See:
            # www.mediawiki.org/wiki/Help:Extension:ParserFunctions#
            #    Stripping_whitespace
            level = func.nesting_level
            short_indent = '\n' + indent * (level - 1)
            newline_indent = short_indent + indent
            if len(args) == 1:
                arg = args[0]
                # the first arg is both the first and last argument
                if arg.positional:
                    arg.value = (
                        newline_indent + arg.value.strip(ws) + short_indent
                    )
                else:
                    # Note that we don't add spaces before and after the
                    # '=' in parser functions because it could be part of
                    # an ordinary string.
                    arg.name = newline_indent + arg.name.lstrip(ws)
                    arg.value = arg.value.rstrip(ws) + short_indent
                functions = parsed.parser_functions
                continue
            # Special formatting for the first argument
            arg = args[0]
            if arg.positional:
                arg.value = \
                    newline_indent + arg.value.strip(ws) + newline_indent
            else:
                arg.name = newline_indent + arg.name.lstrip(ws)
                arg.value = arg.value.rstrip(ws) + newline_indent
            # Formatting the middle arguments
            for arg in args[1:-1]:
                if arg.positional:
                    arg.value = ' ' + arg.value.strip(ws) + newline_indent
                else:
                    arg.name = ' ' + arg.name.lstrip(ws)
                    arg.value = arg.value.rstrip(ws) + newline_indent
            # Special formatting for the last argument
            arg = args[-1]
            if arg.positional:
                arg.value = ' ' + arg.value.strip(ws) + short_indent
            else:
                arg.name = ' ' + arg.name.lstrip(ws)
                arg.value = arg.value.rstrip(ws) + short_indent
            functions = parsed.parser_functions
        return parsed.string

    @property
    def parameters(self) -> List['Parameter']:
        """Return a list of parameter objects."""
        return [
            Parameter(
                self._lststr,
                self._type_to_spans,
                span,
            ) for span in self._subspans('Parameter')
        ]

    @property
    def parser_functions(self) -> List['ParserFunction']:
        """Return a list of parser function objects."""
        return [
            ParserFunction(
                self._lststr,
                self._type_to_spans,
                span,
            ) for span in self._subspans('ParserFunction')
        ]

    @property
    def templates(self) -> List['Template']:
        """Return a list of templates as template objects."""
        return [
            Template(
                self._lststr,
                self._type_to_spans,
                span,
            ) for span in self._subspans('Template')
        ]

    @property
    def wikilinks(self) -> List['WikiLink']:
        """Return a list of wikilink objects."""
        return [
            WikiLink(
                self._lststr,
                self._type_to_spans,
                span,
            ) for span in self._subspans('WikiLink')
        ]

    @property
    def comments(self) -> List['Comment']:
        """Return a list of comment objects."""
        return [
            Comment(
                self._lststr,
                self._type_to_spans,
                span,
            ) for span in self._subspans('Comment')
        ]

    @property
    def external_links(self) -> List['ExternalLink']:
        """Return a list of found external link objects.

        Note:
            Templates adjacent to *bare* external links, are *not* considered
            part of the link. In reality, this depends on the contents of the
            template:

            >>> WikiText(
            ...    'http://example.com{{dead link}}'
            ...).external_links[0].url
            'http://example.com'

            But if the external link is in brackets, everything until the
            first space is treated as the url:
            >>> WikiText(
            ...    '[http://example.com{{space template}} text]'
            ...).external_links[0].url
            'http://example.com{{space template}}'
        """
        external_links = []  # type: List['ExternalLink']
        external_links_append = external_links.append
        type_to_spans = self._type_to_spans
        lststr = self._lststr
        ss, se = self._span
        spans = type_to_spans.setdefault('ExternalLink', [])
        spans_append = spans.append
        if not spans:
            # All the added spans will be new.
            for m in EXTERNALLINK_FINDITER(self._dark_shadow):
                span = m.span()
                span = [span[0] + ss, span[1] + ss]
                spans_append(span)
                external_links_append(
                    ExternalLink(lststr, type_to_spans, span)
                )
            return external_links
        # There are already some ExternalLink spans. Use the already existing
        # ones when the detected span is one of those.
        span_tuple_to_span_get = {(s[0], s[1]): s for s in spans}.get
        for m in EXTERNALLINK_FINDITER(self._dark_shadow):
            s, e = m.span()
            span = [s + ss, e + ss]
            old_span = span_tuple_to_span_get((span[0], span[1]))
            if old_span is None:
                spans_append(span)
            else:
                span = old_span
            external_links_append(ExternalLink(lststr, type_to_spans, span))
        return external_links

    @property
    def sections(self) -> List['Section']:
        """Return a list of section in current wikitext.

        The first section will always be the lead section, even if it is an
        empty string.

        """
        sections = []  # type: List['Section']
        sections_append = sections.append
        type_to_spans = self._type_to_spans
        lststr = self._lststr
        ss, se = self._span
        type_spans = type_to_spans.setdefault('Section', [])
        type_spans_append = type_spans.append
        full_match = SECTIONS_FULLMATCH(lststr[0][ss:se])
        section_spans = full_match.spans('section')
        levels = [len(eq) for eq in full_match.captures('eq')]
        s, e = section_spans.pop(0)
        s, e = s + ss, e + ss
        if not type_spans:
            # Lead section
            span = [s, e]
            type_spans_append(span)
            lead_section = Section(lststr, type_to_spans, span)
            # Other sections
            for current_level, (s, e) in zip(
                reversed(levels), reversed(section_spans)
            ):
                s, e = s + ss, e + ss
                # Add text of the current_section to any parent section.
                # Note that section 0 is not a parent for any subsection.
                for section, section_level, section_span in zip(
                    reversed(sections),
                    levels[-len(sections):],
                    reversed(type_spans),
                ):
                    if section_level > current_level:
                        e = section_span[1]
                    else:
                        break
                span = [s, e]
                type_spans_append(span)
                sections_append(Section(lststr, type_to_spans, span))
            sections_append(lead_section)
            sections.reverse()
            return sections
        # There are already some spans. Instead of appending new spans
        # use them when the detected span already exists.
        span_tuple_to_span = {(s[0], s[1]): s for s in type_spans}.get
        # Continue lead section
        old_span = span_tuple_to_span((s, e))
        if old_span is None:
            span = [s, e]
            type_spans_append(span)
        else:
            span = old_span
        lead_section = Section(lststr, type_to_spans, span)
        # Adjust other sections
        calced_spans = []
        calced_spans_append = calced_spans.append
        for current_level, (s, e) in zip(
            reversed(levels), reversed(section_spans)
        ):
            s, e = s + ss, e + ss
            # Add text of the current_section to any parent section.
            # Note that section 0 is not a parent for any subsection.
            for section, section_level, section_span in zip(
                reversed(sections),
                levels[-len(sections):],
                reversed(calced_spans),
            ):
                if section_level > current_level:
                    e = section_span[1]
                else:
                    break
            old_span = span_tuple_to_span((s, e))
            if old_span is None:
                span = [s, e]
                type_spans_append(span)
            else:
                span = old_span
            calced_spans_append(span)
            sections_append(Section(lststr, type_to_spans, span))
        sections_append(lead_section)
        sections.reverse()
        return sections

    @property
    def tables(self) -> List['Table']:
        """Return a list of found table objects."""
        tables = []  # type: List['Table']
        tables_append = tables.append
        type_to_spans = self._type_to_spans
        lststr = self._lststr
        shadow = self._shadow[:]
        ss, se = self._span
        spans = type_to_spans.setdefault('Table', [])
        if not spans:
            # All the added spans will be new.
            m = True  # type: Any
            while m:
                m = False
                for m in TABLE_FINDITER(shadow):
                    ms, me = m.span()
                    # Ignore leading whitespace using len(m[1]).
                    span = [ss + ms + len(m[1]), ss + me]
                    spans.append(span)
                    tables_append(Table(lststr, type_to_spans, span))
                    shadow[ms:me] = b'_' * (me - ms)
            return tables
        # There are already exists some spans. Try to use the already existing
        # before appending new spans.
        span_tuple_to_span_get = {(s[0], s[1]): s for s in spans}.get
        m = True
        while m:
            m = False
            for m in TABLE_FINDITER(shadow):
                ms, me = m.span()
                # Ignore leading whitespace using len(m[1]).
                span = [ss + ms + len(m[1]), ss + me]
                old_span = span_tuple_to_span_get((span[0], span[1]))
                if old_span is None:
                    spans.append(span)
                else:
                    span = old_span
                tables_append(Table(lststr, type_to_spans, span))
                shadow[ms:me] = b'_' * (me - ms)
        return tables

    def lists(self, pattern: str=None) -> List['WikiList']:
        """Return a list of WikiList objects.

        :pattern: The starting pattern for list items.
            Return all types of lists (ol, ul, and dl) if pattern is None.
            If pattern is not None, it will be passed to the regex engine,
            remember to escape the `*` character. Examples:

                - `\#` means top-level ordered lists
                - `\#\*` means unordred lists inside an ordered one
                - Currently definition lists are not well supported, but you
                    can use `[:;]` as their pattern.

            Tips and tricks:

                Be careful when using the following patterns as they will
                probably cause malfunction in the `sublists` method of the
                resultant List. (However don't worry about them if you are
                not going to use the `sublists` method.)

                - Use `\*+` as a pattern and nested unordered lists will be
                    treated as flat.
                - Use `\*\s*` as pattern to rtstrip `items` of the list.

                Although the pattern parameter is optional, but specifying it
                can improve the performance.

        """
        lists = []
        lststr = self._lststr
        type_to_spans = self._type_to_spans
        spans = type_to_spans.setdefault('WikiList', [])
        spans_append = spans.append
        span_tuple_to_span_get = {(s[0], s[1]): s for s in spans}.get
        patterns = ('\#', '\*', '[:;]') if pattern is None \
            else (pattern,)  # type: Tuple[str, ...]
        for pattern in patterns:
            list_regex = regex_compile(
                LIST_PATTERN_FORMAT.replace(b'{pattern}', pattern.encode()),
                MULTILINE,
            )
            ss = self._span[0]
            for m in list_regex.finditer(self._shadow):
                ms, me = m.span()
                span = [ss + ms, ss + me]
                old_span = span_tuple_to_span_get((span[0], span[1]))
                if old_span is None:
                    spans_append(span)
                else:
                    span = old_span
                lists.append(
                    WikiList(
                        lststr, pattern, m, type_to_spans, span, 'WikiList'
                    )
                )
        return lists

    def tags(self, name=None) -> List['Tag']:
        """Return all tags with the given name."""
        lststr = self._lststr
        type_to_spans = self._type_to_spans
        if name:
            if name in _tag_extensions:
                string = lststr[0]
                return [
                    Tag(lststr, type_to_spans, span, 'ExtTag')
                    for span in type_to_spans['ExtTag']
                    if string.startswith('<' + name, span[0])
                ]
            tags = []  # type: List['Tag']
            tags_append = tags.append
        else:
            # There is no name, add all extension tags. Before using shadow.
            tags = [
                Tag(lststr, type_to_spans, span, 'ExtTag')
                for span in type_to_spans['ExtTag']
            ]
            tags_append = tags.append
        # Get the left-most start tag, match it to right-most end tag
        # and so on.
        ss = self._span[0]
        shadow = self._shadow
        if name:
            # There is a name but it is not in TAG_EXTENSIONS.
            reversed_start_matches = reversed([m for m in regex_compile(
                START_TAG_PATTERN.replace(
                    rb'{name}', rb'(?P<name>' + name.encode() + rb')'
                )
            ).finditer(shadow)])
            end_search = regex_compile(END_TAG_PATTERN .replace(
                b'{name}', name.encode()
            )).search
        else:
            reversed_start_matches = reversed(
                [m for m in START_TAG_FINDITER(shadow)]
            )
        shadow_copy = shadow[:]
        spans = type_to_spans.setdefault('Tag', [])
        span_tuple_to_span_get = {(s[0], s[1]): s for s in spans}.get
        spans_append = spans.append
        for start_match in reversed_start_matches:
            if start_match['self_closing']:
                # Don't look for the end tag
                s, e = start_match.span()
                span = [ss + s, ss + e]
            else:
                # look for the end-tag
                if name:
                    # the end_search is already available
                    # noinspection PyUnboundLocalVariable
                    end_match = end_search(shadow_copy, start_match.end())
                else:
                    # build end_search according to start tag name
                    end_match = search(
                        END_TAG_PATTERN.replace(
                            b'{name}', start_match['name']
                        ),
                        shadow_copy,
                    )
                if end_match:
                    s, e = end_match.span()
                    shadow_copy[s:e] = b'_' * (e - s)
                    span = [ss + start_match.start(), ss + e]
                else:
                    # Assume start-only tag.
                    s, e = start_match.span()
                    span = [ss + s, ss + e]
            old_span = span_tuple_to_span_get((span[0], span[1]))
            if old_span is None:
                spans_append(span)
            else:
                span = old_span
            tags_append(Tag(lststr, type_to_spans, span, 'Tag'))
        return tags


class SubWikiText(WikiText):

    """Define a middle-class to be used by some other subclasses.

    Allow the user to focus on a particular part of WikiText.

    """

    def __init__(
        self,
        string: Union[str, MutableSequence[str]],
        _type_to_spans: Optional[Dict[str, List[List[int]]]]=None,
        _span: Optional[List[int]]=None,
        _type: Optional[Union[str, int]]=None,
    ) -> None:
        """Initialize the object."""
        _type = _type or type(self).__name__
        self._type = _type

        super().__init__(string, _type_to_spans)

        # _type_to_spans and _span are either both None or not None.
        if _type_to_spans is None and _type not in SPAN_PARSER_TYPES:
            _type_to_spans = self._type_to_spans
            span = [0, len(string)]
            _type_to_spans[_type] = [span]
            self._span = span
        else:
            self._span = \
                self._type_to_spans[_type][-1] if _span is None else _span

    def _subspans(self, _type: str) -> Generator[int, None, None]:
        """Yield all the sub-span indices excluding self._span."""
        s, e = self._span
        for span in self._type_to_spans[_type]:
            # Do not yield self._span.
            ss, se = span
            if s < ss and se <= e:
                yield span


if __name__ == '__main__':
    # To make PyCharm happy! http://stackoverflow.com/questions/41524090
    from ._tag import (
        Tag, START_TAG_PATTERN, END_TAG_BYTES_PATTERN, START_TAG_FINDITER
    )
    from ._parser_function import ParserFunction
    from ._template import Template
    from ._wikilink import WikiLink
    from ._comment import Comment
    from ._externallink import ExternalLink
    from ._section import Section
    from ._wikilist import WikiList, LIST_PATTERN_FORMAT
    from ._table import Table
    from ._parameter import Parameter
