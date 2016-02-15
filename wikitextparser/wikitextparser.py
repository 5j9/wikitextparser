"""The main module of wikitextparser."""


import re

from .spans import (
    parse_to_spans,
    VALID_EXTLINK_CHARS_PATTERN,
    VALID_EXTLINK_SCHEMES_PATTERN,
    BARE_EXTERNALLINK_PATTERN
)
from .parameter import Parameter
from .argument import Argument
from .externallink import ExternalLink
from .wikilink import WikiLink
from .section import Section
from .comment import Comment
from .wikitext import WikiText
from .table import Table


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
    # Should not containt any other table-start
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


class WikiText(WikiText):

    """Return a WikiText object."""

    def __init__(
        self,
        string,
        spans=None,
    ):
        """Initialize the object."""
        self._common_init(string, spans)

    def _common_init(self, string, spans):
        if isinstance(string, list):
            self._lststr = string
        else:
            self._lststr = [string]
        if spans:
            self._spans = spans
        else:
            self._spans = parse_to_spans(self._lststr[0])

    def strins(self, start, string):
        """Insert the given string at the specified index. start >= 0."""
        lststr = self._lststr
        lststr0 = lststr[0]
        start += self._get_span()[0]
        # Updating lststr
        lststr[0] = lststr0[:start] + string + lststr0[start:]
        # Updating spans
        self._extend_span_update(
            estart=start,
            elength=len(string),
        )
        for k, v in parse_to_spans(string).items():
            for ss, se in v:
                self._spans[k].append((ss + start, se + start))

    def pprint(self, indent='    ', remove_comments=False):
        """Return a pretty print form of self.string.

        May be useful in some templates. Indents parser function and template
        arguments.
        """
        parsed = WikiText(self.string)
        if remove_comments:
            for c in parsed.comments:
                c.string = ''
        # First remove all current spacings.
        for template in parsed.templates:
            level = template._get_indent_level()
            template_name = template.name.strip()
            template.name = template_name
            if ':' in template_name:
                not_a_parser_fucntion = False
            else:
                not_a_parser_fucntion = True
            args = template.arguments
            if args:
                template.name += '\n' + indent * level
                # Required for alignment
                max_name_len = max(len(a.name.strip()) for a in args)
                # Order of positional arguments changes when they are converted
                # to keyword arguments in the for-loop below. Count them while
                # converting.
                positional_count = 0
                for arg in args:
                    value = arg.value
                    stripped_name = arg.name.strip()
                    positional = arg.positional
                    # Positional arguments of tempalates are sensitive to
                    # whitespace. See:
                    # https://meta.wikimedia.org/wiki/Help:Newlines_and_spaces
                    if positional:
                        positional_count += 1
                        if not_a_parser_fucntion:
                            if value.strip() == value:
                                arg.name = (
                                    ' ' + str(positional_count) + ' ' +
                                    ' ' * (max_name_len - len(stripped_name))
                                )
                                arg.value = (
                                    ' ' + value.strip() + '\n' + indent * level
                                )
                            else:
                                # The argument should be forced to be a named
                                # one otherwise the process may introduce
                                # duplicate arguments.
                                arg.name = (
                                    ' ' + str(positional_count) + ' ' +
                                    ' ' * (max_name_len - len(stripped_name))
                                )
                                arg.value = (
                                    ' <nowiki></nowiki>' + value +
                                    '<nowiki></nowiki>\n' + indent * level
                                )
                    else:
                        arg.name = (
                            ' ' + stripped_name + ' ' +
                            ' ' * (max_name_len - len(stripped_name))
                        )
                        arg.value = ' ' + value.strip() + '\n' + indent * level
                # Special formatting for the last argument.
                if not arg.positional:
                    arg.value = (
                        arg.value.rstrip() + '\n' + indent * (level - 1)
                    )
        for parser_function in parsed.parser_functions:
            level = parser_function._get_indent_level()
            name = parser_function.name.strip()
            parser_function.name = name
            if name == '#tag':
                # The 2nd argument of `tag` parser function is an exception
                # and cannot be stripped.
                # So in `{{#tag:tagname|arg1|...}}`, no whitespace should be
                # added/removed to/from arg1.
                # See: [[mw:Help:Extension:ParserFunctions#Miscellaneous]]
                # This makes things complicated. Continue.
                continue
            args = parser_function.arguments
            if len(args) > 1:
                arg0 = args[0]
                arg0.value = ' ' + arg0.value.strip() + '\n' + indent * level
                if not arg0.positional:
                    arg0.name = ' ' + arg0.name.strip() + ' '
                # Required for alignment
                max_name_len = max(
                    (
                        len(a.name.strip()) for a in args[1:] if
                        not a.positional
                    ),
                    default=None
                )
                # Whitespace, including newlines, tabs, and spaces is stripped
                # from the beginning and end of all the parameters of
                # parser functions. See:
                # www.mediawiki.org/wiki/Help:Extension:ParserFunctions#
                #    Stripping_whitespace
                for arg in args[1:]:
                    arg.value = ' ' + arg.value.strip() + '\n' + indent * level
                    if not arg.positional:
                        name = arg.name.strip()
                        arg.name = (
                            ' ' + name + ' ' + ' ' * (max_name_len - len(name))
                        )
                # Special formatting for the last argument
                arg.value = arg.value.rstrip() + '\n' + indent * (level - 1)
        return parsed.string

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
        """Returns a list of section in current wikitext.

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
        loop = True
        while loop:
            loop = False
            for m in TABLE_REGEX.finditer(shadow):
                loop = True
                mspan = m.span()
                # Ignore leading whitespace using len(m.group(1))
                mspan = (ss + mspan[0] + len(m.group(1)), ss + mspan[1])
                if mspan not in tspans:
                    tspans.append(mspan)
                tables.append(
                    Table(
                        self._lststr,
                        spans,
                        tspans.index(mspan)
                    )
                )
                ms, me = mspan
                shadow = shadow[:ms] + '_' * (me - ms) + shadow[me:]
        return tables


class _Indexed_WikiText(WikiText):

    """This is a middle-class to be used by some other subclasses.

    Not intended for the final user.
    """

    def _gen_subspan_indices(self, type_):
        """Return all the subspan indices excluding self._get_span()"""
        ss, se = self._get_span()
        for i, s in enumerate(self._spans[type_]):
            # not including self._get_span()
            if ss < s[0] and s[1] < se:
                yield i


class Section(Section, WikiText):

    """Mix the Section class with _Indexed_WikiText."""

    pass


class Template(_Indexed_WikiText):

    """Convert strings to Template objects.

    The string should start with {{ and end with }}.
    """

    def __init__(
        self,
        string,
        spans=None,
        index=None,
    ):
        """Initialize the object."""
        self._common_init(string, spans)
        if index is None:
            self._index = len(self._spans['templates']) - 1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the Template."""
        return 'Template(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['templates'][self._index]

    @property
    def arguments(self):
        """Parse template content. Create self.name and self.arguments."""
        barsplits = self._not_in_subspans_split_spans('|')[1:]
        arguments = []
        spans = self._spans
        lststr = self._lststr
        typeindex = 'ta' + str(self._index)
        if typeindex not in spans:
            spans[typeindex] = []
        aspans = spans[typeindex]
        if barsplits:
            # remove the final '}}' from the last argument.
            barsplits[-1] = (barsplits[-1][0], barsplits[-1][1] - 2)
            for aspan in barsplits:
                # include the the starting '|'
                aspan = (aspan[0] + -1, aspan[1])
                if aspan not in aspans:
                    aspans.append(aspan)
                arguments.append(
                    Argument(
                        lststr,
                        spans,
                        aspans.index(aspan),
                        typeindex,
                    )
                )
        return arguments

    @property
    def name(self):
        """Return template's name part. (includes whitespace)"""
        p0 = self._not_in_subspans_partition('|')[0]
        if len(p0) == len(self.string):
            return p0[2:-2]
        else:
            return p0[2:]

    @name.setter
    def name(self, newname):
        """Set the new name for the template."""
        name = self.name
        self.strins(2, newname)
        self.strdel(2 + len(newname), 2 + len(newname + name))

    def rm_first_of_dup_args(self):
        """Eliminate duplicate arguments by removing the first occurrences.

        Remove first occurances of duplicate arguments-- no matter what their
        value is. Result of the rendered wikitext should remain the same.
        Warning: Some meaningful data may be removed from wikitext.

        Also see `rm_dup_args_safe` function.
        """
        names = []
        for a in reversed(self.arguments):
            name = a.name.strip()
            if name in names:
                a.strdel(0, len(a.string))
            else:
                names.append(name)

    def rm_dup_args_safe(self, tag=None):
        """Remove duplicate arguments in a safe manner.

    `   Remove the duplicate arguments only if:
        1. Both arguments have the same name AND value.
        2. Arguments have the same name and one of them is empty. (Remove the
            empty one.)

        Warning: Although this is considered to be safe as no meaningful data
            is removed but the result of the renedered wikitext may actually
            change if the second arg is empty and removed but the first has a
            value.

        If `tag` is defined, it should be a string, tag the remaining
        arguments by appending the provided tag to their value.

        Also see `rm_first_of_dup_args` function.
        """
        template_stripped_name = self.name.strip()
        name_args_vals = {}
        # Removing positional args affects their name. By reversing the list
        # we avoid encountering those kind of args.
        for arg in reversed(self.arguments):
            name = arg.name.strip()
            if arg.positional:
                # Value of keyword arguments is automatically stripped by MW.
                val = arg.value
            else:
                # But it's not OK to strip whitespace in positional arguments.
                val = arg.value.strip()
            if name in name_args_vals:
                # This is a duplicate argument.
                if not val:
                    # This duplacate argument is empty. It's safe to remove it.
                    arg.strdel(0, len(arg.string))
                else:
                    # Try to remove any of the detected duplicates of this
                    # that are empty or their value equals to this one.
                    name_args = name_args_vals[name][0]
                    name_vals = name_args_vals[name][1]
                    if val in name_vals:
                        arg.strdel(0, len(arg.string))
                    elif '' in name_vals:
                        i = name_vals.index('')
                        a = name_args.pop(i)
                        a.strdel(0, len(a.string))
                        name_vals.pop(i)
                    else:
                        # It was not possible to remove any of the duplicates.
                        name_vals.append(arg)
                        name_vals.append(val)
                        if tag:
                            arg.value += tag
            else:
                name_args_vals[name] = ([arg], [val])

    def set_arg(
        self, name, value, positional=None, before=None, after=None,
        preserve_spacing=True
    ):
        """Set the value for `name` argument. Add it if it doesn't exist.

        Use `positional`, `before` and `after` keyword arguments only when
            adding a new argument.
        If `before` is passed, ignore `after`.
        If neither `before` nor `after` are passed and it's needed to add a new
            argument, then append the new argument to the end.
        If `positional` is passed and it's True, try to add the given value
            as a positional argument. If it's None, do as appropriate.
            Ignore `preserve_spacing` if positional is True.
        """
        args = list(reversed(self.arguments))
        arg = self._get_arg(name, args)
        # Updating an existing argument.
        if arg:
            if positional:
                arg.positional = positional
            if preserve_spacing:
                val = arg.value
                arg.value = val.replace(val.strip(), value)
            else:
                arg.value = value
            return
        # Adding a new argument
        if positional is None and not name:
            positional = True
        # Calculate the whitespace needed before arg-name and after arg-value.
        if not positional and preserve_spacing and args:
            before_names = []
            name_lengths = []
            before_values = []
            after_values = []
            for arg in args:
                aname = arg.name
                before_names.append(re.match(r'\s*', aname).group())
                name_lengths.append(len(aname))
                bv, av = re.match(r'(\s*).*(\s*)$', arg.value).groups()
                before_values.append(bv)
                after_values.append(av)
            before_name = mode(before_names)
            name_length = mode(name_lengths)
            after_value = mode(
                [re.match(r'.*?(\s*)\|', self.string).group(1)] +
                after_values[1:]
            )
            before_value = mode(before_values)
        else:
            preserve_spacing = False
        # Calculate the string that needs to be added to the Template.
        if positional:
            # Ignore preserve_spacing for positional args.
            addstring = '|' + value
        else:
            if preserve_spacing:
                addstring = (
                    '|' + (before_name + name.strip()).ljust(name_length) +
                    '=' + before_value + value + after_value
                )
            else:
                addstring = '|' + name + '=' + value
        # Place the addstring in the right position.
        if before:
            arg = self._get_arg(before, args)
            arg.strins(0, addstring)
        elif after:
            arg = self._get_arg(after, args)
            arg.strins(len(arg.string), addstring)
        else:
            if args and not positional:
                # Insert after the last argument.
                # The addstring needs to be recalculated because we don't
                # want to change the the whitespace before the final braces.
                arg = args[0]
                arg_string = arg.string
                arg.strins(
                    len(arg_string),
                    arg.string.rstrip() + after_value + addstring.rstrip() +
                    after_values[0]
                )
                arg.strdel(0, len(arg_string))
            else:
                # The template has no arguments or the new arg is
                # positional AND is to be added at the end of the template.
                self.strins(len(self.string) - 2, addstring)

    def _get_arg(self, name, args):
        """Return the first argument in the args that has the given name.

        Return None if no such argument is found.

        As the computation of self.arguments is a little costly, this
        function was created so that other methods that have already computed
        the arguments use it instead of calling get_arg directly.
        """
        for arg in args:
            if arg.name.strip() == name.strip():
                return arg

    def get_arg(self, name):
        """Return the last argument with the given name.

        Return None if no such argument is found.
        """
        return self._get_arg(name, reversed(self.arguments))

    def has_arg(self, name, value=None):
        """Return true if the is an arg named `name`.

        Also check equality of values if `value` is provided.

        Note: If you just need to get an argument and you want to LBYL, it's
            better to get_arg directly and then check if the returned value
            is None.
        """
        for arg in reversed(self.arguments):
            if arg.name.strip() == name.strip():
                if value:
                    if arg.positional:
                        if arg.value == value:
                            return True
                        else:
                            return False
                    else:
                        if arg.value.strip() == value.strip():
                            return True
                        else:
                            return False
                else:
                    return True
        return False


