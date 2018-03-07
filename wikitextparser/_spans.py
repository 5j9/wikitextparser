"""Define the functions required for parsing wikitext into spans."""


from typing import Dict, List, Callable, Any, Optional

from regex import VERBOSE, IGNORECASE
from regex import compile as regex_compile


# According to https://www.mediawiki.org/wiki/Manual:$wgLegalTitleChars
# illegal title characters are: r'[]{}|#<>[\u0000-\u0020]'
VALID_TITLE_CHARS_PATTERN = rb'[^\x00-\x1f\|\{\}\[\]<>\n]++'
# Templates
TEMPLATE_FINDITER = regex_compile(
    rb'\{\{\s*+'
    # name
    + VALID_TITLE_CHARS_PATTERN + rb'''
    \s*+
    (?>\|[^{}]*+)?+  # optional args
    \}\}''',
    VERBOSE,
).finditer
INVALID_TL_NAME_FINDITER = regex_compile(
    rb'''
    \{\{
    [\s_]*+ # invalid name
    (?>\|[^{}]*)?+  # optional args
    \}\}
    ''',
    VERBOSE,
).finditer
# Parameters
PARAMETER_FINDITER = regex_compile(
    rb'''
    \{\{\{
    [^{}]*+
    \}\}\}
    ''',
    VERBOSE,
).finditer
# Parser functions
# According to https://www.mediawiki.org/wiki/Help:Magic_words
# See also:
# https://translatewiki.net/wiki/MediaWiki:Sp-translate-data-MagicWords/fa
PARSER_FUNCTION_FINDITER = regex_compile(
    rb'\{\{\s*+'
    # generated pattern: _config.regex_pattern(_config._parser_functions)
    # with \#[^{}\s:]++ added manually.
    rb'(?>\#[^{}\s:]++|u(?>rlencode|c(?:first)?+)|p(?>lural|ad(?>right|left))|'
    rb'nse?+|l(?>ocalurl|c(?:first)?+)|int|g(?>rammar|ender)|f(?>ullurl|ormatn'
    rb'um|ilepath)|canonicalurl|anchorencode|TALK(?>SPACEE?+|PAGENAMEE?+)|SUB('
    rb'?>PAGENAMEE?+|JECT(?>SPACEE?+|PAGENAMEE?+))|R(?>OOTPAGENAMEE?+|EVISION('
    rb'?>YEAR|USER|TIMESTAMP|MONTH1?+|ID|DAY2?+))|P(?>ROTECTION(?>LEVEL|EXPIRY'
    rb')|AGE(?>SI(?>ZE|N(?>N(?>S|AMESPACE)|CAT(?:EGORY)?+))|NAMEE?+|ID))|N(?>U'
    rb'M(?>INGROUP|BER(?>OF(?>VIEWS|USERS|PAGES|FILES|EDITS|A(?>RTICLES|DMINS|'
    rb'CTIVEUSERS))|INGROUP))|AMESPACE(?>NUMBER|E)?+)|FULLPAGENAMEE?+|D(?>ISPL'
    rb'AYTITLE|EFAULT(?>SORT(?:KEY)?+|CATEGORYSORT))|CASCADINGSOURCES|BASEPAGE'
    rb'NAMEE?+|ARTICLE(?>SPACEE?+|PAGENAMEE?+))'
    # end of generated part
    rb':[^{}]*+\}\}',
).finditer
# External links
INVALID_EXTLINK_CHARS = rb' \t\n<>\[\]"'
VALID_EXTLINK_CHARS = rb'[^' + INVALID_EXTLINK_CHARS + rb']++'

