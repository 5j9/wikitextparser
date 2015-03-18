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

class WikiText:

    """Return a WikiText object."""

    def __init__(self, string, spans=None):
        """Initialize the object."""
        self.string = string
        if spans:
            self._spans = spans
        else:
            self._get_spans()

    def __repr__(self):
        """Return the string representation of the WikiText."""
        return 'WikiText("' + self.string + '")'

    def __str__(self):
        """Retrun result string."""
        return self.string

    def get_templates(self):
        """Return a list of templates as template objects."""
        return [
            Template(
                self.string[span[0]:span[1]],
                self._get_subspans(span),
            ) for span in self._spans[2]
        ]

    def get_parser_functions(self):
        """Return a list of parser function objects."""
        return [
            ParserFunction(
                self.string[span[0]:span[1]],
                self._get_subspans(span),
            ) for span in self._spans[1]
        ]
        

    def get_parameters(self):
        """Return a list of parameter objects."""
        return [
            Parameter(
                self.string[span[0]:span[1]],
                self._get_subspans(span),
            ) for span in self._spans[0]
        ]

    def get_wikilinks(self):
        """Return a list of wikilink objects."""
        return [
            Parameter(
                self.string[span[0]:span[1]],
                self._get_subspans(span),
            ) for span in self._spans[3]
        ]

    def get_external_links(self):
        """Return a list of external link objects."""
        return [
            ExternalLink(
                m.group(),
                self._get_subspans(m.span()),
            ) for m in EXTERNALLINK_REGEX.finditer(self.string)
        ]

    def get_comments(self):
        """Return a list of comment objects."""
        return [
            Comment(
                self.string[span[0]:span[1]],
                None,
            ) for span in self._spans[4]
        ]

    def _not_in_subspans_split(self, char):
        """Split self.string using `char` unless char is in ._spans."""
        string = self.string
        splits = []
        findstart = 0
        while True:
            index = string.find(char, findstart)
            while self._in_subspans(index):
                index = string.find(char, index + 1)
            if index == -1:
                return splits + [string[findstart:]]
            splits.append(string[findstart:index])
            findstart = index+1

    def _get_subspans(self, span):
        """Return a list of subpan_groups in self._spans.

        Start and end of the new subspans will be changed to match span.
        """
        subspan_groups = []
        for spans in self._spans:
            subspans = []
            for subspan in spans:
                if span[0] < subspan[0] and subspan[1] < span[1]:
                    subspans.append(
                        (subspan[0] - span[0], subspan[1] - span[0])
                    )
            subspan_groups.append(subspans)
        return subspan_groups

    def _in_subspans(self, index):
        """Return True if the given index is found within one of the subspan."""
        for spans in self._spans:
            for span in spans:
                if span[0] <= index < span[1]:
                    return True
        return False

    def _get_spans(self):
        """Return spans of elements.

        The result a tuple in containing lists of the following spans:
        (params, parser functions, templates, wikilinks).
        """
        string = self.string
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
        self._spans = (
            parameter_spans,
            parser_function_spans,
            template_spans,
            wikilink_spans,
            comment_spans,
        )
    

