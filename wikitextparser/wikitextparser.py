"""The main module of wikitextparser."""


import re
from difflib import SequenceMatcher

from .spans import parse_to_spans
from .parameter import Parameter
from .argument import Argument
from .externallink import ExternalLink
from .wikilink import WikiLink
from .section import Section
from .comment import Comment


# HTML
HTML_TAG_REGEX = re.compile(
    r'<([A-Z][A-Z0-9]*)\b[^>]*>(.*?)</\1>',
    re.DOTALL|re.IGNORECASE,
)
# External links
VALID_EXTLINK_CHARS_PATTERN = r'[^ \\^`#<>\[\]\"\t\n{|}]*'
# See DefaultSettings.php on MediaWiki and
# https://www.mediawiki.org/wiki/Help:Links#External_links
VALID_EXTLINK_SCHEMES_PATTERN = (
    r'('
    r'bitcoin:|ftp://|ftps://|geo:|git://|gopher://|http://|https://|'
    r'irc://|ircs://|magnet:|mailto:|mms://|news:|nntp://|redis://|'
    r'sftp://|sip:|sips:|sms:|ssh://|svn://|tel:|telnet://|urn:|'
    r'worldwind://|xmpp:|//'
    r')'
)
BARE_EXTERNALLINK_REGEX = re.compile(
    VALID_EXTLINK_SCHEMES_PATTERN.replace(r'|//', r'') +
    VALID_EXTLINK_CHARS_PATTERN,
    re.IGNORECASE,
)
BRACKET_EXTERNALLINK_REGEX = re.compile(
    r'\[' + VALID_EXTLINK_SCHEMES_PATTERN + VALID_EXTLINK_CHARS_PATTERN +
    r' *[^\]\n]*\]',
    re.IGNORECASE,
)
EXTERNALLINK_REGEX = re.compile(
    r'(' + BARE_EXTERNALLINK_REGEX.pattern + r'|' +
    BRACKET_EXTERNALLINK_REGEX.pattern + r')',
    re.IGNORECASE,
)
# Arguments
POSITIONAL_ARG_NAME = re.compile('[1-9][0-9]*')
# Sections
SECTION_HEADER_REGEX = re.compile(r'(?<=(?<=\n)|(?<=^))=[^\n]+?= *(?:\n|$)')
LEAD_SECTION_REGEX = re.compile(
    r'^.*?(?=' + SECTION_HEADER_REGEX.pattern + r'|$)',
    re.DOTALL,
)
SECTION_REGEX = re.compile(
    SECTION_HEADER_REGEX.pattern + r'.*?\n*(?=' +
    SECTION_HEADER_REGEX.pattern + '|$)',
    re.DOTALL,
)


