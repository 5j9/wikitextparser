"""Functions to parse WikiText into spans."""


import re


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
PARSER_FUNCTION_NAME_PATTERN = r'#[^{}\s]*?:'
PARSER_FUNCTION_REGEX = re.compile(
    r'\{\{\s*' + PARSER_FUNCTION_NAME_PATTERN + r'[^{}]*?\}\}'
)
# Wikilinks
# https://www.mediawiki.org/wiki/Help:Links#Internal_links
WIKILINK_REGEX = re.compile(
    r'\[\[' + VALID_TITLE_CHARS_PATTERN.replace(r'\{\}', '') +
    r'(\]\]|\|[\S\s]*?\]\])'
)
# For a complete list of extension tags on your wiki, see the
# "Parser extension tags" section at the end of [[Special:Version]].
# <templatedata> and <includeonly> are added manually.
# A simple trick to find out if a tag should be listed here or not is as
# follows:
# Create the {{text}} template in your wiki (You can copy the source code from
# English Wikipedia). Then save the following in test page:
# {{text|0<tagname>1}}2</tagname>3}}4
# If the ending braces in the redered result appear between 3 and 4, then
# `tagname` is not an extension (e.g. <small>). Otherwise, i.e. if those
# braces appear between 1 and 2 or completely don't show up, `tagname` is
# probably an extension tag (e.g.: <pre>).
TAG_EXTENSIONS = [
    'ref',
    'math',
    'source',
    'syntaxhighlight',
    'pre',
    'poem',
    'hiero',
    'score',
    'includeonly',
    'timeline',
    'nowiki',
    'categorytree',
    'charinsert',
    'references',
    'imagemap',
    'inputbox',
    'section',
    'templatedata',
    'gallery',
    'graph',
    'imagemap',
    'indicator',
]
COMMENT_REGEX = re.compile(
    r'<!--.*?-->',
    re.DOTALL,
)
EXTENSION_TAGS_REGEX = re.compile(
    r'<(' + '|'.join(TAG_EXTENSIONS)+ r')\s*.*?>.*?</\1\s*>',
    re.DOTALL|re.IGNORECASE,
)
HTML_TAG_REGEX = re.compile(
    r'<([A-Z][A-Z0-9]*)\b[^>]*>(.*?)</\1>',
    re.DOTALL|re.IGNORECASE,
)


def parse_to_spans(string):
    """Calculate and set self._spans.

    The result a dictionary containing lists of spans:
    {
        'p': parameter_spans,
        'pf': parser_function_spans,
        't': template_spans,
        'wl': wikilink_spans,
        'c': comment_spans,
        'et': extension_tag_spans,
    }
    """
    # HTML <!-- comments -->
    comment_spans = []
    for match in COMMENT_REGEX.finditer(string):
        comment_spans.append(match.span())
        group = match.group()
        string = string.replace(group, '_' * len(group))
    # <extension tags>
    extension_tag_spans = []
    for match in EXTENSION_TAGS_REGEX.finditer(string):
        extension_tag_spans.append(match.span())
        group = match.group()
        string = string.replace(group, '_' * len(group))
    # The title in WikiLinks may contain braces that interfere with
    # detection of templates
    wikilink_spans = []
    parameter_spans = []
    parser_function_spans = []
    template_spans = []
    for match in WIKILINK_REGEX.finditer(string):
        span = match.span()
        wikilink_spans.append(span)
        group = match.group()
        parameter_spans, parser_function_spans, template_spans = innerloop(
            group,
            span[0],
            parameter_spans,
            parser_function_spans,
            template_spans,
        )
        string = string.replace(
            group,
            group.replace('}', '_').replace('{', '_'),
        )
    parameter_spans, parser_function_spans, template_spans = innerloop(
        string,
        0,
        parameter_spans,
        parser_function_spans,
        template_spans,
    )
    return {
        'p': parameter_spans,
        'pf': parser_function_spans,
        't': template_spans,
        'wl': wikilink_spans,
        'c': comment_spans,
        'et': extension_tag_spans,
    }

def innerloop(
    string,
    index,
    parameter_spans,
    parser_function_spans,
    template_spans
):
    """Run the main loop for _get_spans.

    `string`: The string or part of string that we are looking up.
    `index`: Add to every returned index.
    
    This function was created because the _get_spans function needs to
    call it n + 1 time. One time for the whole string and n times for
    each of the n WikiLinks.
    """
    
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
                ss, se = match.span()
                parameter_spans.append((ss + index, se + index))
                group = match.group()
                string = string.replace(group, '___' + group[3:-3] + '___')
        # Templates
        loop = True
        while loop:
            # Parser fucntions
            while loop:
                loop = False
                for match in PARSER_FUNCTION_REGEX.finditer(string):
                    loop = True
                    ss, se = match.span()
                    parser_function_spans.append((ss + index, se + index))
                    group = match.group()
                    string = string.replace(
                        group, '__' + group[2:-2] + '__'
                    )
            # loop is False at this point
            for match in TEMPLATE_NOT_PARAM_REGEX.finditer(string):
                loop = True
                ss, se = match.span()
                template_spans.append((ss + index, se + index))
                group = match.group()
                string = string.replace(group, '__' + group[2:-2] + '__' )
        if not match:
            break
    return parameter_spans, parser_function_spans, template_spans