class Template(WikiText):

    """Convert strings to Template objects.

    The string should start with {{ and end with }}.
    """

    def __init__(
        self,
        template_string,
        spans=None,
        remove_duplicate_args=True,
    ):
        """Detect template name and arguments."""
        self.string = template_string
        if spans:
            self._spans = spans
        else:
            self._get_spans()
            self._spans[2].pop()
        self._parse()
        if remove_duplicate_args:
            self.remove_duplicate_arguments()

    def __repr__(self):
        """Return the string representation of the Template."""
        return 'Template("' + self.__str__() + '")'

    def __str__(self):
        """Retrun result string."""
        string = '{{' + self.name + '|'
        for a in self.arguments:
            string += ''.join(a.string) + '|'
        string = string[:-1] + '}}'
        return string

    def _parse(self):
        """Parse template content. Create self.name and self.arguments."""
        barsplits = self._not_in_subspans_split('|')
        self.name = barsplits.pop(0)[2:]
        self.arguments = []
        if barsplits:
            barsplits[-1] = barsplits[-1][:-2]
            for s in barsplits:
                self.arguments.append(Argument(s))
        else:
            self.name = self.name[:-2]

    def remove_duplicate_arguments(self):
        """Remove duplicate keyword arguments."""
        d = {}
        arguments = self.arguments
        for n, a in enumerate(self.arguments):
            an = a.name.strip()
            if an in d:
                arguments.pop(d[an])
            elif a.equal_sign:
                d[an] = n
        self.arguments = arguments
        # update attributes
        self._get_spans()
        self._spans[2].pop()
        self.string = self.__str__()


class Parameter(WikiText):

    """Use to represent {{{parameters}}}."""

    def __init__(self, param_string, spans=None):
        """Detect named and keyword parameters."""
        self.string = param_string
        if spans:
            self._spans = spans
        else:
            self._get_spans()
            self._spans[0].pop()
        self._parse()

    def __repr__(self):
        """Return the string representation of the Parameter."""
        return 'Parameter("' + self.string + '")'
    
    def _parse(self):
        """Parse the parameter."""
        self.name, pipe, self.default_value = self.string[3:-3].partition('|')


class ParserFunction(WikiText):

    """Use to represent a ParserFunction."""

    def __init__(self, function_string, spans=None):
        """Detect name and arguments."""
        self.string = function_string
        if spans:
            self._spans = spans
        else:
            self._get_spans()
            self._spans[1].pop()
        self._parse()

    def __repr__(self):
        """Return the string representation of the ParserFunction."""
        return 'ParserFunction("' + self.string + '")'

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

    
class Argument(WikiText):

    """Use to represent Templates or ParserFunction arguments."""

    def __init__(self, param_string, spans=None):
        """Detect named or keyword argument."""
        self.string = param_string
        if spans:
            self._spans = spans
        else:
            self._get_spans()
        self._parse()

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'Argument("' + self.string + '")'
    
    def _parse(self):
        """Parse the argument."""
        self.name, self.equal_sign, self.value = self.string.partition('=')


class WikiLink(WikiText):

    """Use to represent WikiLinks."""

    def __init__(self, wikilinkg_string, spans=None):
        """Detect named or keyword argument."""
        self.string = wikilinkg_string
        if spans:
            self._spans = spans
        else:
            self._get_spans()
            self._spans[3].pop()
        self._parse()

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'WikiLink("' + self.string + '")'
    
    def _parse(self):
        """Parse the WikiLink."""
        self.target, pipe, self.text = self.string[2:-2].partition('|')


class ExternalLink(WikiText):

    """Use to represent External Links."""

    def __init__(self, extlink_string, spans=None):
        """Detect named or keyword argument."""
        self.string = extlink_string
        if spans:
            self._spans = spans
        else:
            self._get_spans()
        self._parse()

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'ExtLink("' + self.string + '")'
    
    def _parse(self):
        """Parse the ExtLink."""
        string = self.string
        if string.startswith('['):
            self.brackets = True
            self.url, space, self.title = string[1:-1].partition(' ')
        else:
            self.url = string
            self.brackets = False

    def set_title(self, new_title):
        """Set the title to new_title.

        If the link is not in brackets, they will be added.
        """
        self.title = new_title
        self.string = '[' + self.url + ' ' + self.title + ']'

        
class Comment(WikiText):

    """Use to represent External Links."""

    def __init__(self, string, spans=None):
        """Detect named or keyword argument."""
        self.contents = string[4:-3]
        if spans:
            self._spans = spans
        else:
            self.string = '____' + self.contents + '___'
            self._get_spans()
        self.string = string

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'ExtLink("' + self.string + '")'
    
