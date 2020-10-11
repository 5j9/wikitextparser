"""Define the WikiText and SubWikiText classes."""

from bisect import bisect_left, bisect_right, insort_right
from copy import deepcopy
from html import unescape
from itertools import islice
from operator import attrgetter
from typing import (
    Dict, Generator, Iterable, List, MutableSequence, Optional, Tuple, Union)
from warnings import warn

from regex import DOTALL, IGNORECASE, MULTILINE, VERBOSE, \
    compile as regex_compile, finditer, search
from wcwidth import wcswidth

# noinspection PyProtectedMember
from ._config import (
    _HTML_TAG_NAME, _bare_external_link_schemes, _tag_extensions,
    regex_pattern)
from ._spans import (
    BARE_EXTERNAL_LINK, END_TAG_PATTERN, EXTERNAL_LINK_URL_TAIL,
    INVALID_URL_CHARS, PARSABLE_TAG_EXTENSION_NAME, START_TAG_PATTERN,
    parse_to_spans)

NAME_CAPTURING_HTML_START_TAG_FINDITER = regex_compile(
    START_TAG_PATTERN.replace(
        b'{name}', rb'(?<name>' + _HTML_TAG_NAME + rb')', 1)).finditer

PARSABLE_TAG_EXTENSIONS_MATCH = regex_compile(
    rb'<' + PARSABLE_TAG_EXTENSION_NAME + rb'\b', IGNORECASE).match

# External links
BRACKET_EXTERNAL_LINK_SCHEMES = regex_pattern(
    _bare_external_link_schemes | {'//'})
BRACKET_EXTERNAL_LINK_URL = (
    BRACKET_EXTERNAL_LINK_SCHEMES + EXTERNAL_LINK_URL_TAIL)
BRACKET_EXTERNAL_LINK = (
    rb'\[' + BRACKET_EXTERNAL_LINK_URL + rb'[^\]\n]*+\]')
EXTERNAL_LINK = \
    rb'(?>' + BARE_EXTERNAL_LINK + rb'|' + BRACKET_EXTERNAL_LINK + rb')'
EXTERNAL_LINK_FINDITER = regex_compile(EXTERNAL_LINK, IGNORECASE).finditer
INVALID_EXT_CHARS_SUB = regex_compile(  # the [:-4] slice allows \[ and \]
    rb'[' + INVALID_URL_CHARS[:-4] + rb'{}]').sub

# Sections
SECTION_HEADING = rb'^(?<equals>={1,6})[^\n]+?(?P=equals)[ \t]*+$'
SECTIONS_FULLMATCH = regex_compile(
    rb'(?<section>(?<equals>).*?)'  # lead section
    rb'(?<section>'
    + SECTION_HEADING +  # heading
    rb'.*?'  # section content
    rb')*',  # Todo: why can't be made possessive?
    DOTALL | MULTILINE | VERBOSE,
).fullmatch

# Tables
TABLE_FINDITER = regex_compile(
    rb"""
    # Table-start
    # Always starts on a new line with optional leading spaces or indentation.
    (?<=^[ :\0]*+)
    {\| # Table contents
    (?:
        # Any character, as long as it is not indicating another table-start
        (?!^\ *+\{\|).
    )*?
    # Table-end
    \n\s*+
    (?> \|} | \Z )
    """,
    DOTALL | MULTILINE | VERBOSE).finditer

BOLD_ITALIC_FINDITER = regex_compile(  # bold-italic, bold, or italic tokens
    rb"""((?>'\0*)*?)'\0*+'\0*+('\0*+('\0*+')?+)?+(?=[^']|$)|($)""",
    MULTILINE | VERBOSE).finditer

BOLD_FINDITER = regex_compile(rb"""
    # start token
    '\0*+'\0*+'
    # content
    (\0*+[^'\n]++.*?)
    # end token
    (?:'\0*+'\0*+'|$)
""", MULTILINE | VERBOSE).finditer

ITALIC_FINDITER = regex_compile(rb"""
    # start token
    '\0*+'
    # content
    (\0*+[^'\n]++.*?)
    # end token
    (?:'\0*+'|$)
""", MULTILINE | VERBOSE).finditer

# Types which are detected by parse_to_spans
SPAN_PARSER_TYPES = {
    'Template', 'ParserFunction', 'WikiLink', 'Comment', 'Parameter',
    'ExtensionTag'}

WS = '\r\n\t '


class DeadIndexError(TypeError):
    pass


class DeadIndex(int):
    """Do not allow adding to another integer but allow usage in a slice.

    Addition of indices is the main operation during mutation of WikiText
    objects.
    """
    __slots__ = ()

    def __add__(self, o):
        raise DeadIndexError(
            'this usually means that the object has died '
            '(overwritten or deleted) and cannot be mutated')
    __radd__ = __add__

    def __repr__(self):
        return 'DeadIndex()'


DEAD_INDEX = DeadIndex()  # == int() == 0
DEAD_SPAN = DEAD_INDEX, DEAD_INDEX, None, None


