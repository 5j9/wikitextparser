import re
from datetime import datetime
from pprint import pprint as pp
from timeit import timeit


# According to https://www.mediawiki.org/wiki/Manual:$wgLegalTitleChars
# illegal title characters are: r'[]{}|#<>[\u0000-\u0020]'
TEMPLATE_NAME_REGEX = r'[^\x00-\x1f\|\{\}\[\]<>\n]*'
TEMPLATE_REGEX = r'\{\{\s*' + TEMPLATE_NAME_REGEX  + r'\s*(\|[^{}]*?\}\}|\}\})'
TEMPLATE_NOT_PARAM_REGEX = re.compile(
    TEMPLATE_REGEX + r'(?!\})'
    r'|(?<!{)' + TEMPLATE_REGEX
)

TEMPLATE_PARAMETER_REGEX = re.compile(r'\{\{\{[^{}]*?\}\}\}')

PARSER_FUNCTION_NAME_REGEX = r'[^\s]*'
PARSER_FUNCTION_REGEX = re.compile(
    r'\{\{\s*#' + PARSER_FUNCTION_NAME_REGEX + r':[^{}]*?\}\}'
)


class WikiText:

    """Return a WikiText object."""

    def __init__(self, string, spans=None):
        """Initialize the object."""
        self.string = string
        if spans:
            self._ppft_spans = spans
        else:
            self._get_ppft_spans()

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
            ) for span in self._ppft_spans[2]
        ]

    def get_parser_functions(self):
        """Return a list of parser function objects."""
        return [
            ParserFunction(
                self.string[span[0]:span[1]],
                self._get_subspans(span),
            ) for span in self._ppft_spans[1]
        ]
        

    def get_parameters(self):
        """Return a list of parameter objects."""
        return [
            Parameter(
                self.string[span[0]:span[1]],
                self._get_subspans(span),
            ) for span in self._ppft_spans[0]
        ]

    def _not_in_subspans_split(self, char):
        """Split self.string using `char` unless char is in ._ppft_spans."""
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
        """Return a list of subpan_groups in self._ppft_spans.

        Start and end of the new subspans will be changed to match span.
        """
        subspan_groups = []
        for spans in self._ppft_spans:
            subspans = []
            for subspan in spans:
                if span[0] < subspan[0] and subspan[1] < span[1]:
                    subspans.append(
                        (subspan[0] - span[0], subspan[1] - span[0])
                    )
            subspan_groups.append(subspans)
        return subspan_groups

    def _get_indexes(self, char): # remove
        """Return a list for all index of char within the string."""
        return [i for i, ltr in enumerate(self.string) if ltr == char]

    def _in_subspans(self, index):
        """Return True if the given index is found within one of the subspan."""
        for spans in self._ppft_spans:
            for span in spans:
                if span[0] <= index < span[1]:
                    return True
        return False

    def _get_ppft_spans(self):
        """Return spans of (parameters, parser functions, templates)."""
        string = self.string
        parameter_spans = []
        parser_function_spans = []
        template_spans = []
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
            # The following conditional statement is not necessary
            # (performance?)
            if '{' not in string and '}' not in string:
                break
            match = None
            # Template parameters
            loop = True
            while loop:
                loop = False
                for match in TEMPLATE_PARAMETER_REGEX.finditer(string):
                    loop = True
                    parameter_spans.append(match.span())
                    group = match.group()
                    string = string.replace(group, '___' + group[3:-3] + '___' )
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
        self._ppft_spans = (
            parameter_spans,
            parser_function_spans,
            template_spans
        )
    

class Template(WikiText):

    """Convert strings to template objects.

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
            self._ppft_spans = spans
        else:
            self._get_ppft_spans()
            self._ppft_spans[2].pop()
        self.parse()
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

    def parse(self):
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
        self._get_ppft_spans()
        self._ppft_spans[2].pop()
        self.string = self.__str__()


class Parameter(WikiText):

    """Use to represent {{{parameters}}}."""

    def __init__(self, param_string, spans=None):
        """Detect named and keyword parameters."""
        self.string = param_string
        if spans:
            self._ppft_spans = spans
        else:
            self._get_ppft_spans()
            self._ppft_spans[0].pop()
        self.parse()

    def __repr__(self):
        """Return the string representation of the Parameter."""
        return 'Parameter("' + self.string + '")'
    
    def parse(self):
        """Parse the parameter."""
        self.name, pipe, self.default_value = self.string[3:-3].partition('|')


class ParserFunction(WikiText):

    """Use to represent a ParserFunction."""

    def __init__(self, function_string, spans=None):
        """Detect name and arguments."""
        self.string = function_string
        if spans:
            self._ppft_spans = spans
        else:
            self._get_ppft_spans()
            self._ppft_spans[1].pop()
        self.parse()

    def __repr__(self):
        """Return the string representation of the ParserFunction."""
        return 'ParserFunction("' + self.string + '")'

    def parse(self):
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
            self._ppft_spans = spans
        else:
            self._get_ppft_spans()
        self.parse()

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'Argument("' + self.string + '")'
    
    def parse(self):
        """Parse the argument."""
        self.name, self.equal_sign, self.value = self.string.partition('=')


