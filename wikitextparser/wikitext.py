"""Define the Wikitext and SubWikiText classes."""


# Todo: consider using a tree structure (interval or segment tree).
# Todo: Consider using separate strings for each node.

from copy import deepcopy
from typing import (
    MutableSequence, Dict, List, Tuple, Union, Generator, Any, Optional
)

from regex import VERBOSE, DOTALL, MULTILINE, IGNORECASE, search
from regex import compile as regex_compile
from wcwidth import wcswidth

from .spans import (
    parse_to_spans,
    VALID_EXTLINK_CHARS_PATTERN,
    VALID_EXTLINK_SCHEMES_PATTERN,
    BARE_EXTERNALLINK_PATTERN,
    TAG_EXTENSIONS,
    PARSABLE_TAG_EXTENSIONS,
)


# External links
BRACKET_EXTERNALLINK_PATTERN = r'\[%s%s\ *[^\]\n]*\]' % (
    VALID_EXTLINK_SCHEMES_PATTERN, VALID_EXTLINK_CHARS_PATTERN
)
EXTERNALLINK_FINDITER = regex_compile(
    r'(%s|%s)' % (BARE_EXTERNALLINK_PATTERN, BRACKET_EXTERNALLINK_PATTERN),
    IGNORECASE | VERBOSE,
).finditer
# Todo: Perhaps the regular expressions for sections can be improved by using
# the features of the regex module.
# Sections
SECTION_HEADER_PATTERN = r'^=[^\n]+?= *$'
LEAD_SECTION_MATCH = regex_compile(
    r'.*?(?=%s|\Z)' % SECTION_HEADER_PATTERN,
    DOTALL | MULTILINE,
).match
SECTION_FINDITER = regex_compile(
    r'%s.*?\n*(?=%s|\Z)'
    % (SECTION_HEADER_PATTERN, SECTION_HEADER_PATTERN),
    DOTALL | MULTILINE,
).finditer
# Tables
TABLE_FINDITER = regex_compile(
    r"""
    # Table-start
    # Always starts on a new line with optional leading spaces or indentation.
    ^
    # Group the leading spaces or colons so that we can ignore them later.
    ([ :]*)
    {\| # Table contents
    (?:
        # Any character, as long as it is not indicating another table-start
        (?!^\ *\{\|).
    )*?
    # Table-end
    \n\s*
    (?> \|} | \Z )
    """,
    DOTALL | MULTILINE | VERBOSE
).finditer
TAG_EXTENSIONS = set(TAG_EXTENSIONS) | set(PARSABLE_TAG_EXTENSIONS)

