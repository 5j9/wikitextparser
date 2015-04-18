import re
from datetime import datetime
from pprint import pprint as pp
from timeit import timeit


# According to https://www.mediawiki.org/wiki/Manual:$wgLegalTitleChars
# illegal title characters are: r'[]{}|#<>[\u0000-\u0020]'
VALID_TITLE_CHARS_PATTERN = r'[^\x00-\x1f\|\{\}\[\]<>\n]*'
#Templates
TEMPLATE_PATTERN = (
    r'\{\{\s*' + VALID_TITLE_CHARS_PATTERN  + r'\s*(\|[^{}]*?\}\}|\}\})'
)
TEMPLATE_NOT_PARAM_REGEX = re.compile(
    TEMPLATE_PATTERN + r'(?!\})'
    r'|(?<!{)' + TEMPLATE_PATTERN
)
# Parameters
TEMPLATE_PARAMETER_REGEX = re.compile(r'\{\{\{[^{}]*?\}\}\}')
# Parser functions
PARSER_FUNCTION_NAME_PATTERN = r'[^\s]*'
PARSER_FUNCTION_REGEX = re.compile(
    r'\{\{\s*#' + PARSER_FUNCTION_NAME_PATTERN + r':[^{}]*?\}\}'
)
# Wikilinks
# https://www.mediawiki.org/wiki/Help:Links#Internal_links
WIKILINK_REGEX = re.compile(
    r'\[\[' + VALID_TITLE_CHARS_PATTERN + r'(\]\]|\|[\S\s]*?\]\])'
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
COMMENT_REGEX = re.compile(
    r'<!--.*?-->',
    re.DOTALL,
)
NOWIKI_REGEX = re.compile(
    r'<nowiki\s*.*?>.*?</nowiki\s*>',
    re.DOTALL,
)
SECTION_HEADER_REGEX = re.compile(r'(?:(?<=\n)|(?<=^))=[^\n]+?= *(?:\n|$)')
LEAD_SECTION_REGEX = re.compile(
    r'^.*?(?=' + SECTION_HEADER_REGEX.pattern + r')',
    re.DOTALL,
)
SECTION_REGEX = re.compile(
    SECTION_HEADER_REGEX.pattern + r'.*?(?=' +
    SECTION_HEADER_REGEX.pattern + '|$)',
    re.DOTALL,
)
SECTION_LEVEL_TITLE = re.compile(r'^(={1,6})([^\n]+?)\1( *(?:\n|$))')

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
            self._spans = self._get_spans()

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
        """Set a new string for this object. Update spans accordingly."""
        lststr = self._lststr
        oldlength = len(self.string)
        newlength = len(newstring)
        oldstart, oldend = self._get_span()
        # updating lststr
        lststr[0] = lststr[0][:oldstart] + newstring + lststr[0][oldend:]
        # updating spans
        if newlength > oldlength:
            oldstart, oldend = self._get_span()
            self._extend_span_update(oldstart, newlength - oldlength)
        elif newlength < oldlength:
            self._shrink_span_update(oldstart, oldstart + oldlength - newlength)

    def __repr__(self):
        """Return the string representation of the WikiText."""
        return 'WikiText("' + self.string + '")'

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
        selfstart, selfend = self._get_span()
        if 'el' not in spans:
            spans['el'] = []
        elspans = spans['el']
        for m in EXTERNALLINK_REGEX.finditer(self.string):
            mspan = m.span()
            mspan = (mspan[0] + selfstart, mspan[1] + selfstart)
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
        selfstart, selfend = self._get_span()
        selfstring = self.string
        if 's' not in spans:
            spans['s'] = []
        sspans = spans['s']
        # Lead section
        mspan = LEAD_SECTION_REGEX.match(selfstring).span()
        mspan = (mspan[0] + selfstart, mspan[1] + selfstart)
        if mspan not in sspans:
            sspans.append(mspan)
        sections.append(Section(lststr, spans, sspans.index(mspan)))
        # Other sections
        for m in SECTION_REGEX.finditer(selfstring):
            mspan = m.span()
            mspan = (mspan[0] + selfstart, mspan[1] + selfstart)
            if mspan not in sspans:
                sspans.append(mspan)
            latest_section = Section(lststr, spans, sspans.index(mspan))
            sections.append(latest_section)
            latest_level = latest_section.level
            # adding text of the latest_section to any parent section
            # Note that section 0 is not a parent for any subsection
            for i, section in enumerate(sections[1:]):
                if section.level < latest_level:
                    index = section._index
                    sspans[index] = (sspans[index][0], mspan[1])
                    sections[i+1] = Section(lststr, spans, index)
                else:
                    # do not extend spans that have lower level but belong
                    # to another header.
                    break
        return sections

    def _not_in_subspans_split(self, char):
        """Split self.string using `char` unless char is in self._spans."""
        # not used?
        spanstart, spanend = self._get_span()
        string = self._lststr[0][spanstart:spanend]
        splits = []
        findstart = 0
        in_spans = self._in_subspans_factory()
        while True:
            index = string.find(char, findstart)
            while in_spans(spanstart + index):
                index = string.find(char, index + 1)
            if index == -1:
                return splits + [string[findstart:]]
            splits.append(string[findstart:index])
            findstart = index + 1

    def _not_in_subspans_splitspans(self, char):
        """Like _not_in_subspans_split but return spans."""
        spanstart, spanend = self._get_span()
        string = self._lststr[0][spanstart:spanend]
        results = []
        findstart = 0
        in_spans = self._in_subspans_factory()
        while True:
            index = string.find(char, findstart)
            while in_spans(spanstart + index):
                index = string.find(char, index + 1)
            if index == -1:
                return results + [(spanstart + findstart, spanend)]
            results.append((spanstart + findstart, spanstart + index))
            findstart = index + 1

    def _in_subspans_factory(self):
        """Return a function that can tell if an index is in subspans.

        Checked subspans types are: ('t', 'p', 'pf', 'wl', 'c', 'nw').
        """
        # calculate subspans
        selfstart, selfend = self._get_span()
        subspans = []
        for key in ('t', 'p', 'pf', 'wl', 'c', 'nw'):
            for span in self._spans[key]:
                if selfstart < span[0] and span[1] < selfend:
                    subspans.append(span)
        # the return function
        def in_spans(index):
            """Return True if the given index is found within one of the spans."""
            for span in subspans:
                if span[0] <= index < span[1]:
                    return True
            return False
        return in_spans

    def _gen_subspan_indices(self, type_):
        selfstart, selfend = self._get_span()
        for i, s in enumerate(self._spans[type_]):
            # including self._get_span()
            if selfstart <= s[0] and s[1] <= selfend:
                yield i

    def _get_spans(self):
        """Calculate and set self._spans.

        The result a dictionary containing lists of spans:
        {
            'p': parameter_spans,
            'pf': parser_function_spans,
            't': template_spans,
            'wl': wikilink_spans,
            'c': comment_spans,
            'nw': nowiki_spans,
        }
        """
        string = self._lststr[0]
        parameter_spans = []
        parser_function_spans = []
        template_spans = []
        wikilink_spans = []
        comment_spans = []
        nowiki_spans = []
        # HTML comments
        for match in COMMENT_REGEX.finditer(string):
            comment_spans.append(match.span())
            group = match.group()
            string = string.replace(group, '_' * len(group))
        # <nowiki>
        for match in NOWIKI_REGEX.finditer(string):
            nowiki_spans.append(match.span())
            group = match.group()
            string = string.replace(group, '_' * len(group))
        # The title in WikiLinks may contain braces that interfere with
        # detection of templates
        for match in WIKILINK_REGEX.finditer(string):
            wikilink_spans.append(match.span())
            group = match.group()
            string = string.replace(
                group,
                group.replace('}', '_').replace('{', '_'),
            )
        while True:
            # Single braces will interfere with detection of other elements and
            # should be removed beforehand.
            string = re.sub(r'(?<!{){(?=[^{])', '_', string)
            string = re.sub(r'(?<!})}(?=[^}])', '_', string)
            # The following was much more faster than
            # string = re.sub(r'{(?=[^}]*$)', '_', string)
            head, sep, tail = string.rpartition('}')
            string = ''.join((head, sep, tail.replace('{', '_')))
            # Also Python does not support non-fixed-length lookbehinds
            head, sep, tail = string.partition('{')
            string = ''.join((head.replace('}', '_'), sep, tail))
            match = None
            # Template parameters
            loop = True
            while loop:
                loop = False
                for match in TEMPLATE_PARAMETER_REGEX.finditer(string):
                    loop = True
                    parameter_spans.append(match.span())
                    group = match.group()
                    string = string.replace(group, '___' + group[3:-3] + '___')
            # Parser fucntions
            loop = True
            while loop:
                loop = False
                for match in PARSER_FUNCTION_REGEX.finditer(string):
                    loop = True
                    parser_function_spans.append(match.span())
                    group = match.group()
                    string = string.replace(group, '__' + group[2:-2] + '__' )
            # Templates
            loop = True
            while loop:
                loop = False
                for match in TEMPLATE_NOT_PARAM_REGEX.finditer(string):
                    loop = True
                    template_spans.append(match.span())
                    group = match.group()
                    string = string.replace(group, '__' + group[2:-2] + '__' )
            if not match:
                break
        return {
            'p': parameter_spans,
            'pf': parser_function_spans,
            't': template_spans,
            'wl': wikilink_spans,
            'c': comment_spans,
            'nw': nowiki_spans,
        }
        

    def _shrink_span_update(self, rmstart, rmend):
        """Update self._spans according to the removed span.

        Warning: If an operation involves both _shrink_span_update and
        _extend_span_update, you might wanna consider doing the
        _extend_span_update before the _shrink_span_update as this function
        can cause data loss in self._spans.
        """
        # Note: No span should be removed from _spans.
        # Don't use self._set_spans()
        rmlength = rmend - rmstart
        for t, spans in self._spans.items():
            for i, (spanstart, spanend) in enumerate(spans):
                if rmend <= spanstart:
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

    def _extend_span_update(self, astart, alength):
        """Update self._spans according to the added span."""
        # Note: No span should be removed from _spans.
        # Don't use self._set_spans()
        for spans in self._spans.values():
            for i, (spanstart, spanend) in enumerate(spans):
                if astart < spanstart:
                    # added part is before the span
                    spans[i] = (spanstart + alength, spanend + alength)
                elif spanstart <= astart < spanend:
                    # added part is inside the span
                    spans[i] = (spanstart, spanend + alength)


class _Indexed_Object(WikiText):

    """This is a middle-class to be used by some other subclasses.

    Not intended for the final user.
    """

    def _common_init(
        self,
        string,
        spans=None,
        index=None,
    ):
        """Set initial value for self._lststr, self._spans and self._index."""
        if type(string) is list:
            self._lststr = string
        else:
            self._lststr = [string]
        if spans is None:
            self._spans = self._get_spans()
        else:
            self._spans = spans
        if index is None:
            self._index = -1
        else:
            self._index = index

    def _gen_subspan_indices(self, type_):
        selfstart, selfend = self._get_span()
        for i, s in enumerate(self._spans[type_]):
            # not including self._get_span()
            if selfstart < s[0] and s[1] < selfend:
                yield i



class Template(_Indexed_Object):

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
        self._common_init(string, spans, index)

    def __repr__(self):
        """Return the string representation of the Template."""
        return 'Template("' + self.string + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['t'][self._index]

    @property
    def arguments(self):
        """Parse template content. Create self.name and self.arguments."""
        barsplits = self._not_in_subspans_splitspans('|')[1:]
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
        return self.string[2:-2].partition('|')[0]

    @name.setter
    def name(self, newname):
        """Set the new name for the template."""
        name, pipe, paramters  = self.string[2:-2].partition('|')
        if pipe:
            self.string = '{{' + newname + '|' + paramters + '}}'
        else:
            self.string = '{{' + newname + '}}'
        

    def rm_first_of_dup_args(self):
        """Remove duplicate keyword arguments by only keeping the last ones.

        This function does not care about values.
        """
        name_argument = {}
        for a in self.arguments:
            an = a.name.strip()
            if an in name_argument:
                name_argument[an].string = ''
            elif a.equal_sign:
                name_argument[an] = a


class Parameter(_Indexed_Object):

    """Use to represent {{{parameters}}}."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans, index)

    def __repr__(self):
        """Return the string representation of the Parameter."""
        return 'Parameter("' + self.string + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['p'][self._index]

    @property
    def name(self):
        """Return current parameter's name."""
        return self.string[3:-3].partition('|')[0]

    @name.setter
    def name(self, newname):
        """Set the new name."""
        name, pipe, default = self.string[3:-3].partition('|')
        if pipe:
            self.string = '{{{' + newname + '|' + default + '}}}'
        else:
            self.string = '{{{' + newname + '}}}'

    @property
    def pipe(self):
        """Return `|` if there is a pipe (default value) in the Parameter.

         Return '' otherwise.
         """
        return self.string[3:-3].partition('|')[1]

    @property
    def default(self):
        """Return value of a keyword argument."""
        return self.string[3:-3].partition('|')[2]

    @default.setter
    def default(self, newdefault):
        """Set the new value. If a default exist, change it. Add ow."""
        self.string = '{{{' + self.name + '|' + newdefault + '}}}'

    def append_default_param(self, new_default_name):
        """Append a new default parameter in the appropriate place.

        The new default will be added to the innter-most parameter.
        If the parameter already exists among defaults, don't change anything.
        """
        stripped_default_name = new_default_name.strip()
        if stripped_default_name == self.name.strip():
            return
        dig = True
        innermost_param = self
        while dig:
            dig = False
            default = innermost_param.default
            for p in innermost_param.parameters:
                if p.string == default:
                    if stripped_default_name == p.name.strip():
                        return
                    innermost_param = p
                    dig = True
        if innermost_param.pipe:
            innermost_param.string = (
                '{{{' + innermost_param.name + '|{{{' + 
                new_default_name + '|' + innermost_param.default + '}}}}}}'
            )
        else:
            innermost_param.string = (
                '{{{' + innermost_param.name + '|{{{' + 
                new_default_name + '}}}}}}'
            )
        

class ParserFunction(_Indexed_Object):

    """Use to represent a ParserFunction."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans, index)

    def __repr__(self):
        """Return the string representation of the ParserFunction."""
        return 'ParserFunction("' + self.string + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['pf'][self._index]

    @property
    def arguments(self):
        """Parse template content. Create self.name and self.arguments."""
        barsplits = self._not_in_subspans_splitspans('|')
        arguments = []
        spans = self._spans
        lststr = self._lststr
        typeindex = 'pfa' + str(self._index)
        if typeindex not in spans:
            spans[typeindex] = []
        aspans = spans[typeindex]
        selfstart, selfend = self._get_span()
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
        return self.string.partition(':')[0].partition('#')[2]


class WikiLink(_Indexed_Object):

    """Use to represent WikiLinks."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans, index)

    def __repr__(self):
        """Return the string representation of the WikiLink."""
        return 'WikiLink("' + self.string + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['wl'][self._index]

    @property
    def target(self):
        """Return target of this WikiLink."""
        return self.string[2:-2].partition('|')[0]

    @target.setter
    def target(self, newtarget):
        """Set a new target."""
        target, pipe, text = self.string[2:-2].partition('|')
        if pipe:
            self.string = '[[' + newtarget + '|' + text + ']]'
        else:
            self.string = '[[' + newtarget + ']]'

    @property
    def text(self):
        """Return display text of this WikiLink."""
        target, pipe, text = self.string[2:-2].partition('|')
        if pipe:
            return text

    @text.setter
    def text(self, newtext):
        """Set a new text."""
        self.string = '[[' + self.target + '|' + newtext + ']]'


class Comment(_Indexed_Object):

    """Use to represent comments."""

    def __init__(self, string, spans=None, index=None):
        """Run self._common_init."""
        self._common_init(string, spans, index)

    def __repr__(self):
        """Return the string representation of the Comment."""
        return 'Comment("' + self.string + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['c'][self._index]

    @property
    def contents(self):
        """Return contents of this comment."""
        return self.string[4:-3]


class ExternalLink(_Indexed_Object):

    """Use to represent External Links."""

    def __init__(self, string, spans=None, index=None):
        """Run self._common_init. Set self._spans['el'] if spans is None."""
        self._common_init(string, spans, index)
        if spans is None:
            self._spans['el'] = [(0, len(string))]

    def __repr__(self):
        """Return the string representation of the ExternalLink."""
        return 'ExternalLink("' + self.string + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['el'][self._index]
    
    @property
    def url(self):
        """Return the url part of the ExternalLink."""
        if self.in_brackets:
            return self.string[1:-1].partition(' ')[0]
        return self.string

    @url.setter
    def url(self, newurl):
        """Set a new url for the current ExternalLink."""
        text = self.text
        if self.in_brackets:
            if text:
                self.string = '[' + newurl + ' ' + text + ']'
            else:
                self.string = '[' + newurl + ']'
        else:
            self.string = newurl
        
    @property
    def text(self):
        """Return the display text of the external link.

        Return self.string if this is a bare link.
        Return 
        """
        if self.in_brackets:
            return self.string[1:-1].partition(' ')[2]
        return self.string

    @text.setter
    def text(self, newtext):
        """Set a new text for the current ExternalLink.

        Automatically puts the ExternalLink in brackets if it's not already.
        """
        self.string = '[' + self.url + ' ' + newtext + ']'

    @property
    def in_brackets(self):
        """Return true if the ExternalLink is in brackets. False otherwise."""
        if self.string.startswith('['):
            return True
        return False

        
class Argument(_Indexed_Object):

    """Use to represent Template or ParserFunction arguments.

    Note that in mediawiki documentation `arguments` are (also) called
    parameters. In this module the convention is like this:
    {{{parameter}}}, {{t|argument}}.
    See https://www.mediawiki.org/wiki/Help:Templates for more information.
    """

    def __init__(self, string, spans=None, index=None, typeindex=None):
        """Initialize the object."""
        self._common_init(string, spans, index)
        if typeindex is None:
            self._typeindex = 'a'
        else:
            self._typeindex = typeindex
        if spans is None:
            self._spans[self._typeindex] = [(0, len(string))]
            

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'Argument("' + self.string + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans[self._typeindex][self._index]

    @property
    def name(self):
        """Return arg's name-part. Return the position for positional args."""
        pipename, equal, value = self.string.partition('=')
        if equal:
            return pipename[1:]
        # positional argument
        position = 1
        godstring = self._lststr[0]
        for span0, span1 in self._spans[self._typeindex][:self._index]:
            if span0 < span1 and '=' not in godstring[span0:span1]:
                position += 1
        return str(position)

    @name.setter
    def name(self, newname):
        """Changes the name of the argument."""
        self.string = '|' + newname + '=' + self.value

    @property
    def equal_sign(self):
        """Return `=` if there is an equal sign in the argument. Else ''."""
        return self.string.partition('=')[1]

    @property
    def value(self):
        """Return value of a keyword argument."""
        pipename, equal, value = self.string.partition('=')
        if equal:
            return value
        # anonymous parameters
        return pipename[1:]

    @value.setter
    def value(self, newvalue):
        """Set a the value for the current argument."""
        pipename, equal, value = self.string.partition('=')
        if equal:
            self.string = pipename + '=' + newvalue
        else:
            self.string = pipename[0] + newvalue
        

class Section(_Indexed_Object):

    """Use to represent wikitext Sections."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans, index)
        if spans is None:
            self._spans['s'] = [(0, len(string))]

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'Argument("' + self.string + '")'

    def _get_span(self):
        """Return selfspan (span of self.string in self._lststr[0])."""
        return self._spans['s'][self._index]

    @property
    def level(self):
        """Return level of this section. Level is in range(1,7)."""
        selfstring = self.string
        m = SECTION_LEVEL_TITLE.match(selfstring)
        if not m:
            return 0
        return len(m.group(1))

    @level.setter
    def level(self, newlevel):
        """Change leader level of this sectoin."""
        equals = '=' * newlevel
        self.string = equals + self.title + equals + self.contents
            
    @property
    def title(self):
        """Return title of this section. Return '' for lead sections."""
        level = self.level
        if level == 0:
            return ''
        return self.string.partition('\n')[0].rstrip()[level:-level]

    @title.setter
    def title(self, newtitle):
        """Set the new title for this section and update self.lststr."""
        level = self.level
        if level == 0:
            raise RuntimeError(
                "Can't set title for a lead section. "
                "Try adding it to the contents."
            )
        equals = '=' * level
        self.string = equals + newtitle + equals + '\n' + self.contents
        
    @property
    def contents(self):
        """Return contents of this section."""
        if self.level == 0:
            return self.string
        return self.string.partition('\n')[2]

    @contents.setter
    def contents(self, newcontents):
        """Set newcontents as the contents of this section."""
        level = self.level
        if level == 0:
            self.string = newcontents
        else:
            self.string = self.string.partition('\n')[0] + '\n' + newcontents
            