class WikiText:

    # In subclasses of WikiText _type is used as the key for _type_to_spans
    # Therefore: self._span can be found in self._type_to_spans[self._type].
    # The following class attribute acts as a default value.
    _type = 'WikiText'

    __slots__ = '_type_to_spans', '_lststr', '_span_data', '_shadow_cache'

    def __init__(
        self,
        string: Union[MutableSequence[str], str],
        _type_to_spans: Dict[str, List[List[int]]] = None,
    ) -> None:
        """Initialize the object.

        Set the initial values for self._lststr, self._type_to_spans.

        :param string: The string to be parsed or a list containing the string
            of the parent object.
        :param _type_to_spans: If the lststr is already parsed, pass its
            _type_to_spans property as _type_to_spans to avoid parsing it
            again.
        """
        if _type_to_spans is not None:
            self._type_to_spans = _type_to_spans
            self._lststr = string  # type: MutableSequence[str]
            return
        self._lststr = [string]
        byte_array = bytearray(string, 'ascii', 'replace')
        span = self._span_data = [0, len(string), None, byte_array]
        _type = self._type
        if _type not in SPAN_PARSER_TYPES:
            type_to_spans = self._type_to_spans = parse_to_spans(byte_array)
            type_to_spans[_type] = [span]
            self._shadow_cache = string, byte_array
        else:
            # In SPAN_PARSER_TYPES, we can't pass the original byte_array to
            # parser to generate the shadow because it will replace the whole
            # string with '_'. Also, we can't just modify it before passing
            # because the generated _type_to_spans will lack self._span.
            # As a workaround we can add the missed span after parsing.
            if type(self) is Parameter:
                head = byte_array[:2]
                tail = byte_array[-2:]
                byte_array[:2] = b'__'
                byte_array[-2:] = b'__'
            else:
                head = byte_array[0]
                tail = byte_array[-1]
                byte_array[0] = 3
                byte_array[-1] = 32
            type_to_spans = parse_to_spans(byte_array)
            self._shadow_cache = string, byte_array
            type_to_spans[_type].insert(0, span)
            self._type_to_spans = type_to_spans
            if type(self) is Parameter:
                byte_array[:2] = head
                byte_array[-2:] = tail
            else:
                byte_array[0] = head
                byte_array[-1] = tail

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
        ps, pe, _, _ = value._span_data
        ss, se, _, _ = self._span_data
        if ss <= ps and se >= pe:
            return True
        return False

    def __len__(self):
        s, e, _, _ = self._span_data
        return e - s

    def __call__(
        self, start: int, stop: Optional[int] = False, step: int = None
    ) -> str:
        """Return `self.string[start]` or `self.string[start:stop]`.

        Return self.string[start] if stop is False.
        Otherwise return self.string[start:stop:step].
        """
        if stop is False:
            if start >= 0:
                return self._lststr[0][self._span_data[0] + start]
            return self._lststr[0][self._span_data[1] + start]
        s, e, _, _ = self._span_data
        return self._lststr[0][
            s if start is None else (s + start if start >= 0 else e + start):
            e if stop is None else (s + stop if stop >= 0 else e + stop):
            step]

    def _check_index(self, key: Union[slice, int]) -> (int, int):
        """Return adjusted start and stop index as tuple.

        Used in  __setitem__ and __delitem__.
        """
        ss, se, _, _ = self._span_data
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
                'step is not implemented for string setter.')
        start = key.start or 0
        stop = key.stop
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
                'stop index out of range or start is after the stop')
        return start + ss, stop + ss

    def __setitem__(self, key: Union[slice, int], value: str) -> None:
        """Set a new string for the given slice or character index.

        Use this method instead of calling `insert` and `del` consecutively.
        By doing so only one of the `_insert_update` and
        `_shrink_update` functions will be called and the performance
        will improve.
        """
        abs_start, abs_stop = self._check_index(key)
        # Update lststr
        lststr = self._lststr
        lststr0 = lststr[0]
        lststr[0] = lststr0[:abs_start] + value + lststr0[abs_stop:]
        # Set the length of all subspans to zero because
        # they are all being replaced.
        self._close_subspans(abs_start, abs_stop)
        # Update the other spans according to the new length.
        val_ba = bytearray(value, 'ascii', 'replace')
        len_change = len(value) + abs_start - abs_stop
        if len_change > 0:
            self._insert_update(abs_start, len_change)
        elif len_change < 0:
            self._del_update(
                rmstart=abs_stop + len_change,  # new stop
                rmstop=abs_stop)  # old stop
        # Add the newly added spans contained in the value.
        type_to_spans = self._type_to_spans
        for type_, value_spans in parse_to_spans(val_ba).items():
            tts = type_to_spans[type_]
            for s, e, m, ba in value_spans:
                try:
                    insort_right(tts, [abs_start + s, abs_start + e, m, ba])
                except TypeError:
                    # already exists which has lead to comparing Matches
                    continue

    def __delitem__(self, key: Union[slice, int]) -> None:
        """Remove the specified range or character from self.string.

        Note: If an operation involves both insertion and deletion, it'll be
        safer to use the `insert` function first. Otherwise there is a
        possibility of insertion into the wrong spans.
        """
        start, stop = self._check_index(key)
        lststr = self._lststr
        lststr0 = lststr[0]
        lststr[0] = lststr0[:start] + lststr0[stop:]
        # Update spans
        self._del_update(start, stop)

    # Todo: def __add__(self, other) and __radd__(self, other)

    def insert(self, index: int, string: str) -> None:
        """Insert the given string before the specified index.

        This method has the same effect as ``self[index:index] = string``;
        it only avoids some condition checks as it rules out the possibility
        of the key being an slice, or the need to shrink any of the sub-spans.
        """
        ss, se, _, _ = self._span_data
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
        self._insert_update(
            index=index,
            length=string_len)
        # Remember newly added spans by the string.
        type_to_spans = self._type_to_spans
        byte_array = bytearray(string, 'ascii', 'replace')
        for type_, spans in parse_to_spans(byte_array).items():
            for s, e, _, _ in spans:
                insort_right(
                    type_to_spans[type_],
                    [index + s, index + e, None, byte_array])

    @property
    def span(self) -> tuple:
        """Return the span of self relative to the start of the root node."""
        # In Python 3.7 and earlier, generalized iterable unpacking in yield
        # and return statements requires enclosing parentheses:
        # https://docs.python.org/3.8/whatsnew/3.8.html#other-language-changes
        return (*self._span_data[:2],)  # noqa

    @property
    def string(self) -> str:
        """Return str(self). Support get, set, and delete operations.

        getter and deleter: Note that this will overwrite the current string,
            emptying any object that points to the old string.
        """
        start, end, _, _ = self._span_data
        return self._lststr[0][start:end]

    @string.setter
    def string(self, newstring: str) -> None:
        self[:] = newstring

    @string.deleter
    def string(self) -> None:
        del self[:]

    def _subspans(self, type_: str) -> List[List[int]]:
        """Return all the sub-span including self._span."""
        return self._type_to_spans[type_]

    def _close_subspans(self, start: int, stop: int) -> None:
        """Close all sub-spans of (start, stop)."""
        ss, se, _, _ = self._span_data
        for spans in self._type_to_spans.values():
            b = bisect_left(spans, [start])
            for i, (s, e, _, _) in enumerate(
                spans[b:bisect_right(spans, [stop], b)]
            ):
                if e <= stop:
                    if ss != s or se != e:
                        spans.pop(i + b)[:] = DEAD_SPAN
                        b -= 1

    def _del_update(self, rmstart: int, rmstop: int) -> None:
        """Update self._type_to_spans according to the removed span.

        Warning: If an operation involves both _shrink_update and
        _insert_update, you might wanna consider doing the
        _insert_update before the _shrink_update as this function
        can cause data loss in self._type_to_spans.
        """
        # Note: The following algorithm won't work correctly if spans
        # are not sorted.
        # Note: No span should be removed from _type_to_spans.
        for spans in self._type_to_spans.values():
            i = len(spans) - 1
            while i >= 0:
                # todo update byte_aray
                s, e, _, b = span = spans[i]
                if rmstop <= s:
                    # rmstart <= rmstop <= s <= e
                    rmlength = rmstop - rmstart
                    # todo
                    span[:] = s - rmlength, e - rmlength, None, None
                    i -= 1
                    continue
                break  # pragma: no cover
            else:
                continue  # pragma: no cover
            while True:
                if rmstart <= s:
                    if rmstop < e:
                        # rmstart < s <= rmstop < e
                        # todo: update byte_array instead
                        span[:] = rmstart, e + rmstart - rmstop, None, None
                        i -= 1
                        if i < 0:
                            break
                        s, e, _, _ = span = spans[i]
                        continue
                    # rmstart <= s <= e < rmstop
                    spans.pop(i)[:] = DEAD_SPAN
                    i -= 1
                    if i < 0:
                        break
                    s, e, _, _ = span = spans[i]
                    continue
                break  # pragma: no cover
            while i >= 0:
                if e <= rmstart:
                    # s <= e <= rmstart <= rmstop
                    i -= 1
                    if i < 0:
                        break
                    s, e, _, _ = span = spans[i]
                    continue
                # s <= rmstart <= rmstop <= e
                span[1] -= rmstop - rmstart
                span[2] = None
                # todo: update bytearray instead
                span[3] = None
                i -= 1
                if i < 0:
                    break
                s, e, _, _ = span = spans[i]
                continue

    def _insert_update(self, index: int, length: int) -> None:
        """Update self._type_to_spans according to the added length."""
        self_span = ss, se, _, _ = self._span_data
        for spans in self._type_to_spans.values():
            for span in spans:
                s0, s1, _, _ = span
                if index < s1 or s1 == index == se:
                    span[1] += length
                    span[3] = None  # todo: update instead
                    # index is before s, or at s but not on self_span
                    if index < s0 or s0 == index != ss or (
                        s0 == index and span is not self_span
                    ):
                        span[0] += length

    def _nesting_level(self, parent_types) -> int:
        ss, se, _, _ = self._span_data
        level = 0
        type_to_spans = self._type_to_spans
        for type_ in parent_types:
            spans = type_to_spans[type_]
            for s, e, _, _ in spans[:bisect_right(spans, [ss + 1])]:
                if se <= e:
                    level += 1
        return level

    @property
    def _shadow(self) -> bytearray:
        """Return a copy of self.string with specific sub-spans replaced.

        Comments blocks are replaced by spaces. Other sub-spans are replaced
        by underscores.

        The replaced sub-spans are: (
            'Template', 'WikiLink', 'ParserFunction', 'ExtensionTag',
            'Comment',
        )

        This function is called upon extracting tables or extracting the data
        inside them.
        """
        ss, se, m, cached_shadow = span_data = self._span_data
        if cached_shadow is not None:
            return cached_shadow
        shadow = span_data[3] = \
            bytearray(self._lststr[0][ss:se], 'ascii', 'replace')
        if self._type in SPAN_PARSER_TYPES:
            head = shadow[:2]
            tail = shadow[-2:]
            shadow[:2] = shadow[-2:] = b'__'
            parse_to_spans(shadow)
            shadow[:2] = head
            shadow[-2:] = tail
        else:
            parse_to_spans(shadow)
        return shadow

    @property
    def _ext_link_shadow(self):
        """Replace the invalid chars of SPAN_PARSER_TYPES with b'_'.

        For comments, all characters are replaced, but for ('Template',
        'ParserFunction', 'Parameter') only invalid characters are replaced.
        """
        ss, se, _, _ = self._span_data
        byte_array = bytearray(self._lststr[0][ss:se], 'ascii', 'replace')
        subspans = self._subspans
        for type_ in 'Comment', 'WikiLink':
            for s, e, _, _ in subspans(type_):
                byte_array[s:e] = (e - s) * b'_'
        for type_ in 'Template', 'ParserFunction', 'Parameter':
            for s, e, _, _ in subspans(type_):
                byte_array[s:e] = b'  ' + INVALID_EXT_CHARS_SUB(
                    b' ', byte_array[s + 2:e - 2]) + b'  '
        return byte_array

    def _inner_type_to_spans_copy(self) -> Dict[str, List[List[int]]]:
        """Create the arguments for the parse function used in pformat method.

        Only return sub-spans and change them to fit the new scope, i.e
        self.string.
        """
        ss, se, _, _ = self._span_data
        if ss == 0 and se == len(self._lststr[0]):
            return deepcopy(self._type_to_spans)
        return {
            type_: [
                [s - ss, e - ss, m, ba[:]] for s, e, m, ba
                in spans[bisect_left(spans, [ss]):] if e <= se
            ] for type_, spans in self._type_to_spans.items()}

    def plain_text(
        self, *,
        replace_templates=True,
        replace_parser_functions=True,
        replace_parameters=True,
        replace_tags=True,
        replace_external_links=True,
        replace_wikilinks=True,
        unescape_html_entities=True,
        replace_bolds_and_italics=True,
        _is_root_node=False
    ) -> str:
        """Return a plain text string representation of self."""
        if _is_root_node is False:
            s, e, m, b = self._span_data
            tts = self._inner_type_to_spans_copy()
            parsed = WikiText([self._lststr[0][s:e]], tts)
            parsed._span_data = tts[self._type][0]
        else:
            tts = self._type_to_spans
            parsed = self
        lst = list(parsed.string)

        def remove(b: int, e: int):
            lst[b:e] = [None] * (e - b)

        for (b, e, _, _) in tts['Comment']:
            remove(b, e)
        if replace_templates:
            for (b, e, _, _) in tts['Template']:
                remove(b, e)
        if replace_parser_functions:
            for (b, e, _, _) in tts['ParserFunction']:
                remove(b, e)
        if replace_external_links:
            for el in parsed.external_links:
                if el.in_brackets:
                    b, e = el.span
                    text = el.text
                    if text is None:
                        remove(b, e)
                    else:
                        remove(b, e - 1 - len(text))
                        remove(e - 1, e)
        # replacing bold and italics should be done before wikilinks and tags
        # because removing tags and wikilinks creates invalid spans, and
        # get_bolds() will try to look into wikilinks for bold parts.
        if replace_bolds_and_italics:
            for i in parsed.get_bolds_and_italics():
                b, e = i.span
                ib, ie = i._match.span(1)  # text span
                remove(b, b + ib)
                remove(b + ie, e)
        if replace_parameters:
            for p in parsed.parameters:
                b, e = p.span
                default_start = p._shadow.find(124)
                if default_start != -1:
                    remove(b, b + default_start + 1)
                    remove(e - 3, e)
                else:
                    remove(b, e)
        if replace_tags:
            for t in parsed.get_tags():
                b, e = t.span
                cb, ce = t._match.span('contents')
                remove(b, b + cb)
                remove(b + ce, e)
        if replace_wikilinks:
            for w in parsed.wikilinks:
                b, e = w.span
                if w.wikilinks:
                    remove(b, e)  # image
                else:
                    tb, te = w._match.span(4)  # text span
                    if tb != -1:
                        remove(b, b + tb)
                        remove(b + te, e)
                    else:
                        tb, te = w._match.span(1)  # target span
                        remove(b, b + tb)
                        remove(b + te, e)
        string = ''.join(c for c in lst if c is not None)
        if unescape_html_entities:
            string = unescape(string)
        return string

    def pformat(self, indent: str = '    ', remove_comments=False) -> str:
        """Return a pretty-print of self.string as string.

        Try to organize templates and parser functions by indenting, aligning
        at the equal signs, and adding space where appropriate.

        Note that this function will not mutate self.
        """
        ws = WS
        # Do not try to do inplace pformat. It will overwrite on some spans.
        lststr0 = self._lststr[0]
        s, e, m, b = self._span_data
        parsed = WikiText([lststr0[s:e]], self._inner_type_to_spans_copy())
        # Since _type_to_spans arg of WikiText has been used, parsed._span
        # is not set yet.
        span = [0, e - s, m, b[:]]
        parsed._span_data = span
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
        for template in reversed(parsed.templates):
            stripped_tl_name = template.name.strip(ws)
            template.name = (
                ' ' + stripped_tl_name + ' '
                if stripped_tl_name[0] == '{' else stripped_tl_name
            )
            args = template.arguments
            if not args:
                continue
            if ':' in stripped_tl_name:
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
                    ' ' * (max_name_len - arg_name_lengths.pop()))
                last_arg.value = (
                    ' ' + last_stripped_value + '\n' + indent * (level - 1))
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
                        last_value.rstrip(ws) + ' ' + last_comment_indent)
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
                        ' ' * (max_name_len - arg_name_len))
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
                        newline_indent + arg.value.strip(ws) + short_indent)
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
        _lststr = self._lststr
        _type_to_spans = self._type_to_spans
        return [
            Parameter(_lststr, _type_to_spans, span, 'Parameter')
            for span in self._subspans('Parameter')]

    @property
    def parser_functions(self) -> List['ParserFunction']:
        """Return a list of parser function objects."""
        _lststr = self._lststr
        _type_to_spans = self._type_to_spans
        return [
            ParserFunction(_lststr, _type_to_spans, span, 'ParserFunction')
            for span in self._subspans('ParserFunction')]

    @property
    def templates(self) -> List['Template']:
        """Return a list of templates as template objects."""
        _lststr = self._lststr
        _type_to_spans = self._type_to_spans
        return [
            Template(_lststr, _type_to_spans, span, 'Template')
            for span in self._subspans('Template')]

    @property
    def wikilinks(self) -> List['WikiLink']:
        """Return a list of wikilink objects."""
        _lststr = self._lststr
        _type_to_spans = self._type_to_spans
        return [
            WikiLink(_lststr, _type_to_spans, span, 'WikiLink')
            for span in self._subspans('WikiLink')]

    @property
    def comments(self) -> List['Comment']:
        """Return a list of comment objects."""
        _lststr = self._lststr
        _type_to_spans = self._type_to_spans
        return [
            Comment(_lststr, _type_to_spans, span, 'Comment')
            for span in self._subspans('Comment')]

    _relative_contents_end = span

    @property
    def _balanced_quotes_shadow(self):
        """Return bold and italic match objects according MW's algorithm.

        The comments at /includes/parser/Parser.php:doQuotes are helpful:
        https://github.com/wikimedia/mediawiki/blob/master/includes/parser/Parser.php
        https://phabricator.wikimedia.org/T15227#178834
        """
        bold_matches = []
        odd_italics = False
        odd_bold_italics = False
        shadow_copy = self._shadow[:]
        append_match = bold_matches.append
        for match in BOLD_ITALIC_FINDITER(shadow_copy):
            if match[4] is not None:  # newline or string end
                if odd_italics is True and (
                        len(bold_matches) + odd_bold_italics) % 2:
                    # one of the bold marks needs to be interpreted as italic
                    first_multi_letter_word = first_space = None
                    for bold_match in bold_matches:
                        bold_start = bold_match.start()
                        if shadow_copy[bold_start - 1:bold_start] == b' ':
                            if first_space is None:
                                first_space = bold_start
                            continue
                        if shadow_copy[bold_start - 2:bold_start - 1] == b' ':
                            shadow_copy[bold_start] = 95  # _
                            break  # first_single_letter_word
                        if first_multi_letter_word is None:
                            first_multi_letter_word = bold_start
                            continue
                    else:  # there was no first_single_letter_word
                        if first_multi_letter_word is not None:
                            shadow_copy[first_multi_letter_word] = 95  # _
                        elif first_space is not None:
                            shadow_copy[first_space] = 95  # _
                bold_matches.clear()
                odd_italics = False
                continue
            if match[2] is None:  # italic
                odd_italics ^= True
                continue
            if match[3] is None:  # bold
                s, e = match.span(1)
                if s != e:  # four apostrophes, hide the first one
                    shadow_copy[s] = 95  # _
                append_match(match)
                continue
            # bold-italic
            s, e = match.span(1)
            es = e - s
            if es:  # more than 5 apostrophes, hide the previous ones
                shadow_copy[s:e] = b'_' * es
            odd_bold_italics ^= True
            odd_italics ^= True
        return shadow_copy

    def _bolds_italics_recurse(self, result: list, filter_cls: Optional[type]):
        for prop in (
                'templates', 'parser_functions', 'parameters', 'wikilinks'):
            for e in getattr(self, prop):
                result += e.get_bolds_and_italics(
                    filter_cls=filter_cls, recursive=False)
        extension_tags = self._extension_tags
        if not extension_tags:
            return result
        # noinspection PyProtectedMember
        result_spans = {(*i._span_data[:2],) for i in result}
        for e in extension_tags:
            for i in e.get_bolds_and_italics(
                    filter_cls=filter_cls, recursive=False):
                # noinspection PyProtectedMember
                if (*i._span_data[:2],) not in result_spans:
                    result.append(i)

    def get_bolds_and_italics(
        self, *, recursive=True, filter_cls: type = None
    ) -> List[Union['Bold', 'Italic']]:
        """Return a list of bold and italic objects in self.

        This is faster than calling ``get_bolds`` and ``get_italics``
        individually.
        :keyword recursive: if True also look inside templates, parser
            functions, extension tags, etc.
        :keyword filter_cls: only return this type. Should be
            `wikitextparser.Bold` or `wikitextparser.Italic`.
            The default is None and means both bolds and italics.
        """
        result = []
        append = result.append
        _lststr = self._lststr
        s = self._span_data[0]
        type_to_spans = self._type_to_spans
        tts_setdefault = type_to_spans.setdefault
        balanced_shadow = self._balanced_quotes_shadow
        rs, re = self._relative_contents_end

        if filter_cls is None or filter_cls is Bold:
            bold_spans = tts_setdefault('Bold', [])
            get_old_bold_span = {(s[0], s[1]): s for s in bold_spans}.get
            bold_matches = list(BOLD_FINDITER(balanced_shadow, rs, re))
            for match in bold_matches:
                ms, me = match.span()
                b, e = s + ms, s + me
                old_span = get_old_bold_span((b, e))
                if old_span is None:
                    span = [b, e, None, balanced_shadow[ms:me]]
                    insort_right(bold_spans, span)
                else:
                    span = old_span
                append(Bold(_lststr, type_to_spans, span, 'Bold'))
            if recursive:
                self._bolds_italics_recurse(result, filter_cls)
                if filter_cls is Bold:
                    result.sort(key=attrgetter('_span_data'))
                    return result
            elif filter_cls is Bold:
                return result
        else:  # filter_cls is Italic
            bold_matches = BOLD_FINDITER(balanced_shadow, rs, re)

        # filter_cls is None or filter_cls is Italic

        # remove bold tokens before searching for italics
        for match in bold_matches:
            ms, me = match.span()
            cs, ce = match.span(1)  # content
            balanced_shadow[ms:cs] = b'_' * (cs - ms)
            balanced_shadow[ce:me] = b'_' * (me - ce)

        italic_spans = tts_setdefault('Italic', [])
        get_old_italic_span = {(s[0], s[1]): s for s in italic_spans}.get
        for match in ITALIC_FINDITER(balanced_shadow, rs, re):
            ms, me = match.span()
            b, e = span = s + ms, s + me
            old_span = get_old_italic_span(span)
            if old_span is None:
                span = [b, e, None, balanced_shadow[ms:me]]
                insort_right(italic_spans, span)
            else:
                span = old_span
            append(Italic(
                _lststr, type_to_spans, span, 'Bold', me != match.end(1)))
        if recursive and filter_cls is Italic:
            self._bolds_italics_recurse(result, filter_cls)
            result.sort(key=attrgetter('_span_data'))
            return result
        if filter_cls is None:  # all Italics are appended after Bolds
            result.sort(key=attrgetter('_span_data'))
        return result

    def get_bolds(self, recursive=True) -> List['Bold']:
        """Return bold parts of self.

        :param recursive: if True also look inside templates, parser functions,
            extension tags, etc.
        """
        return self.get_bolds_and_italics(filter_cls=Bold, recursive=recursive)

    def get_italics(self, recursive=True) -> List['Italic']:
        """Return italic parts of self.

        :param recursive: if True also look inside templates, parser functions,
            extension tags, etc.
        """
        return self.get_bolds_and_italics(
            filter_cls=Italic, recursive=recursive)

    @property
    def external_links(self) -> List['ExternalLink']:
        """Return a list of found external link objects.

        Note:
            Templates adjacent to external links are considered part of the
            link. In reality, this depends on the contents of the template:

            >>> WikiText(
            ...    'http://example.com{{dead link}}'
            ...).external_links[0].url
            'http://example.com{{dead link}}'

            >>> WikiText(
            ...    '[http://example.com{{space template}} text]'
            ...).external_links[0].url
            'http://example.com{{space template}}'
        """
        external_links = []  # type: List['ExternalLink']
        external_links_append = external_links.append
        type_to_spans = self._type_to_spans
        lststr = self._lststr
        ss, se, _, _ = self._span_data
        spans = type_to_spans.setdefault('ExternalLink', [])
        span_tuple_to_span_get = {(s[0], s[1]): s for s in spans}.get
        el_shadow = self._ext_link_shadow

        def _extract(start, end):
            for m in EXTERNAL_LINK_FINDITER(el_shadow, start, end):
                ms, me = m.span()
                span = s, e, _, _ = [ss + ms, ss + me, None, el_shadow[ms:me]]
                old_span = span_tuple_to_span_get((s, e))
                if old_span is None:
                    insort_right(spans, span)
                else:
                    span = old_span
                external_links_append(
                    ExternalLink(lststr, type_to_spans, span, 'ExternalLink'))

        for s, e, _, _ in self._subspans('ExtensionTag'):
            if PARSABLE_TAG_EXTENSIONS_MATCH(el_shadow, s, e):
                _extract(s, e)
            el_shadow[s:e] = (e - s) * b'_'
        _extract(None, None)
        return external_links

    @property
    def sections(self) -> List['Section']:
        """Return self.get_section(include_subsections=True)."""
        return self.get_sections()

    def get_sections(
        self, include_subsections=True, level=None
    ) -> List['Section']:
        """Return a list of sections in current wikitext.

        The first section will always be the lead section, even if it is an
        empty string.

        :param include_subsections: Only return the leading part of each
            section if False.
        :param level: Only return sections where section.level == level.
            Return all levels if None (default).
        """
        sections = []  # type: List['Section']
        sections_append = sections.append
        type_to_spans = self._type_to_spans
        lststr = self._lststr
        ss, se, _, ba = self._span_data
        type_spans = type_to_spans.setdefault('Section', [])
        shadow = self._shadow
        full_match = SECTIONS_FULLMATCH(shadow)
        section_spans = full_match.spans('section')
        levels = [len(eq) for eq in full_match.captures('equals')]
        span_tuple_to_span = {(s[0], s[1]): s for s in type_spans}.get
        for current_index, (current_level, (ms, me)) in enumerate(
            zip(levels, section_spans), 1
        ):
            if level is not None and current_level != level:
                continue
            if include_subsections:
                # Add text of the current_section to any parent section.
                # Note that section 0 is not a parent for any subsection.
                for section_index, section_level in enumerate(
                    levels[current_index:], current_index
                ):
                    if current_level and section_level > current_level:
                        me = section_spans[section_index][1]
                    else:
                        break
            s, e = ss + ms, ss + me
            old_span = span_tuple_to_span((s, e))
            if old_span is None:
                span = [s, e, None, shadow[ms:me]]
                insort_right(type_spans, span)
            else:
                span = old_span
            sections_append(Section(lststr, type_to_spans, span, 'Section'))
        return sections

    @property
    def tables(self) -> List['Table']:
        """Return a list of all tables."""
        return self.get_tables(True)

    def get_tables(self, recursive=False) -> List['Table']:
        """Return tables. Include nested tables if `recursive` is `True`."""
        type_to_spans = self._type_to_spans
        lststr = self._lststr
        shadow_copy = self._shadow[:]
        ss, se, _, _ = self._span_data
        spans = type_to_spans.setdefault('Table', [])
        spans_append = spans.append
        skip_self_span = self._type == 'Table'
        span_tuple_to_span_get = {(s[0], s[1]): s for s in spans}.get
        return_spans = []
        return_spans_append = return_spans.append
        m = True
        shadow_copy_copy = shadow_copy[:]
        while m:
            m = False
            for m in TABLE_FINDITER(shadow_copy, skip_self_span):
                ms, me = m.span()
                # Ignore leading whitespace using len(m[1]).
                s, e = ss + ms, ss + me
                old_span = span_tuple_to_span_get((s, e))
                if old_span is None:
                    span = [s, e, None, shadow_copy_copy[ms:me]]
                    spans_append(span)
                    return_spans_append(span)
                else:
                    return_spans_append(old_span)
                shadow_copy[ms:me] = b'_' * (me - ms)
        return_spans.sort()
        spans.sort()
        if not recursive:
            return_spans = _outer_spans(return_spans)
        return [
            Table(lststr, type_to_spans, sp, 'Table') for sp in return_spans]

    @property
    def _lists_shadow_ss(self) -> Tuple[bytearray, int]:
        """Return appropriate shadow and its offset to be used by `lists`."""
        return self._shadow, self._span_data[0]

    def lists(self, pattern: str = None) -> List['WikiList']:
        """Deprecated, use self.get_lists instead."""
        warn(
            '`lists` method is deprecated, use `get_lists` instead.',
            DeprecationWarning)
        return self.get_lists(pattern)

    def get_lists(
        self, pattern: Union[str, Tuple[str]] = (r'\#', r'\*', '[:;]')
    ) -> List['WikiList']:
        r"""Return a list of WikiList objects.

        :param pattern: The starting pattern for list items.
            If pattern is not None, it will be passed to the regex engine,
            so remember to escape the `*` character. Examples:

                - `'\#'` means top-level ordered lists
                - `'\#\*'` means unordred lists inside an ordered one
                - Currently definition lists are not well supported, but you
                    can use `'[:;]'` as their pattern.

            Tips and tricks:

                Be careful when using the following patterns as they will
                probably cause malfunction in the `sublists` method of the
                resultant List. (However don't worry about them if you are
                not going to use the `sublists` or `List.get_lists` method.)

                - Use `'\*+'` as a pattern and nested unordered lists will be
                    treated as flat.
                - Use `'\*\s*'` as pattern to rtstrip `items` of the list.
        """
        if pattern is None:
            warn('calling get_lists with None pattern is deprecated; '
                 'Use the default value instead.', DeprecationWarning)
            patterns = (r'\#', r'\*', '[:;]')
        elif isinstance(pattern, str):
            patterns = (pattern,)
        else:
            patterns = pattern
        lists = []
        lists_append = lists.append
        lststr = self._lststr
        type_to_spans = self._type_to_spans
        spans = type_to_spans.setdefault('WikiList', [])
        span_tuple_to_span_get = {(s[0], s[1]): s for s in spans}.get
        shadow, ss = self._lists_shadow_ss
        for pattern in patterns:
            for m in finditer(
                LIST_PATTERN_FORMAT.replace(b'{pattern}', pattern.encode(), 1),
                shadow, MULTILINE
            ):
                ms, me = m.span()
                s, e = ss + ms, ss + me
                old_span = span_tuple_to_span_get((s, e))
                if old_span is None:
                    span = [s, e, None, shadow[ms:me]]
                    insort_right(spans, span)
                else:
                    span = old_span
                lists_append(WikiList(
                    lststr, pattern, m, type_to_spans, span, 'WikiList'))
        lists.sort(key=attrgetter('_span_data'))
        return lists

    def tags(self, name=None) -> List['Tag']:
        """Deprecated, use self.get_tags instead."""
        warn(
            '`tags` method is deprecated, use `get_tags` instead.',
            DeprecationWarning)
        return self.get_tags(name)

    @property
    def _extension_tags(self):
        lststr = self._lststr
        type_to_spans = self._type_to_spans
        return [
            Tag(lststr, type_to_spans, span, 'ExtensionTag')
            for span in self._subspans('ExtensionTag')]

    def get_tags(self, name=None) -> List['Tag']:
        """Return all tags with the given name."""
        lststr = self._lststr
        type_to_spans = self._type_to_spans
        if name:
            if name in _tag_extensions:
                string = lststr[0]
                startswith = '<' + name + ' '
                return [
                    Tag(lststr, type_to_spans, span, 'ExtensionTag')
                    for span in type_to_spans['ExtensionTag']
                    if string.startswith(startswith, span[0])]
            tags = []  # type: List['Tag']
        else:
            # There is no name, add all extension tags. Before using shadow.
            tags = self._extension_tags
        tags_append = tags.append
        # Get the left-most start tag, match it to right-most end tag
        # and so on.
        ss = self._span_data[0]
        shadow = self._shadow
        if name:
            # There is a name but it is not in TAG_EXTENSIONS.
            reversed_start_matches = reversed([m for m in regex_compile(
                START_TAG_PATTERN.replace(
                    rb'{name}', rb'(?P<name>' + name.encode() + rb')')
            ).finditer(shadow)])
            end_search = regex_compile(END_TAG_PATTERN.replace(
                b'{name}', name.encode())).search
        else:
            reversed_start_matches = reversed(
                [m for m in NAME_CAPTURING_HTML_START_TAG_FINDITER(shadow)])
        shadow_copy = shadow[:]
        spans = type_to_spans.setdefault('Tag', [])
        span_tuple_to_span_get = {(s[0], s[1]): s for s in spans}.get
        spans_append = spans.append
        for start_match in reversed_start_matches:
            if start_match['self_closing']:
                # Don't look for the end tag
                ms, me = start_match.span()
                span = [ss + ms, ss + me, None, shadow_copy[ms:me]]
            else:
                # look for the end-tag
                sms, sme = start_match.span()
                if name:
                    # the end_search is already available
                    # noinspection PyUnboundLocalVariable
                    end_match = end_search(shadow_copy, sme)
                else:
                    # build end_search according to start tag name
                    end_match = search(
                        END_TAG_PATTERN.replace(
                            b'{name}', start_match['name']),
                        shadow_copy, pos=sme)
                if end_match:
                    ems, eme = end_match.span()
                    shadow_copy[ems:eme] = b'_' * (eme - ems)
                    span = [ss + sms, ss + eme, None, shadow[sms:eme]]
                else:
                    # Assume start-only tag.
                    span = [ss + sms, ss + sme, None, shadow_copy[sms:sme]]
            old_span = span_tuple_to_span_get((span[0], span[1]))
            if old_span is None:
                spans_append(span)
            else:
                span = old_span
            tags_append(Tag(lststr, type_to_spans, span, 'Tag'))
        spans.sort()
        tags.sort(key=attrgetter('_span_data'))
        return tags

    @staticmethod
    def parent(type_: Optional[str] = None) -> Optional['WikiText']:
        """Return None (The parent of the root node is None)."""
        return None

    @staticmethod
    def ancestors(type_: Optional[str] = None) -> list:
        """Return [] (the root node has no ancestors)."""
        return []