# Types which are detected by the
SPAN_PARSER_TYPES = {
    'Template', 'ParserFunction', 'WikiLink', 'Comment', 'Parameter', 'ExtTag'
}


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
        byte_array = bytearray(string.encode('ascii', 'replace'))
        _type = self._type
        if _type not in SPAN_PARSER_TYPES:
            type_to_spans = self._type_to_spans = parse_to_spans(byte_array)
            type_to_spans[_type] = [span]
            self._shadow_cache = string, byte_array.decode()
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
            self._shadow_cache = (string, byte_array.decode())

    def __str__(self) -> str:
        """Return self-object as a string."""
        return self.string

    def __repr__(self) -> str:
        """Return the string representation of self."""
        return '{0}({1})'.format(self.__class__.__name__, repr(self.string))

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

    def __setitem__(self, key: Union[slice, int], value: str) -> None:
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
            bytearray(value.encode('ascii', 'replace'))
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
        self._shrink_span_update(
            rmstart=start,
            rmstop=stop,
        )

    # Todo: def __add__(self, other) and __radd__(self, other)

    def insert(self, index: int, string: str) -> None:
        """Insert the given string before the specified index.

        This method has the same effect as ``self[index:index] = string``;
        it only avoids some condition checks as it rules out the possibility
        of the key being an slice, or the need to shrink any of the sub-spans.

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
            bytearray(string.encode('ascii', 'replace'))
        ).items():
            spans_append = spans_dict[k].append
            for s, e in v:
                spans_append([s + index, e + index])

    @property
    def string(self) -> str:
        """Return str(self)."""
        start, end = self._span
        return self._lststr[0][start:end]

    @string.setter
    def string(self, newstring: str) -> None:
        """Set a new string for this object. Note the old data will be lost."""
        self[:] = newstring

    def _atomic_partition(self, char: str) -> Tuple[str, str, str]:
        """Partition self.string where `char`'s not in atomic sub-spans."""
        s, e = self._span
        index = self._shadow.find(char)
        if index == -1:
            return self._lststr[0][s:e], '', ''
        lststr0 = self._lststr[0]
        return lststr0[s:s + index], char, lststr0[s + index + 1:e]

    def _gen_subspans(self, type_: str) -> List[int]:
        """Yield all the sub-span including self._span."""
        s, e = self._span
        for span in self._type_to_spans[type_]:
            ss, se = span
            # Include self._span
            if s <= ss and se <= e:
                yield span

    def _close_subspans(self, start: int, stop: int) -> None:
        """Close all subspans of (start, stop)."""
        ss, se = self._span
        for type_spans in self._type_to_spans.values():
            for span in type_spans:
                s, e = span
                if (start <= s and e <= stop) and (ss != s or se != e):
                    # Todo: Only one point needs to be -1.
                    span[0] = span[1] = -1

    def _shrink_span_update(self, rmstart: int, rmstop: int) -> None:
        """Update self._type_to_spans according to the removed span.

        Warning: If an operation involves both _shrink_span_update and
        _extend_span_update, you might wanna consider doing the
        _extend_span_update before the _shrink_span_update as this function
        can cause data loss in self._type_to_spans.

        """
        # Note: No span should be removed from _type_to_spans.
        rmlength = rmstop - rmstart
        for t, spans in self._type_to_spans.items():
            for span in spans:
                s, e = span
                if e <= rmstart:
                    # s <= e <= rmstart <= rmstop
                    continue
                if rmstop <= s:
                    # rmstart <= rmstop <= s <= e
                    span[0] = s - rmlength
                    span[1] = e - rmlength
                    continue
                if rmstart <= s:
                    # s needs to be changed.
                    # We already know that rmstop is after the s,
                    # therefore the new s should be located at rmstart.
                    if rmstop >= e:
                        # rmstart <= s <= e < rmstop
                        span[0] = span[1] = -1
                        continue
                    # rmstart < s <= rmstop <= e
                    span[0] = rmstart
                    span[1] = e - rmlength
                    continue
                # From the previous comparison we know that s is before
                # the rmstart; so s needs no change.
                if rmstop < e:
                    # s <= rmstart <= rmstop <= e
                    span[1] = e - rmlength
                else:
                    # s <= rmstart <= e < rmstop
                    span[1] = rmstart

    def _extend_span_update(self, estart: int, elength: int) -> None:
        """Update self._type_to_spans according to the added span."""
        # Note: No span should be removed from _type_to_spans.
        ss, se = self._span
        for spans in self._type_to_spans.values():
            for span in spans:
                s, e = span
                if estart < s or (
                    # Not at the beginning of selfspan
                    estart == s != ss and e != se
                ):
                    # Added part is before the span
                    span[0] = s + elength
                    span[1] = e + elength
                elif s < estart < e or (
                    # At the end of selfspan
                    estart == s == ss and e == se
                ) or (
                    estart == e == se and s == ss
                ):
                    # Added part is inside the span
                    span[1] = e + elength

    @property
    def _indent_level(self) -> int:
        """Calculate the indent level for self.pprint function.

        Minimum returned value for templates and parser functions is 1.
        Being part of any Template or ParserFunction increases the indent
        level by one.

        """
        ss, se = self._span
        level = 1  # a template is always found in itself
        for s, e in self._type_to_spans['Template']:
            if s < ss and se < e:
                level += 1
        for s, e in self._type_to_spans['ParserFunction']:
            if s < ss and se < e:
                level += 1
        return level

    @property
    def _shadow(self) -> str:
        """Return a copy of self.string with specific sub-spans replaced.

        Subspans are replaced by a block of spaces of the same size.

        The replaced subspans are:
            ('Template', 'WikiLink', 'ParserFunction', 'ExtTag', 'Comment',)

        This function is called upon extracting tables or extracting the data
        inside them.

        """
        ss, se = self._span
        string = self._lststr[0][ss:se]
        cached_string, cached_shadow = getattr(
            self, '_shadow_cache', (None, None)
        )
        if cached_string == string:
            return cached_shadow
        # In the old method the existing spans were used to create the shadow.
        # But it was slow because there can be thousands of spans and iterating
        # over them to find the relevant sub-spans could take a significant
        # amount of time. The new method tries to parse the self.string which
        # is usually much more faster because there are usually far less
        # sub-spans for individual objects.
        shadow = bytearray(string.encode('ascii', 'replace'))
        if self._type in SPAN_PARSER_TYPES:
            head = shadow[:2]
            tail = shadow[-2:]
            shadow[:2] = shadow[-2:] = b'__'
            parse_to_spans(shadow)
            shadow[:2] = head
            shadow[-2:] = tail
        else:
            parse_to_spans(shadow)
        shadow = shadow.decode()
        self._shadow_cache = (string, shadow)
        return shadow

    def _pp_type_to_spans(self) -> dict:
        """Create the arguments for the parse function used in pprint method.


        Only pass the spans of subspans and change the spans to fit the new
        scope, i.e self.string.

        """
        ss, se = self._span
        if ss == 0 and se == len(self._lststr[0]):
            return deepcopy(self._type_to_spans)
        type_to_spans = {}  # type: Dict[str, List[List[int, int]]]
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

    def pprint(self, indent: str='    ', remove_comments=False) -> str:
        """Return a pretty-print of self.string as string.

        Try to organize templates and parser functions by indenting, aligning
        at the equal signs, and adding space where appropriate.

        Note that this function will not mutate self.

        """
        # Do not try to do inplace pprint. It will overwrite on some spans.
        string = self.string
        parsed = WikiText([string], self._pp_type_to_spans())
        span = [0, len(string)]
        parsed._span = span
        parsed._type_to_spans['WikiText'] = [span]
        if remove_comments:
            for c in parsed.comments:
                c.string = ''
        else:
            # Only remove comments that contain whitespace.
            for c in parsed.comments:
                if not c.contents.strip():
                    c.string = ''
        # First remove all current spacings.
        for template in parsed.templates:
            template_name = template.name.strip()
            template.name = template_name
            if ':' in template_name:
                # Don't use False because we don't know for sure.
                not_a_parser_function = None
            else:
                not_a_parser_function = True
            args = template.arguments
            if not args:
                continue
            # Required for alignment
            arg_stripped_names = [a.name.strip() for a in args]
            arg_positionalities = [a.positional for a in args]
            arg_name_lengths = [
                wcswidth(n.replace('لا', 'ل')) if
                not arg_positionalities[i] else 0 for
                i, n in enumerate(arg_stripped_names)
            ]
            max_name_len = max(arg_name_lengths)
            # Format template.name.
            level = template._indent_level
            newline_indent = '\n' + indent * level
            if level == 1:
                last_comment_indent = '<!--\n' + indent * (level - 1) + '-->'
            else:
                last_comment_indent = '<!--\n' + indent * (level - 2) + ' -->'
            template.name += newline_indent
            # Special formatting for the last argument.
            last_arg = args.pop()
            last_is_positional = arg_positionalities.pop()
            last_arg_stripped_name = arg_stripped_names.pop()
            last_arg_value = last_arg.value
            last_arg_stripped_value = last_arg_value.strip()
            if (
                not last_is_positional or
                last_arg_value == last_arg_stripped_value
            ):
                if not_a_parser_function:
                    stop_conversion = False
                    last_arg.name = (
                        ' ' + last_arg_stripped_name + ' ' +
                        ' ' * (max_name_len - arg_name_lengths.pop())
                    )
                    last_arg.value = (
                        ' ' + last_arg_stripped_value + '\n' +
                        indent * (level - 1)
                    )
                else:
                    stop_conversion = True
                    if last_is_positional:
                        # Can't strip or adjust the position of the value
                        # because this could be a positional argument in a
                        # template.
                        last_arg.value = (
                            last_arg_value + last_comment_indent
                        )
                    else:
                        # This is either a parser function or a keyword
                        # argument in a template. In both cases the name
                        # can be lstripped and the value can be rstripped.
                        last_arg.name = ' ' + last_arg.name.lstrip()
                        last_arg.value = (
                            last_arg_value.rstrip() + ' ' + last_comment_indent
                        )
            else:
                stop_conversion = True
                last_arg.value += last_comment_indent
            if not args:
                continue
            comment_indent = '<!--\n' + indent * (level - 1) + ' -->'
            for i, arg in enumerate(reversed(args)):
                i = -i - 1
                stripped_name = arg_stripped_names[i]
                positional = arg_positionalities[i]
                value = arg.value
                stripped_value = value.strip()
                # Positional arguments of templates are sensitive to
                # whitespace. See:
                # https://meta.wikimedia.org/wiki/Help:Newlines_and_spaces
                if not stop_conversion:
                    if not positional or value == stripped_value:
                        if not_a_parser_function:
                            arg.name = (
                                ' ' + stripped_name + ' ' +
                                ' ' * (max_name_len - arg_name_lengths[i])
                            )
                            arg.value = (
                                ' ' + stripped_value + newline_indent
                            )
                    else:
                        stop_conversion = True
                        arg.value += comment_indent
                else:
                    arg.value += comment_indent
        i = 0
        functions = parsed.parser_functions
        while i < len(functions):
            func = functions[i]
            i += 1
            name = func.name.lstrip()
            if name.lower() in ('#tag', '#invoke', ''):
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
            level = func._indent_level
            newline_indent = '\n' + indent * level
            if len(args) == 1:
                arg = args[0]
                # The first arg is both the first and last argument.
                if arg.positional:
                    arg.value = (
                        newline_indent + arg.value.strip() +
                        newline_indent.replace(indent, '', 1)
                    )
                else:
                    # Note that we don't add spaces before and after the
                    # '=' in parser functions because it could be part of
                    # an ordinary string.
                    arg.name = newline_indent + arg.name.lstrip()
                    arg.value = (
                        arg.value.rstrip() +
                        newline_indent.replace(indent, '', 1)
                    )
            else:
                # Special formatting for the first argument
                arg = args[0]
                if arg.positional:
                    arg.value = (
                        newline_indent + arg.value.strip() + newline_indent
                    )
                else:
                    arg.name = newline_indent + arg.name.lstrip()
                    arg.value = arg.value.rstrip() + newline_indent
                # Formatting the middle arguments
                for arg in args[1:-1]:
                    if arg.positional:
                        arg.value = (
                            ' ' + arg.value.strip() + newline_indent
                        )
                    else:
                        arg.name = ' ' + arg.name.lstrip()
                        arg.value = (
                            arg.value.rstrip() + newline_indent
                        )
                # Special formatting for the last argument
                arg = args[-1]
                newline_indent = newline_indent.replace(indent, '', 1)
                if arg.positional:
                    arg.value = (
                        ' ' + arg.value.strip() + newline_indent
                    )
                else:
                    arg.name = ' ' + arg.name.lstrip()
                    arg.value = arg.value.rstrip() + newline_indent
            functions = parsed.parser_functions
        return parsed.string

    # Todo: Isn't it better to add a generator for the following properties?
    @property
    def parameters(self) -> List['Parameter']:
        """Return a list of parameter objects."""
        return [
            Parameter(
                self._lststr,
                self._type_to_spans,
                index,
            ) for index in self._gen_subspans('Parameter')
        ]

    @property
    def parser_functions(self) -> List['ParserFunction']:
        """Return a list of parser function objects."""
        return [
            ParserFunction(
                self._lststr,
                self._type_to_spans,
                index,
            ) for index in self._gen_subspans('ParserFunction')
        ]

    @property
    def templates(self) -> List['Template']:
        """Return a list of templates as template objects."""
        return [
            Template(
                self._lststr,
                self._type_to_spans,
                span,
            ) for span in self._gen_subspans('Template')
        ]

    @property
    def wikilinks(self) -> List['WikiLink']:
        """Return a list of wikilink objects."""
        return [
            WikiLink(
                self._lststr,
                self._type_to_spans,
                span,
            ) for span in self._gen_subspans('WikiLink')
        ]

    @property
    def comments(self) -> List['Comment']:
        """Return a list of comment objects."""
        return [
            Comment(
                self._lststr,
                self._type_to_spans,
                span,
            ) for span in self._gen_subspans('Comment')
        ]

    @property
    def external_links(self) -> List['ExternalLink']:
        """Return a list of found external link objects."""
        external_links = []  # type: List['ExternalLink']
        external_links_append = external_links.append
        type_to_spans = self._type_to_spans
        lststr = self._lststr
        ss, se = self._span
        spans = type_to_spans.setdefault('ExternalLink', [])
        spans_append = spans.append
        if not spans:
            # All the added spans will be new.
            for m in EXTERNALLINK_FINDITER(self.string):
                span = m.span()
                span = [span[0] + ss, span[1] + ss]
                spans_append(span)
                external_links_append(
                    ExternalLink(lststr, type_to_spans, span)
                )
            return external_links
        # There are already some ExternalLink spans. Use the already existing
        # ones when the detected span is one of those.
        spanstr_to_span_get = {str(s): s for s in spans}.get
        for m in EXTERNALLINK_FINDITER(self.string):
            s, e = m.span()
            span = [s + ss, e + ss]
            old_span = spanstr_to_span_get(str(span))
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
        string = self.string
        section_spans = type_to_spans.setdefault('Section', [])
        spans_append = section_spans.append
        if not section_spans:
            # All the added spans will be new.
            # Lead section
            s, e = LEAD_SECTION_MATCH(string).span()
            span = [ss + s, ss + e]
            spans_append(span)
            sections_append(Section(lststr, type_to_spans, span))
            # Other sections
            for m in SECTION_FINDITER(string):
                s, e = m.span()
                span = [s + ss, e + ss]
                spans_append(span)
                current_section = Section(lststr, type_to_spans, span)
                # Add text of the current_section to any parent section.
                # Note that section 0 is not a parent for any subsection.
                current_level = current_section.level
                for section in reversed(sections[1:]):
                    section_level = section.level
                    if section_level < current_level:
                        section._span[1] = span[1]
                        current_level = section_level
                sections_append(current_section)
            return sections
        # There are already some spans. Instead of appending new spans
        # use them when the detected span already exists.
        spanstr_to_span_get = {str(s): s for s in section_spans}.get
        # Lead section
        s, e = LEAD_SECTION_MATCH(string).span()
        span = [s + ss, e + ss]
        old_span = spanstr_to_span_get(str(span))
        if old_span is None:
            spans_append(span)
        else:
            span = old_span
        sections_append(
            Section(lststr, type_to_spans, span)
        )
        # Adjust other sections
        for m in SECTION_FINDITER(string):
            s, e = m.span()
            span = [s + ss, e + ss]
            old_span = spanstr_to_span_get(str(span))
            if old_span is None:
                spans_append(span)
            else:
                span = old_span
            current_section = Section(lststr, type_to_spans, span)
            # Add text of the current_section to any parent section.
            # Note that section 0 is not a parent for any subsection.
            current_level = current_section.level
            for section in reversed(sections[1:]):
                section_level = section.level
                if section_level < current_level:
                    section._span[1] = span[1]
                    current_level = section_level
            sections_append(current_section)
        return sections

    @property
    def tables(self) -> List['Table']:
        """Return a list of found table objects."""
        tables = []  # type: List['Table']
        tables_append = tables.append
        type_to_spans = self._type_to_spans
        lststr = self._lststr
        shadow = self._shadow
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
                    shadow = shadow[:ms] + '_' * (me - ms) + shadow[me:]
            return tables
        # There are already exists some spans. Try to use the already existing
        # before appending new spans.
        spanstr_to_span_get = {str(s): s for s in spans}.get
        m = True
        while m:
            m = False
            for m in TABLE_FINDITER(shadow):
                ms, me = m.span()
                # Ignore leading whitespace using len(m[1]).
                span = [ss + ms + len(m[1]), ss + me]
                old_span = spanstr_to_span_get(str(span))
                if old_span is None:
                    spans.append(span)
                else:
                    span = old_span
                tables_append(Table(lststr, type_to_spans, span))
                shadow = shadow[:ms] + '_' * (me - ms) + shadow[me:]
        return tables

    def lists(self, pattern: str=None) -> List['WikiList']:
        """Return a list of WikiList objects.

        :pattern: The starting pattern for list items.
            Return all types of lists (ol, ul, and dl) if pattern is None.
            If pattern is not None, it will be passed to the regex engine with
            VERBOSE flag on, so `#` and `*` should be escaped. Examples:

                - `\#` means top-level ordered lists
                - `\#\*` means unordred lists inside an ordered one
                - Currently definition lists are not well supported, but you
                    can use `[:;]` as their pattern.

            Tips and tricks:

                Be careful when using the following patterns as they will
                probably cause malfunction in the `sublists` method of the
                resultant List. (However they should be safe to use if you are
                not going to use the `sublists` method.)

                - Use `\*+` as a pattern and nested unordered lists will be
                    treated as flat.
                - Use `\*\s*` as pattern to rtstrip `items` of the list.

                Although this parameter is optional, but specifying it can
                improve the performance.

        """
        lists = []
        lststr = self._lststr
        type_to_spans = self._type_to_spans
        spans = type_to_spans.setdefault('WikiList', [])
        spans_append = spans.append
        spanstr_to_span_get = {str(s): s for s in spans}.get
        patterns = ('\#', '\*', '[:;]') if pattern is None \
            else (pattern,)  # type: Tuple[str, ...]
        for pattern in patterns:
            list_regex = regex_compile(
                LIST_PATTERN_FORMAT(pattern=pattern),
                MULTILINE | VERBOSE,
            )
            ss = self._span[0]
            for m in list_regex.finditer(self._shadow):
                ms, me = m.span()
                span = [ss + ms, ss + me]
                old_span = spanstr_to_span_get(str(span))
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
            if name in TAG_EXTENSIONS:
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
        shadow_bytearray = bytearray(shadow.encode('ascii'))
        if name:
            # There is a name but it is not in TAG_EXTENSIONS.
            name_pattern = r'(?P<name>' + name + ')'
            reversed_start_matches = reversed([m for m in regex_compile(
                START_TAG_PATTERN.format(name=name_pattern), VERBOSE
            ).finditer(shadow)])
            end_search = regex_compile(END_TAG_BYTES_PATTERN .replace(
                b'%(name)s', name.encode()
            )).search
        else:
            reversed_start_matches = reversed(
                [m for m in START_TAG_FINDITER(shadow)]
            )
        spans = type_to_spans.setdefault('Tag', [])
        spanstr_to_span_get = {str(s): s for s in spans}.get
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
                    end_match = end_search(shadow_bytearray, start_match.end())
                else:
                    # build end_search according to start tag name
                    end_match = search(
                        END_TAG_BYTES_PATTERN.replace(
                            b'%(name)s', start_match['name'].encode()
                        ),
                        shadow_bytearray,
                    )
                if end_match:
                    s, e = end_match.span()
                    shadow_bytearray[s:e] = b'_' * (e - s)
                    span = [ss + start_match.start(), ss + e]
                else:
                    # Assume start-only tag.
                    s, e = start_match.span()
                    span = [ss + s, ss + e]
            old_span = spanstr_to_span_get(str(span))
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
        _type: Optional[str]=None,
    ) -> None:
        """Initialize the object.

        Run self._common_init.
        Set self._span

        """
        _type = _type or self.__class__.__name__
        self._type = _type

        super().__init__(string, _type_to_spans)

        # _type_to_spans and _span are either both None or not None.
        if _type_to_spans is None and _type not in SPAN_PARSER_TYPES:
            _type_to_spans= self._type_to_spans
            span = [0, len(string)]
            _type_to_spans[_type] = [span]
            self._span = span
        else:
            self._span = \
                self._type_to_spans[_type][-1] if _span is None else _span

    def _gen_subspans(
        self, _type: str=None
    ) -> Generator[int, None, None]:
        """Yield all the sub-span indices excluding self._span."""
        s, e = self._span
        for span in self._type_to_spans[_type]:
            # Do not yield self._span.
            ss, se = span
            if s < ss and se <= e:
                yield span


if __name__ == '__main__':
    # To make PyCharm happy! http://stackoverflow.com/questions/41524090
    from .tag import (
        Tag, START_TAG_PATTERN, END_TAG_BYTES_PATTERN, START_TAG_FINDITER
    )
    from .parser_function import ParserFunction
    from .template import Template
    from .wikilink import WikiLink
    from .comment import Comment
    from .externallink import ExternalLink
    from .section import Section
    from .wikilist import WikiList, LIST_PATTERN_FORMAT
    from .table import Table
    from .parameter import Parameter
