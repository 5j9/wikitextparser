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
SECTION_LEVEL_TITLE = re.compile(r'(\n|^)(={0,6})([^\n]+?)\2 *(\n|$)')

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
        """Retrun result string."""
        start, end = self._get_span()
        return self._lststr[0][start:end]

    def __repr__(self):
        """Return the string representation of the WikiText."""
        return 'WikiText("' + self.__str__() + '")'

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
        for m in EXTERNALLINK_REGEX.finditer(self.__str__()):
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
        selfstring = self.__str__()
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
        """Split self.__str__() using `char` unless char is in ._spans."""
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

        Checked subspans types are: ('t', 'p', 'pf', 'wl', 'c').
        """
        # calculate subspans
        selfstart, selfend = self._get_span()
        subspans = []
        for key in ('t', 'p', 'pf', 'wl', 'c'):
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
        }
        """
        string = self._lststr[0]
        parameter_spans = []
        parser_function_spans = []
        template_spans = []
        wikilink_spans = []
        comment_spans = []
        # HTML comments
        for match in COMMENT_REGEX.finditer(string):
            comment_spans.append(match.span())
            group = match.group()
            string = string.replace(group, '_' * len(group))
        # <nowiki>
        for match in NOWIKI_REGEX.finditer(string):
            group = match.group()
            string = string.replace(group, '_' * len(group))
        # The title in WikiLinks May contain braces that interfere with
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
        }
        

    def _remove_update(self, rmstart, rmend):
        """Update _lststr and _spans according to the removed span.

        Warning: If an operation involves both _remove_update and _add_update,
        you might wanna consider doing the _add_update before the
        _remove_update as this function can cause data loss in self._spans.
        """
        # Note: No span should be removed from _spans.
        # Don't use self._set_spans()
        rmlength = rmend - rmstart
        self._lststr[0] = self._lststr[0][:rmstart] + self._lststr[0][rmend:]
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

    def _add_update(self, astring, astart):
        """Update _lststr and _spans according to the added span."""
        # Note: No span should be removed from _spans.
        # Don't use self._set_spans()
        self._lststr[0] = (
            self._lststr[0][:astart] + astring + self._lststr[0][astart:]
        )
        alength = len(astring)
        for t, spans in enumerate(self._spans):
            for i, (spanstart, spanend) in enumerate(spans):
                if astart <= spanstart:
                    # added part is before the span
                    spans[i] = (spanstart + alength, spanend + alength)
                elif spanstart < astart <= spanend:
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
        remove_duplicate_args=True,
    ):
        """Initialize the object."""
        self._common_init(string, spans, index)
        if remove_duplicate_args:
            self.remove_duplicate_arguments()

    def __repr__(self):
        """Return the string representation of the Template."""
        return 'Template("' + self.__str__() + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['t'][self._index]

    @property
    def arguments(self):
        """Parse template content. Create self.name and self.arguments."""
        barsplits = self._not_in_subspans_splitspans('|')[1:]
        arguments = []
        if 'a' not in self._spans:
            self._spans['a'] = []
        if barsplits:
            barsplits[-1] = (barsplits[-1][0], barsplits[-1][1] - 2)
            for aspan in barsplits:
                if aspan not in self._spans['a']:
                    self._spans['a'].append(aspan)
                arguments.append(
                    Argument(
                        self._lststr,
                        self._spans,
                        self._spans['a'].index(aspan)
                    )
                )
        return arguments

    @property
    def name(self):
        """Return template's name part. (includes whitespace)"""
        barsplits = self._not_in_subspans_split('|')
        if len(barsplits) > 1:
            return barsplits[0][2:]
        return barsplits[0][2:-2]

    @name.setter
    def name(self, newname, keep_whitespace=True):
        """Set the new name for the template."""
        # Todo
        pass
        

    def remove_duplicate_arguments(self):
        """Remove duplicate keyword arguments. Keep the last one."""
        # todo : add test {{t|a|a}}
        name_argument = {}
        for a in self.arguments:
            an = a.name.strip()
            if an in name_argument:
                name_argument[an].destroy()
            elif a.equal_sign:
                name_argument[an] = a


class Parameter(_Indexed_Object):

    """Use to represent {{{parameters}}}."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans, index)

    def __repr__(self):
        """Return the string representation of the Parameter."""
        return 'Parameter("' + self.__str__() + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['p'][self._index]

    @property
    def name(self):
        """Return current parameter's name."""
        return self._not_in_subspans_split('|')[0]

    @property
    def pipe(self):
        """Return `|` if there is an pipe (default value in the argument.

         Return '' otherwise.
         """
        if len(self._not_in_subspans_splitspans('=')) > 1:
            return '='
        return ''

    @property
    def value(self):
        """Return value of a keyword argument."""
        return self._not_in_subspans_split('=')[1]