class ParserFunction(_Indexed_WikiText):

    """Create a new ParserFunction object."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans)
        if index is None:
            self._index = len(self._spans['functions']) - 1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the ParserFunction."""
        return 'ParserFunction(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['functions'][self._index]

    @property
    def arguments(self):
        """Parse template content. Create self.name and self.arguments."""
        barsplits = self._not_in_subspans_split_spans('|')
        arguments = []
        spans = self._spans
        lststr = self._lststr
        typeindex = 'pfa' + str(self._index)
        if typeindex not in spans:
            spans[typeindex] = []
        aspans = spans[typeindex]
        ss, se = self._get_span()
        # remove the final '}}' from the last argument.
        barsplits[-1] = (barsplits[-1][0], barsplits[-1][1] - 2)
        # first argument
        aspan = barsplits.pop(0)
        aspan = (aspan[0] + self.string.find(':'), aspan[1])
        if aspan not in aspans:
            aspans.append(aspan)
        arguments.append(
            Argument(lststr, spans, aspans.index(aspan), typeindex)
        )
        # the rest of the arguments (similar to templates)
        if barsplits:
            for aspan in barsplits:
                # include the the starting '|'
                aspan = (aspan[0] - 1, aspan[1])
                if aspan not in aspans:
                    aspans.append(aspan)
                arguments.append(
                    Argument(lststr, spans, aspans.index(aspan), typeindex)
                )
        return arguments

    @property
    def name(self):
        """Return name part of the current ParserFunction."""
        return self.string[2:].partition(':')[0]

    @name.setter
    def name(self, newname):
        """Set a new name."""
        name = self.name
        self.strins(2, newname)
        self.strdel(2 + len(newname), 2 + len(newname + name))


class Parameter(Parameter, _Indexed_WikiText):

    """Mix the Parameter class with _Indexed_WikiText."""

    pass


class WikiLink(WikiLink, _Indexed_WikiText):

    """Mix the WikiLink class with _Indexed_WikiText."""

    pass


class ExternalLink(ExternalLink, _Indexed_WikiText):

    """Mix the ExternalLink class with _Indexed_WikiText."""

    pass


class Argument(Argument, _Indexed_WikiText):

    """Mix the Arguments class with _Indexed_WikiText."""

    pass


class Comment(Comment, _Indexed_WikiText):

    """Mix the Comment class with _Indexed_WikiText."""

    pass


class Table(Table, _Indexed_WikiText):

    """Mix the Table class with _Indexed_WikiText."""

    pass


def mode(list_):
    """Return the most common item in the list.

    Return the first one if there are more than one most common items.

    Example:

    >>> mode([1,1,2,2,])
    1
    >>> mode([1,2,2])
    2
    >>> mode([])
    ...
    ValueError: max() arg is an empty sequence

    """
    return max(set(list_), key=list_.count)


parse = WikiText
