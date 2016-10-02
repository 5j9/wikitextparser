"""Define the Wikitext and _Indexed_WikiText classes."""


import re
from difflib import SequenceMatcher

from wcwidth import wcswidth

from .spans import (
    parse_to_spans,
    VALID_EXTLINK_CHARS_PATTERN,
    VALID_EXTLINK_SCHEMES_PATTERN,
    BARE_EXTERNALLINK_PATTERN
)


# HTML
HTML_TAG_REGEX = re.compile(
    r'<([A-Z][A-Z0-9]*)\b[^>]*>(.*?)</\1>',
    re.DOTALL | re.IGNORECASE,
)
# External links
BRACKET_EXTERNALLINK_PATTERN = (
    r'\[' + VALID_EXTLINK_SCHEMES_PATTERN + VALID_EXTLINK_CHARS_PATTERN +
    r' *[^\]\n]*\]'
)
EXTERNALLINK_REGEX = re.compile(
    r'(' + BARE_EXTERNALLINK_PATTERN + r'|' +
    BRACKET_EXTERNALLINK_PATTERN + r')',
    re.IGNORECASE,
)
# Sections
SECTION_HEADER_REGEX = re.compile(r'^=[^\n]+?= *$', re.M)
LEAD_SECTION_REGEX = re.compile(
    r'.*?(?=' + SECTION_HEADER_REGEX.pattern + r'|\Z)',
    re.DOTALL | re.MULTILINE,
)
SECTION_REGEX = re.compile(
    SECTION_HEADER_REGEX.pattern + r'.*?\n*(?=' +
    SECTION_HEADER_REGEX.pattern + '|\Z)',
    re.DOTALL | re.MULTILINE,
)
# Tables
TABLE_REGEX = re.compile(
    r"""
    # Table-start
    # Always starts on a new line with optional leading spaces
    ^ # Group the leading spaces so we can ignore them in code
    (\ *)
    {\| # Table contents
    # Should not contain any other table-start
    (?:
      (?!^\ *\{\|)
      .
    )*?
    # Table-end
    \n\s*
    (?:\|}|\Z)
    """,
    re.DOTALL | re.MULTILINE | re.VERBOSE
)


class Temporary:

    """A temporary class to avoid circular dependent imports.

    All variables defined using this class will be over-written inside
     wikitextparser.py.

    """

    pass