# generated pattern: _config.regex_pattern(_config._bare_external_link_schemes)
BARE_EXTLINK_SCHEMES_PATTERN = (
    rb'(?>xmpp:|worldwind://|urn:|tel(?>net://|:)|s(?>vn://|sh://|ms:|ip(?>s:|'
    rb':)|ftp://)|redis://|n(?>ntp://|ews:)|m(?>ms://|a(?>ilto:|gnet:))|irc(?>'
    rb's://|://)|http(?>s://|://)|g(?>opher://|it://|eo:)|ftp(?>s://|://)|bitc'
    rb'oin:)'
)
BARE_EXTERNALLINK_PATTERN = (
    rb'(?>' + BARE_EXTLINK_SCHEMES_PATTERN + rb')' + VALID_EXTLINK_CHARS
)
# Wikilinks
# https://www.mediawiki.org/wiki/Help:Links#Internal_links
WIKILINK_FINDITER = regex_compile(
    rb'''
    \[\[
    (?!\ *+''' + BARE_EXTERNALLINK_PATTERN + rb')'
    + VALID_TITLE_CHARS_PATTERN.replace(rb'\{\}', rb'', 1) + rb'''
    (?:
        \]\]
        |
        \| # Text of the wikilink
        (?> # Any character that is not the start of another wikilink
            [^[\]]+
            |
            \[(?!\[)
            |
            # this group is lazy, therefore \] is not followed by another \]
            \]
        )*?
        \]\]
    )
    ''',
    IGNORECASE | VERBOSE,
).finditer

# generated pattern: _config.regex_pattern(_config._parsable_tag_extensions)
PARSABLE_TAG_EXTENSIONS_PATTERN = (
    rb'(?>section|ref(?:erences)?+|poem|i(?>n(?>putbox|dicator|cludeonly)|mage'
    rb'map)|gallery|categorytree)'
)
# generated pattern: _config.regex_pattern(_config._unparsable_tag_extensions)
UNPARSABLE_TAG_EXTENSIONS_PATTERN = (
    rb'(?>t(?>imeline|emplatedata)|s(?>yntaxhighlight|ource|core)|pre|nowiki|m'
    rb'ath|hiero|graph|charinsert)'
)
TAG_BY_NAME_PATTERN = (
    rb'< (' + UNPARSABLE_TAG_EXTENSIONS_PATTERN + rb'|(' +
    PARSABLE_TAG_EXTENSIONS_PATTERN + rb''')) \b [^>]*+ (?<!/)>
    # content
    (?>
        # Contains no other tags or
        [^<]++
        |
        # the nested-tag is something else or
        < (?! \1 \b [^>]*+ >)
        |
        # the nested tag closes itself
        <\1\b[^>]*/>
    )*?
    # tag-end
    </\1\s*+>'''
)

# The idea of the following regex is to detect innermost HTML tags. From
# http://blog.stevenlevithan.com/archives/match-innermost-html-element
# But it's not bullet proof:
# https://stackoverflow.com/questions/3076219/
EXTENSION_TAGS_FINDITER = regex_compile(
    TAG_BY_NAME_PATTERN,
    IGNORECASE | VERBOSE,
).finditer
COMMENT_PATTERN = r'<!--(?>[^-]++|-(?!->))*+-->'
COMMENT_FINDITER = regex_compile(COMMENT_PATTERN.encode()).finditer
SINGLE_BRACES_FINDITER = regex_compile(
    rb'''
    (?<!{) { (?=[^{|])
    |
    (?<![|}]) } (?=[^}])
    ''',
    VERBOSE,
).finditer


def parse_to_spans(byte_array: bytearray) -> Dict[str, List[List[int]]]:
    """Calculate and set self._type_to_spans.

    The result is a dictionary containing lists of spans:
    {
        'Comment': comment_spans,
        'ExtTag': extension_tag_spans,
        'Parameter': parameter_spans,
        'ParserFunction': parser_function_spans,
        'Template': template_spans,
        'WikiLink': wikilink_spans,
    }

    """
    comment_spans = []  # type: List[List[int]]
    comment_spans_append = comment_spans.append
    extension_tag_spans = []  # type: List[List[int]]
    extension_tag_spans_append = extension_tag_spans.append
    wikilink_spans = []  # type: List[List[int]]
    wikilink_spans_append = wikilink_spans.append
    parameter_spans = []  # type: List[List[int]]
    parameter_spans_append = parameter_spans.append
    parser_function_spans = []  # type: List[List[int]]
    parser_function_spans_append = parser_function_spans.append
    template_spans = []  # type: List[List[int]]
    template_spans_append = template_spans.append
    # HTML <!-- comments -->
    for match in COMMENT_FINDITER(byte_array):
        ms, me = match.span()
        comment_spans_append([ms, me])
        byte_array[ms:me] = b' ' * (me - ms)
    # <extension tags>
    for match in EXTENSION_TAGS_FINDITER(byte_array):
        ms, me = match.span()
        extension_tag_spans_append([ms, me])
        if match[2]:  # parsable tag extension group
            parse_tag_extensions(
                byte_array, ms, me,
                wikilink_spans_append,
                parameter_spans_append,
                parser_function_spans_append,
                template_spans_append,
            )
        byte_array[ms:me] = b'_' * (me - ms)
    # Remove the braces inside WikiLinks.
    # WikiLinks may contain braces that interfere with
    # detection of templates. For example when parsing `{{text |[[A|}}]] }}`,
    # the span of the template should be the whole byte_array.
    match = True
    while match:
        match = False
        for match in WIKILINK_FINDITER(byte_array):
            ms, me = match.span()
            wikilink_spans_append([ms, me])
            parse_pm_tl_pf(
                byte_array, ms, me,
                parameter_spans_append,
                parser_function_spans_append,
                template_spans_append,
            )
            byte_array[ms:me] = b'_' * (me - ms)
    parse_pm_tl_pf(
        byte_array, 0, None,
        parameter_spans_append,
        parser_function_spans_append,
        template_spans_append,
    )
    return {
        'Comment': sorted(comment_spans),
        'ExtensionTag': sorted(extension_tag_spans),
        'Parameter': sorted(parameter_spans),
        'ParserFunction': sorted(parser_function_spans),
        'Template': sorted(template_spans),
        'WikiLink': sorted(wikilink_spans),
    }