class SubWikiText(WikiText):
    """Define a class to be inherited by some subclasses of WikiText.

    Allow to focus on a particular part of WikiText.
    """

    __slots__ = '_type'

    def __init__(
        self,
        string: Union[str, MutableSequence[str]],
        _type_to_spans: Optional[Dict[str, List[List[int]]]] = None,
        _span: Optional[List[int]] = None,
        _type: Optional[Union[str, int]] = None,
    ) -> None:
        """Initialize the object."""
        if _type is None:
            # assert _span is None
            # assert _type_to_spans is None
            self._type = _type = type(self).__name__
            super().__init__(string)
        else:
            # assert _span is not None
            # assert _type_to_spans is not None
            self._type = _type
            super().__init__(string, _type_to_spans)
            self._span_data = _span

    def _subspans(self, _type: str) -> Generator[int, None, None]:
        """Yield all the sub-span indices excluding self._span."""
        ss, se, _, _ = self._span_data
        spans = self._type_to_spans[_type]
        # Do not yield self._span by bisecting for s < ss.
        # The second bisect is an optimization and should be on [se + 1],
        # but empty spans are not desired thus [se] is used.
        b = bisect_left(spans, [ss])
        for span in spans[b:bisect_right(spans, [se], b)]:
            if span[1] <= se:
                yield span

    # noinspection PyProtectedMember
    def ancestors(self, type_: Optional[str] = None) -> List['WikiText']:
        """Return the ancestors of the current node.

        :param type_: the type of the desired ancestors as a string.
            Currently the following types are supported: {Template,
            ParserFunction, WikiLink, Comment, Parameter, ExtensionTag}.
            The default is None and means all the ancestors of any type above.
        """
        if type_ is None:
            types = SPAN_PARSER_TYPES
        else:
            types = type_,
        lststr = self._lststr
        type_to_spans = self._type_to_spans
        ss, se, _, _ = self._span_data
        ancestors = []
        ancestors_append = ancestors.append
        for type_ in types:
            cls = globals()[type_]
            spans = type_to_spans[type_]
            for span in spans[:bisect_right(spans, [ss])]:
                if se < span[1]:
                    ancestors_append(cls(lststr, type_to_spans, span, type_))
        return sorted(ancestors, key=lambda i: ss - i._span_data[0])

    def parent(self, type_: Optional[str] = None) -> Optional['WikiText']:
        """Return the parent node of the current object.

        :param type_: the type of the desired parent object.
            Currently the following types are supported: {Template,
            ParserFunction, WikiLink, Comment, Parameter, ExtensionTag}.
            The default is None and means the first parent, of any type above.
        :return: parent WikiText object or None if no parent with the desired
            `type_` is found.
        """
        ancestors = self.ancestors(type_)
        if ancestors:
            return ancestors[0]
        return None