class WikiText:

    """The WikiText class."""

    def __init__(
            self,
            string: str,
            spans: list or None=None,
    ) -> None:
        """Initialize the object."""
        self._common_init(string, spans)

    def __str__(self) -> str:
        """Return self-object as a string."""
        return self.string

    def __repr__(self) -> str:
        """Return the string representation of the WikiText."""
        return 'WikiText(' + repr(self.string) + ')'

    def __contains__(self, parsed_wikitext) -> bool:
        """Return True if parsed_wikitext is inside self. False otherwise.

        Also self and parsed_wikitext should belong to the same parsed
        wikitext object for this function to return True.

        """
        # Is it usefull (and a good practice) to also accepts str inputs
        # and check if self.string contains it?
        if self._lststr is not parsed_wikitext._lststr:
            return False
        ps, pe = parsed_wikitext._get_span()
        ss, se = self._get_span()
        if ss <= ps and se >= pe:
            return True
        return False

    @property
    def string(self) -> str:
        """Return str(self)."""
        start, end = self._get_span()
        return self._lststr[0][start:end]

    @string.setter
    def string(self, newstring: str) -> None:
        """Set a new string for this object. Update spans accordingly.

        This method can be slow because it uses SequenceMatcher to
        find-out the exact position of each change occured in the
        newstring.

        It tries to avoid the SequenceMatcher by checking to see if the
        newnewstring is a simple concatination at the start or end of the
        oldstring. For long strings, it's highly recommended to use this
        feature and avoid inserting in the middle of the string.

        """
        lststr = self._lststr
        lststr0 = lststr[0]
        oldstart, oldend = self._get_span()
        oldstring = lststr0[oldstart:oldend]
        # Updating lststr
        lststr[0] = lststr0[:oldstart] + newstring + lststr0[oldend:]
        # Updating spans
        oldlength = oldend - oldstart
        newlength = len(newstring)
        if oldlength == newlength and newstring == oldstring:
            return
        elif oldlength < newlength:
            if newstring.startswith(oldstring):
                # The has been an insertion at the end of oldstring.
                self._extend_span_update(
                    estart=oldstart + oldlength,
                    elength=newlength - oldlength,
                )
                return
            if newstring.endswith(oldstring):
                # The has been an insertion at the beggining of oldstring.
                self._extend_span_update(
                    estart=oldstart,
                    elength=newlength - oldlength,
                )
                return
        else:  # oldlength > newlength
            if oldstring.startswith(newstring):
                # The ending part of oldstring has been deleted.
                self._shrink_span_update(
                    rmstart=oldstart + newlength,
                    rmend=oldstart + oldlength,
                )
                return
            if oldstring.endswith(newstring):
                # The starting part of oldstring has been deleted.
                self._shrink_span_update(
                    rmstart=oldstart,
                    rmend=oldstart + oldlength - newlength,
                )
                return
        sm = SequenceMatcher(None, oldstring, newstring, autojunk=False)
        opcodes = [oc for oc in sm.get_opcodes() if oc[0] != 'equal']
        # Opcodes also need adjustment as the spans change.
        opcodes_spans = [
            (oldstart + i, oldstart + j)
            for o in opcodes
            for i in o[1::4] for j in o[2::4]
        ]
        self._spans['opcodes'] = opcodes_spans
        for tag, i1, i2, j1, j2 in opcodes:
            i1, i2 = opcodes_spans.pop(0)
            i1 -= oldstart
            i2 -= oldstart
            if tag == 'replace':
                # a[i1:i2] should be replaced by b[j1:j2].
                len1 = i2 - i1
                len2 = j2 - j1
                if len2 < len1:
                    self._shrink_span_update(
                        rmstart=oldstart + i1 + len2,
                        rmend=oldstart + i2,
                    )
                elif len2 > len1:
                    self._extend_span_update(
                        estart=oldstart + i2,
                        elength=len2 - len1,
                    )
            elif tag == 'delete':
                # a[i1:i2] should be deleted.
                # Note that j1 == j2 in this case.
                self._shrink_span_update(
                    rmstart=oldstart + i1,
                    rmend=oldstart + i2,
                )
            elif tag == 'insert':
                # b[j1:j2] should be inserted at a[i1:i1].
                # Note that i1 == i2 in this case.
                self._extend_span_update(
                    estart=oldstart + i2,
                    elength=j2 - j1,
                )
        del self._spans['opcodes']

    def strdel(self, start: int, end: int) -> None:
        """Remove the given range from self.string.

        0 <= start <= end

        If an operation includes both insertion and deletion. It's safer to
        use the `strins` function first. Otherwise there is a possibility
        of insertion in the wrong spans.

        """
        lststr = self._lststr
        lststr0 = lststr[0]
        ss = self._get_span()[0]
        end += ss
        start += ss
        # Update lststr
        lststr[0] = lststr0[:start] + lststr0[end:]
        # Update spans
        self._shrink_span_update(
            rmstart=start,
            rmend=end,
        )

    def _get_span(self) -> tuple:
        """Return the self-span."""
        return 0, len(self._lststr[0])

    def _not_in_subspans_split(self, char: str) -> list:
        """Split self.string using `char` unless char is in self._spans."""
        # not used
        ss, se = self._get_span()
        string = self._lststr[0][ss:se]
        splits = []
        findstart = 0
        in_spans = self._in_subspans_factory()
        while True:
            index = string.find(char, findstart)
            while in_spans(ss + index):
                index = string.find(char, index + 1)
            if index == -1:
                return splits + [string[findstart:]]
            splits.append(string[findstart:index])
            findstart = index + 1

    def _not_in_subspans_partition(self, char: str) -> tuple:
        """Partition self.string using `char` unless char is in self._spans."""
        ss, se = self._get_span()
        string = self._lststr[0][ss:se]
        findstart = 0
        in_spans = self._in_subspans_factory()
        index = string.find(char, findstart)
        while in_spans(ss + index):
            index = string.find(char, index + 1)
        if index == -1:
            return string, '', ''
        return string[:index], char, string[index + 1:]

    def _not_in_subspans_split_spans(self, char: str) -> list:
        """Like _not_in_subspans_split but return spans."""
        ss, se = self._get_span()
        string = self._lststr[0][ss:se]
        results = []
        findstart = 0
        in_spans = self._in_subspans_factory()
        while True:
            index = string.find(char, findstart)
            while in_spans(ss + index):
                index = string.find(char, index + 1)
            if index == -1:
                return results + [(ss + findstart, se)]
            results.append((ss + findstart, ss + index))
            findstart = index + 1

    def _in_subspans_factory(
        self, ss: int or None=None, se: int or None=None
    ):
        """Return a function that can tell if an index is in subspans.

        `ss` and `se` indicate the spanstart and spanend that subspans will
            be checked for. If not specified, use self._get_span().

        Checked subspans types are:
        (
            'templates', 'parameters', 'functions',
            'wikilinks', 'comments', 'exttags'
        ).

        """
        # Calculate subspans
        if ss is None:
            ss, se = self._get_span()
        subspans = []
        spans = self._spans
        for key in (
            'templates', 'parameters', 'functions',
            'wikilinks', 'comments', 'exttags'
        ):
            for span in spans[key]:
                if ss < span[0] and span[1] <= se:
                    subspans.append(span)

        # Define the function to be returned.
        def index_in_spans(index):
            """Return True if the given index is found within a subspans."""
            for ss, se in subspans:
                if ss <= index < se:
                    return True
            return False

        return index_in_spans

    def _gen_subspan_indices(self, type_: str):
        """Yield all the subspan indices including self._get_span()"""
        s, e = self._get_span()
        for i, (ss, ee) in enumerate(self._spans[type_]):
            # Include self._get_span()
            if s <= ss and ee <= e:
                yield i

    def _close_subspans(self, start: int, end: int) -> None:
        """Close all subspans of (start, end)."""
        ss, se = self._get_span()
        for type_spans in self._spans.values():
            for i, (s, e) in enumerate(type_spans):
                if (
                    (start <= s and e < end) or
                    (start < s and e <= end) or
                    (start == s and e == end and (ss != s or se != e))
                ):
                    type_spans[i] = (start, start)

    def _shrink_span_update(self, rmstart: int, rmend: int) -> None:
        """Update self._spans according to the removed span.

        Warning: If an operation involves both _shrink_span_update and
        _extend_span_update, you might wanna consider doing the
        _extend_span_update before the _shrink_span_update as this function
        can cause data loss in self._spans.

        """
        # Note: No span should be removed from _spans.
        rmlength = rmend - rmstart
        for t, spans in self._spans.items():
            for i, (spanstart, spanend) in enumerate(spans):
                if spanend <= rmstart:
                    continue
                elif rmend <= spanstart:
                    # removed part is before the span
                    spans[i] = (spanstart - rmlength, spanend - rmlength)
                elif rmstart < spanstart:
                    # spanstart needs to be changed
                    # we already know that rmend is after the spanstart
                    # so the new spanstart should be located at rmstart
                    if rmend <= spanend:
                        spans[i] = (rmstart, spanend - rmlength)
                    else:
                        # Shrink to an empty string.
                        spans[i] = (rmstart, rmstart)
                else:
                    # we already know that spanstart is before the rmstart
                    # so the spanstart needs no change.
                    if rmend <= spanend:
                        spans[i] = (spanstart, spanend - rmlength)
                    else:
                        spans[i] = (spanstart, rmstart)

    def _extend_span_update(self, estart: int, elength: int) -> None:
        """Update self._spans according to the added span."""
        # Note: No span should be removed from _spans.
        ss, se = self._get_span()
        for spans in self._spans.values():
            for i, (spanstart, spanend) in enumerate(spans):
                if estart < spanstart or (
                    # Not at the beginning of selfspan
                    estart == spanstart and spanstart != ss and spanend != se
                ):
                    # Added part is before the span
                    spans[i] = (spanstart + elength, spanend + elength)
                elif spanstart < estart < spanend or (
                    # At the end of selfspan
                    estart == spanstart and spanstart == ss and spanend == se
                ) or (
                    estart == spanend and spanend == se and spanstart == ss
                ):
                    # Added part is inside the span
                    spans[i] = (spanstart, spanend + elength)

    def _get_indent_level(self, with_respect_to=None) -> int:
        """Calculate the indent level for self.pprint function.

        Minimum returned value is 1.
        Being part of any Template or Parserfunction increases the indent level
        by one.

        `with_respect_to` is an instance of WikiText object.

        """
        ss, se = self._get_span()
        level = 1  # a template is always found in itself
        if with_respect_to is None:
            for s, e in self._spans['templates']:
                if s < ss and se < e:
                    level += 1
            for s, e in self._spans['functions']:
                if s < ss and se < e:
                    level += 1
            return level
        else:
            rs, re = with_respect_to._get_span()
            for s, e in self._spans['templates']:
                if rs <= s < ss and se < e <= re:
                    level += 1
            for s, e in self._spans['functions']:
                if rs <= s < ss and se < e <= re:
                    level += 1
            return level

    def _shadow(
        self,
        types=('templates', 'wikilinks', 'functions', 'exttags', 'comments')
    ) -> str:
        """Return a copy of self.string with specified subspans replaced.

        This function is used in finding the spans of wikitables.

        """
        ss, se = self._get_span()
        shadow = self.string
        for type_ in types:
            for sss, sse in self._spans[type_]:
                if sss < ss or sse > se:
                    continue
                shadow = (
                    shadow[:sss - ss] +
                    (sse - sss) * '_' +
                    shadow[sse - ss:]
                )
        return shadow

    def _common_init(self, lststr: str or list, spans: list) -> None:
        """Do the common initializations required for subclasses of WikiText.

        :lststr: The raw string of the object to be parsed or a list pointing
            to the mother string of the parent object.
        :spans: If the lststr is already parsed, pass its _spans property as
            spans to avoid parsing it again.

        """
        if isinstance(lststr, list):
            self._lststr = lststr
        else:
            self._lststr = [lststr]
        if spans:
            self._spans = spans
        else:
            self._spans = parse_to_spans(self._lststr[0])

    def strins(self, start: int, string: str) -> None:
        """Insert the given string at the specified index. start >= 0."""
        lststr = self._lststr
        lststr0 = lststr[0]
        start += self._get_span()[0]
        # Update lststr
        lststr[0] = lststr0[:start] + string + lststr0[start:]
        # Update spans
        self._extend_span_update(
            estart=start,
            elength=len(string),
        )
        # Remember newly added spans by the string.
        spans_dict = self._spans
        for k, v in parse_to_spans(string).items():
            spans = spans_dict[k]
            for ss, se in v:
                spans.append((ss + start, se + start))

    def replace_slice(self, start: int, end: int, string: str) -> None:
        """Replace self.string[start:end] with string.

        Use this method instead of calling `strins` and `strdel` consecutively.
        By doing so only one of the `_extend_span_update` and
        `_shrink_span_update` functions will be called and the perfomance will
        improve.

        """
        lststr = self._lststr
        lststr0 = lststr[0]
        ss = self._get_span()[0]
        start += ss
        end += ss
        # Update lststr
        lststr[0] = lststr0[:start] + string + lststr0[end:]
        # Set the length of all subspans to zero because
        # they are all being replaced.
        self._close_subspans(start, end)
        # Update the other spans according to the new length.
        del_len = end - start
        ins_len = len(string)
        if ins_len > del_len:
            self._extend_span_update(
                estart=start,
                elength=ins_len - del_len,
            )
        elif ins_len < del_len:
            self._shrink_span_update(
                rmstart=end + ins_len - del_len,  # new end
                rmend=end,  # old end
            )
        # Add the newly added spans contained in the string.
        spans_dict = self._spans
        for k, v in parse_to_spans(string).items():
            spans = spans_dict[k]
            for ss, se in v:
                spans.append((ss + start, se + start))

    def pprint(self, indent: str='    ', remove_comments=False) -> None:
        """Return a pretty-print of self.string as string.

        Try to organize templates and parser functions by indenting, aligning
        at the equal signs, and adding space where appropriate.

        """
        # Do not try to do inplace pprint. It will overwrite on some spans.
        parsed = parse(self.string, self._spans)
        if remove_comments:
            for c in parsed.comments:
                c.string = ''
        else:
            # Only remove comments that contain whitespace.
            for c in parsed.comments:  # type: Comment
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
            level = template._get_indent_level()
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
            function = functions[i]
            i += 1
            name = function.name.lstrip()
            if name.lower() in ('#tag', '#invoke', ''):
                # The 2nd argument of `tag` parser function is an exception
                # and cannot be stripped.
                # So in `{{#tag:tagname|arg1|...}}`, no whitespace should be
                # added/removed to/from arg1.
                # See: [[mw:Help:Extension:ParserFunctions#Miscellaneous]]
                # All args of #invoke are also whitespace-sensitive.
                # Todo: Instead use comments to indent.
                continue
            args = function.arguments
            if not args:
                function.name = name
            else:
                # Whitespace, including newlines, tabs, and spaces is stripped
                # from the beginning and end of all the parameters of
                # parser functions. See:
                # www.mediawiki.org/wiki/Help:Extension:ParserFunctions#
                #    Stripping_whitespace
                level = function._get_indent_level()
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

    # Todo: Isn't it better to use generators for the following properties?
    @property
    def parameters(self):
        """Return a list of parameter objects."""
        return [
            Parameter(
                self._lststr,
                self._spans,
                index,
            ) for index in self._gen_subspan_indices('parameters')
        ]

    @property
    def parser_functions(self):
        """Return a list of parser function objects."""
        return [
            ParserFunction(
                self._lststr,
                self._spans,
                index,
            ) for index in self._gen_subspan_indices('functions')
        ]

    @property
    def templates(self):
        """Return a list of templates as template objects."""
        return [
            Template(
                self._lststr,
                self._spans,
                index,
            ) for index in self._gen_subspan_indices('templates')
        ]

    @property
    def wikilinks(self):
        """Return a list of wikilink objects."""
        return [
            WikiLink(
                self._lststr,
                self._spans,
                index,
            ) for index in self._gen_subspan_indices('wikilinks')
        ]

    @property
    def comments(self):
        """Return a list of comment objects."""
        return [
            Comment(
                self._lststr,
                self._spans,
                index,
            ) for index in self._gen_subspan_indices('comments')
        ]

    @property
    def external_links(self):
        """Return a list of found external link objects."""
        external_links = []
        spans = self._spans
        ss, se = self._get_span()
        if 'extlinks' not in spans:
            spans['extlinks'] = []
        elspans = spans['extlinks']
        for m in EXTERNALLINK_REGEX.finditer(self.string):
            mspan = m.span()
            mspan = (mspan[0] + ss, mspan[1] + ss)
            if mspan not in elspans:
                elspans.append(mspan)
            external_links.append(
                ExternalLink(
                    self._lststr,
                    spans,
                    elspans.index(mspan)
                )
            )
        return external_links

    @property
    def sections(self):
        """Return a list of section in current wikitext.

        The first section will always be the lead section, even if it is an
        empty string.

        """
        sections = []
        spans = self._spans
        lststr = self._lststr
        ss, se = self._get_span()
        selfstring = self.string
        if 'sections' not in spans:
            spans['sections'] = []
        sspans = spans['sections']
        # Lead section
        mspan = LEAD_SECTION_REGEX.match(selfstring).span()
        mspan = (mspan[0] + ss, mspan[1] + ss)
        if mspan not in sspans:
            sspans.append(mspan)
        sections.append(Section(lststr, spans, sspans.index(mspan)))
        # Other sections
        for m in SECTION_REGEX.finditer(selfstring):
            mspan = m.span()
            mspan = (mspan[0] + ss, mspan[1] + ss)
            if mspan not in sspans:
                sspans.append(mspan)
            latest_section = Section(lststr, spans, sspans.index(mspan))
            # Add text of the latest_section to any parent section.
            # Note that section 0 is not a parent for any subsection.
            min_level_added = latest_section.level
            for section in reversed(sections[1:]):
                section_level = section.level
                if section_level < min_level_added:
                    index = section._index
                    sspans[index] = (sspans[index][0], mspan[1])
                    min_level_added = section_level
            sections.append(latest_section)
        return sections

    @property
    def tables(self):
        """Return a list of found table objects."""
        shadow = self._shadow()
        tables = []
        spans = self._spans
        ss, se = self._get_span()
        if 'tables' not in spans:
            spans['tables'] = []
        tspans = spans['tables']
        m = True
        while m:
            m = False
            for m in TABLE_REGEX.finditer(shadow):
                ms, me = m.span()
                # Ignore leading whitespace using len(m.group(1)).
                mspan = (ss + ms + len(m.group(1)), ss + me)
                if mspan not in tspans:
                    tspans.append(mspan)
                tables.append(
                    Table(
                        self._lststr,
                        spans,
                        tspans.index(mspan)
                    )
                )
                shadow = shadow[:ms] + '_' * (me - ms) + shadow[me:]
        return tables


class IndexedWikiText(WikiText):

    """This is a middle-class to be used by some other subclasses.

    Not intended for the final user.

    """

    def _gen_subspan_indices(self, type_: str or None=None):
        """Yield all the subspan indices excluding self._get_span()."""
        s, e = self._get_span()
        for i, (ss, ee) in enumerate(self._spans[type_]):
            # Do not yield self._get_span().
            if s < ss and ee <= e:
                yield i


ExternalLink = WikiLink = Template = Comment = ParserFunction = Parameter = \
    Table = Section = Temporary
parse = WikiText