class ParserFunction(_Indexed_Object):

    """Use to represent a ParserFunction."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans, index)
        self._parse()

    def __repr__(self):
        """Return the string representation of the ParserFunction."""
        return 'ParserFunction("' + self.__str__() + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['pf'][self._index]

    def _parse(self):
        """Parse the ParserFunction."""
        barsplits = self._not_in_subspans_split('|')
        self.arguments = []
        self.name, arg1 = barsplits.pop(0)[2:].split(':')
        self.arguments.append(Argument(arg1))
        if barsplits:
            barsplits[-1] = barsplits[-1][:-2]
            for s in barsplits:
                self.arguments.append(Argument(s))
        else:
            self.arguments[0] = self.arguments[0][:-2]


class WikiLink(_Indexed_Object):

    """Use to represent WikiLinks."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans, index)

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'WikiLink("' + self.__str__() + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['wl'][self._index]

    @property
    def target(self):
        """Return target of this WikiLink."""
        return self.__str__()[2:-2].partition('|')[0]

    @property
    def text(self):
        """Return display text of this WikiLink."""
        target, pipe, text = self.__str__()[2:-2].partition('|')
        if pipe:
            return text


class Comment(_Indexed_Object):

    """Use to represent External Links."""

    def __init__(self, string, spans=None, index=None):
        """Detect named or keyword argument."""
        self._common_init(string, spans, index)

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'Comment("' + self.__str__() + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['c'][self._index]

    @property
    def contents(self):
        """Return contents of this comment."""
        return self.__str__()[4:-3]


class ExternalLink(_Indexed_Object):

    """Use to represent External Links."""

    def __init__(self, string, spans=None, index=None):
        """Detect named or keyword argument."""
        self._common_init(string, spans, index)
        if spans is None:
            self._spans['el'] = [(0, len(string))]

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'ExternalLink("' + self.__str__() + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['el'][self._index]
    
    @property
    def url(self):
        """Return the url part of the ExternalLink."""
        if self.in_brackets:
            return self.__str__()[1:-1].partition(' ')[0]
        return self.__str__()

    @property
    def text(self):
        """Return the display text of the external link.

        Return self.__str__() if this is a bare link.
        Return 
        """
        if self.in_brackets:
            return self.__str__()[1:-1].partition(' ')[2]
        return self.__str__()

    @property
    def in_brackets(self):
        """Return true if the ExternalLink is in brackets. False otherwise."""
        if self.__str__().startswith('['):
            return True
        return False

    def set_title(self, new_title):
        """Set the title to new_title.

        If the link is not in brackets, they will be added.
        """
        self.title = new_title
        self.string = '[' + self.url + ' ' + self.title + ']'

    def destroy(self):
        """Delete references this object from self._spans and self.lststr."""
        spanstart, spanend = self._get_span()
        self._remove_update(spanstart, spanend)
        self._spans['el'].pop(self._index)
        self._index = None

        
class Argument(_Indexed_Object):

    """Use to represent Template or ParserFunction arguments."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans, index)
        if spans is None:
            self._spans['a'] = [(0, len(string))]

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'Argument("' + self.__str__() + '")'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['a'][self._index]

    @property
    def name(self):
        """Return argument's name-part."""
        return self._not_in_subspans_split('=')[0]

    @property
    def equal_sign(self):
        """Return `=` if there is an equal sign in the argument. Else ''."""
        if len(self._not_in_subspans_splitspans('=')) > 1:
            return '='
        return ''

    @property
    def value(self):
        """Return value of a keyword argument."""
        return self._not_in_subspans_split('=')[1]

    def destroy(self):
        """Delete references this object from self._spans and self.lststr."""
        span = self._get_span()
        self._remove_update(span[0] - 1, span[1])
        self._spans['a'].pop(self._index)
        self._index = None
        

class Section(_Indexed_Object):

    """Use to represent wikitext Sections."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans, index)
        if spans is None:
            self._spans['s'] = [(0, len(string))]

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'Argument("' + self.__str__() + '")'

    def _get_span(self):
        """Return selfspan (span of self.__str__() in self._lststr[0])."""
        return self._spans['s'][self._index]

    @property
    def level(self):
        """Return level of this section. Level is in range(1,7)."""
        selfstring = self.__str__()
        m = SECTION_LEVEL_TITLE.match(selfstring)
        if not m:
            return 0
        return len(m.group(2))
            
    @property
    def title(self):
        """Return title of this section. Return '' for lead sections."""
        level = self.level
        if level == 0:
            return ''
        return self.__str__().partition('\n')[0].rstrip()[level:-level]

    @property
    def contents(self):
        if self.level == 0:
            return self.__str__()
        return self.__str__().partition('\n')[2]