def parse_tag_extensions(
    byte_array: bytearray,
    start: int,
    end: int,
    wikilink_spans_append: Callable,
    parameter_spans_append: Callable,
    pfunction_spans_append: Callable,
    template_spans_append: Callable,
) -> None:
    """Parse the byte_array to spans.

    This function is basically the same as `parse_to_spans`, but accepts an
    start that indicates the starting start of the given byte_array.
    `byte_array`s that are passed to this function are the contents of
    PARSABLE_TAG_EXTENSIONS.

    """
    match = True  # type: Any
    while match:
        match = False
        for match in WIKILINK_FINDITER(byte_array, start, end):
            ms, me = match.span()
            wikilink_spans_append([ms, me])
            # See if the other WIKILINK_FINDITER call can help.
            parse_pm_tl_pf(
                byte_array, ms, me,
                parameter_spans_append,
                pfunction_spans_append,
                template_spans_append,
            )
            byte_array[ms:me] = b'_' * (me - ms)
    parse_pm_tl_pf(
        byte_array, start, end,
        parameter_spans_append,
        pfunction_spans_append,
        template_spans_append,
    )


def parse_pm_tl_pf(
    byte_array: bytearray, start: int, end: Optional[int],
    parameter_spans_append: Callable,
    pfunction_spans_append: Callable,
    template_spans_append: Callable,
) -> None:
    """Find the spans of parameters, parser functions, and templates.

    :byte_array: The byte_array or part of byte_array that is being parsed.
    :start: Add to every returned start.

    This is the innermost loop of the parse_to_spans function.
    If the byte_array passed to parse_to_spans contains n WikiLinks, then
    this function will be called n + 1 times. One time for the whole byte_array
    and n times for each of the n WikiLinks.

    """
    # Remove empty double braces
    match = True  # type: Any
    while match:
        match = False
        for match in INVALID_TL_NAME_FINDITER(byte_array, start, end):
            ms, me = match.span()
            byte_array[ms:me] = (me - ms) * b'_'
    ms = True
    while ms is not None:
        # Single braces will interfere with detection of other elements and
        # should be removed beforehand.
        for m in SINGLE_BRACES_FINDITER(byte_array, start, end):
            byte_array[m.start()] = 95  # 95 == ord('_')
        ms = None
        # Parser functions
        match = True
        while match:
            match = False
            for match in PARSER_FUNCTION_FINDITER(byte_array, start, end):
                ms, me = match.span()
                pfunction_spans_append([ms, me])
                byte_array[ms:me] = b'_' * (me - ms)
        # Parameters
        match = True
        while match:
            match = False
            for match in PARAMETER_FINDITER(byte_array, start, end):
                ms, me = match.span()
                parameter_spans_append([ms, me])
                byte_array[ms:me] = b'_' * (me - ms)
        # Templates
        # match is False at this point
        for match in TEMPLATE_FINDITER(byte_array, start, end):
            ms, me = match.span()
            template_spans_append([ms, me])
            byte_array[ms:me] = b'_' * (me - ms)