class WikiText:

    """Return a WikiText object."""

    def __init__(
        self,
        string,
        spans=None,
    ):
        """Initialize the object."""
        self._common_init(string, spans)

    def _common_init(self, string, spans):
        if type(string) is list:
            self._lststr = string
        else:
            self._lststr = [string]
        if spans:
            self._spans = spans
        else:
            self._spans = parse_to_spans(self._lststr[0])

    def __str__(self):
        """Return self-object as a string."""
        return self.string

    @property
    def string(self):
        """Retrun str(self)."""
        start, end = self._get_span()
        return self._lststr[0][start:end]

    @string.setter
    def string(self, newstring):
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
        if oldlength == newlength:
            if newstring == oldstring:
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
        else: # oldlength > newlength
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

    def strins(self, start, string):
        """Insert the given string at the specified index. Where start >= 0."""
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

    def strdel(self, start, end):
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
        # Updating lststr
        lststr[0] = lststr0[:start] + lststr0[end:]
        # Updating spans
        self._shrink_span_update(
            rmstart=start,
            rmend=end,
        )
            

    def __repr__(self):
        """Return the string representation of the WikiText."""
        return 'WikiText(' + repr(self.string) + ')'

    def __contains__(self, parsed_wikitext):
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

    def _get_span(self):
        """Return the self-span."""
        return (0, len(self._lststr[0]))

    @property
    def parameters(self):
        """Return a list of parameter objects."""
        return [
            Parameter(
                self._lststr,
                self._spans,
                index,
            ) for index in self._gen_subspan_indices('p')
        ]

    @property
    def parser_functions(self):
        """Return a list of parser function objects."""
        return [
            ParserFunction(
                self._lststr,
                self._spans,
                index,
            ) for index in self._gen_subspan_indices('pf')
        ]

    @property
    def templates(self):
        """Return a list of templates as template objects."""
        return [
            Template(
                self._lststr,
                self._spans,
                index,
            ) for index in self._gen_subspan_indices('t')
        ]

    @property
    def wikilinks(self):
        """Return a list of wikilink objects."""
        return [
            WikiLink(
                self._lststr,
                self._spans,
                index,
            ) for index in self._gen_subspan_indices('wl')
        ]

    @property
    def comments(self):
        """Return a list of comment objects."""

        return [
            Comment(
                self._lststr,
                self._spans,
                index,
            ) for index in self._gen_subspan_indices('c')
        ]

    @property
    def external_links(self):
        """Return a list of found external link objects."""
        external_links = []
        spans = self._spans
        ss, se = self._get_span()
        if 'el' not in spans:
            spans['el'] = []
        elspans = spans['el']
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
        if 's' not in spans:
            spans['s'] = []
        sspans = spans['s']
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

    def _not_in_subspans_split(self, char):
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

    def _not_in_subspans_partition(self, char):
        """Partition self.string using `char` unless char is in self._spans."""
        ss, se = self._get_span()
        string = self._lststr[0][ss:se]
        findstart = 0
        in_spans = self._in_subspans_factory()
        index = string.find(char, findstart)
        while in_spans(ss + index):
            index = string.find(char, index + 1)
        if index == -1:
            return (string, '', '')
        return (string[:index], char, string[index+1:])

    def _not_in_subspans_split_spans(self, char):
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

    def _in_subspans_factory(self):
        """Return a function that can tell if an index is in subspans.

        Checked subspans types are: ('t', 'p', 'pf', 'wl', 'c', 'et').
        """
        # Calculate subspans
        ss, se = self._get_span()
        subspans = []
        for key in ('t', 'p', 'pf', 'wl', 'c', 'et'):
            for span in self._spans[key]:
                if ss < span[0] and span[1] <= se:
                    subspans.append(span)
        # The return function
        def in_spans(index):
            """Return True if the given index is found within a subspans."""
            for span in subspans:
                if span[0] <= index < span[1]:
                    return True
            return False
        return in_spans

    def _gen_subspan_indices(self, type_):
        """Return all the subspan indices including self._get_span()"""
        ss, se = self._get_span()
        for i, s in enumerate(self._spans[type_]):
            # Including self._get_span()
            if ss <= s[0] and s[1] <= se:
                yield i
        

    def _shrink_span_update(self, rmstart, rmend):
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

    def _extend_span_update(self, estart, elength):
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
                    estart == spanstart and spanstart== ss and spanend == se
                ) or (
                    estart == spanend and spanend == se and spanstart == ss
                ):
                    # Added part is inside the span
                    spans[i] = (spanstart, spanend + elength)


    def _get_indent_level(self, with_respect_to=None):
        """Calculate the indent level for self.pprint function.

        Minimum returned value is 1.
        Being part of any Template or Parserfunction increases the indent level
        by one.

        `with_respect_to` is an instance of WikiText object.
        """
        ss, se = self._get_span()
        level = 1 # a template is always found in itself
        if with_respect_to is None:
            for s, e in self._spans['t']:
                if s < ss and se < e:
                    level += 1
            for s, e in self._spans['pf']:
                if s < ss and se < e:
                    level += 1
            return level
        else:
            rs, re = with_respect_to._get_span()
            for s, e in self._spans['t']:
                if rs <= s < ss and se < e <= re:
                    level += 1
            for s, e in self._spans['pf']:
                if rs <= s < ss  and se < e <= re:
                    level += 1
            return level

    def pprint(self, indent='    ', remove_comments=False):
        """Return a pretty print form of self.string.

        May be useful in some templates. Indents parser function and template
        arguments.
        """
        parsed = WikiText(self.string)
        if remove_comments:
            for c in parsed.comments:
                c.string = ''
        # first remove all current spacings
        for template in parsed.templates:
            level = template._get_indent_level()
            template.name = template.name.strip()
            arguments = template.arguments
            if arguments:
                template.name += '\n' + indent * level
                for argument in arguments:
                    # Warning:
                    # positional arguments of tempalates are sensitive to
                    # whitespace. See:
                    # https://meta.wikimedia.org/wiki/Help:Newlines_and_spaces
                    argument_value = argument.value
                    # Changing positional args to keyword args was disabled
                    # because currently the parser can not distinguish between
                    # some parserfunctions (e.g. {{formatnum:string|R}}) and
                    # templates.
                    '''if (argument.positional and
                        argument_value.strip() == argument_value
                    ):
                        argument.name = argument.name
                        argument.value = (
                            argument_value.strip() + '\n' + indent * level
                        )'''
                    if not argument.positional:
                        argument.name = argument.name.strip()
                        argument.value = (
                            argument_value.strip() + '\n' + indent * level
                        )
                # Special formatting for the last argument
                if not argument.positional:
                    argument.value = (
                        argument.value.rstrip() + '\n' + indent * (level - 1)
                    )

        for parser_function in parsed.parser_functions:
            level = parser_function._get_indent_level()
            parser_function.name = parser_function.name.strip()
            arguments = parser_function.arguments
            if len(arguments) > 1:
                arg0 = arguments[0]
                arg0.value = arg0.value.strip() + '\n' + indent * level
                # Whitespace, including newlines, tabs, and spaces is stripped
                # from the beginning and end of all the parameters of
                # parser functions. See:
                # www.mediawiki.org/wiki/Help:Extension:ParserFunctions#
                #    Stripping_whitespace
                for argument in arguments[1:]:
                    argument.value = (
                        argument.value.strip() + '\n' + indent * level
                    )
                # Special formatting for the last argument
                argument.value = (
                    argument.value.rstrip() + '\n' + indent * (level - 1)
                )
        return parsed.string


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
            self._index = len(self._spans['t']) -1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the Template."""
        return 'Template(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['t'][self._index]

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
        name  = self.name
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
        # Updating an existing argument
        if arg:
            if preserve_spacing:
                val = arg.value
                arg.value = val.replace(val.strip(), value)
            else:
                arg.value = value
            return
        # Adding a new argument
        if positional is None:
            if POSITIONAL_ARG_NAME.match(name) and value.strip() == value:
                positional = True
        # Calculate the whitespace needed before arg-name and after arg-value
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
        # Calculate the string that needs to be added to the Template
        if positional:
                # ignore preserve_spacing for positional args
                addstring = '|' + value
        else:
            if preserve_spacing:
                addstring = (
                    '|' + (before_name + name.strip()).ljust(name_length) +
                    '=' + before_value + value + after_value
                )
            else:
                addstring = '|' + name + '=' + value
        # Place the addstring in the right position
        if before:
            arg = self._get_arg(before, args)
            arg.strins(0, addstring)
        elif after:
            arg = self._get_arg(after, args)
            arg.strins(len(arg.string), addstring)
        else:
            if args:
                # Insert after the last argument
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
                # The template has no arguments
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
            self._index = len(self._spans['pf']) -1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the ParserFunction."""
        return 'ParserFunction(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['pf'][self._index]

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
                aspan = (aspan[0] -1, aspan[1])
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