def _outer_spans(sorted_spans: List[List[int]]) -> Iterable[List[int]]:
    """Yield the outermost intervals."""
    for i, span in enumerate(sorted_spans):
        se = span[1]
        for ps, pe, _, _ in islice(sorted_spans, None, i):
            if se < pe:
                break
        else:  # none of the previous spans included span
            yield span


def remove_markup(s: str, **kwargs) -> str:
    """Return a string with wiki markup removed/replaced."""
    return WikiText(s).plain_text(**kwargs, _is_root_node=True)


plain_text_doc = """

        Comments are always removed.
        :keyword replace_templates: Replace `{{template|argument}}` with ``.
        :keyword replace_parser_functions: Replace `{{#if:a|y|n}}` with ``.
        :keyword replace_parameters: Replace `{{{a}}}` with `` and {{{a|b}}}
            with `b`.
        :keyword replace_tags: Replace `<s>text</s>` with `text`.
        :keyword replace_external_links: Replace `[https://wikimedia.org/ wm]`
            with `wm`, and `[https://wikimedia.org/]` with ``.
        :keyword replace_wikilinks: Replace wikilinks with their text
            representation, e.g. `[[a|b]]` with `b` and `[[a]]` with `a`.
        :keyword unescape_html_entities: Replace HTML entities like `&Sigma;`,
            `&#931;`, and `&#x3a3;` with `Σ`.
        :keyword replace_bolds: replace `'''b'''` with `b`.
        :keyword replace_italics: replace `''i''` with `i`.
"""
WikiText.plain_text.__doc__ += plain_text_doc
remove_markup.__doc__ += plain_text_doc

if __name__ == '__main__':
    # To make PyCharm happy! http://stackoverflow.com/questions/41524090
    from ._tag import Tag
    from ._parser_function import ParserFunction
    from ._template import Template
    from ._wikilink import WikiLink
    from ._comment_bold_italic import Comment, Bold, Italic
    from ._externallink import ExternalLink
    from ._section import Section
    from ._wikilist import WikiList, LIST_PATTERN_FORMAT
    from ._table import Table
    from ._parameter import Parameter
