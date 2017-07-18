"""Define the functions required for parsing wikitext into spans."""


from typing import Dict, List, Callable, Any, Optional

from regex import VERBOSE, DOTALL, IGNORECASE
from regex import compile as regex_compile
from re import compile as re_compile


# According to https://www.mediawiki.org/wiki/Manual:$wgLegalTitleChars
# illegal title characters are: r'[]{}|#<>[\u0000-\u0020]'
INVALID_TITLE_CHARS_PATTERN = r'\x00-\x1f\|\{\}\[\]<>\n'
# Templates
TEMPLATE_PATTERN = (
    r'''
    \{\{
    (?>\s*[^%1s]*\s*)  # name
    (?>\|[^{}]*)?  # optional args
    \}\}
    ''' % INVALID_TITLE_CHARS_PATTERN
)
INVALID_TL_NAME_FINDITER = regex_compile(
    rb'''
    \{\{
    (?>[\s_]*) # invalid name
    (?>\|[^{}]*)?  # optional args
    \}\}
    ''',
    VERBOSE,
).finditer
TEMPLATE_NOT_PARAM_FINDITER = regex_compile(
    (r'%s (?!\})  |  (?<!{) %s' % (
        TEMPLATE_PATTERN,
        TEMPLATE_PATTERN,
    )).encode(),
    VERBOSE,
).finditer
# Parameters
PARAMETER_FINDITER = regex_compile(
    rb'''
    \{\{\{
    (?>[^{}]*)
    \}\}\}
    ''',
    VERBOSE,
).finditer
# Parser functions
# According to https://www.mediawiki.org/wiki/Help:Magic_words
# See also:
# https://translatewiki.net/wiki/MediaWiki:Sp-translate-data-MagicWords/fa
PARSER_FUNCTION_FINDITER = regex_compile(
    rb"""
    \{\{\s*
    (?>
        \#[^{}\s:]*
        |ARTICLE(?>PAGENAMEE?|SPACEE?)
        |BASEPAGENAMEE?
        |CASCADINGSOURCES
        |D(?>
            ISPLAYTITLE
            |EFAULT(?>CATEGORYSORT|SORT(?:KEY)?)
        )
        |FULLPAGENAMEE?
        |P(?>
            AGE(?>
                ID
                |SI(?>
                    ZE
                    |N(?>
                        CAT(?:EGORY)?
                        |N(?>S|AMESPACE)
                    )
                )
                |NAMEE?
            )
            |ROTECTION(?>LEVEL|EXPIRY)
        )
        |ROOTPAGENAMEE?
        |N(?>
            AMESPACE(?>NUMBER|E?)
            |UM(?>
                BER(?>
                    OF(?>
                        A(?>CTIVEUSERS|DMINS|RTICLES)
                        |EDITS
                        |FILES
                        |PAGES
                        |USERS
                        |VIEWS
                    )
                    |INGROUP
                )
                |INGROUP
            )
        )
        |REVISION(?>DAY2?|ID|MONTH1?|TIMESTAMP|USER|YEAR)
        |SUB(?>
            JECT(?>SPACEE?|PAGENAMEE?)
            |PAGENAMEE?
        )
        |TALK(?>PAGENAMEE?|SPACEE?)
        |anchorencode
        |canonicalurl
        |f(?>
            ilepath
            |ormatnum
            |ullurl
        )
        |g(?>
            rammar
            |ender
        )
        |int
        |l(?>
            c(?:first)?
            |ocalurl
        )
        |nse?
        |p(?>
            ad(?>left|right)
            |lural
        )
        |u(?>
            c(?:first)?
            |rlencode
        )
    )
    :[^{}]*\}\}
    """,
    VERBOSE
).finditer
# External links
VALID_EXTLINK_CHARS_PATTERN = r'(?>[^ \\^`#<>\[\]\"\t\n{|}]*)'
# See DefaultSettings.php on MediaWiki and
# https://www.mediawiki.org/wiki/Help:Links#External_links
VALID_EXTLINK_SCHEMES_PATTERN = r'''
    (?>
        //
        |bitcoin:
        |ftp(?>://|s://)
        |g(?>eo:|it://|opher://)
        |http(?>://|s://)
        |irc(?>://|s://)
        |m(?>
            a(?>gnet:|ilto:)
            |ms://
        )
        |n(?>ews:|ntp://)
        |redis://
        |s(?>
            ftp://
            |ip(?>:|s:)
            |ms:
            |sh://
            |vn://
        )
        |tel(?>:||net://)
        |urn:
        |worldwind://
        |xmpp:
    )
'''
BARE_EXTERNALLINK_PATTERN = (
    VALID_EXTLINK_SCHEMES_PATTERN.replace('//\n        |', '') +
    VALID_EXTLINK_CHARS_PATTERN
)
# Wikilinks
# https://www.mediawiki.org/wiki/Help:Links#Internal_links
WIKILINK_FINDITER = regex_compile((
    r'''
    \[\[
    (?!%s)
    (?>[^%s]*)
    (
        \]\]
        |
        \| # Text of the wikilink
        (?>
            # Any character that is not the start of another wikilink
            (?!\[\[)[\S\s]
        )*?
        \]\]
    )
    ''' % (
        BARE_EXTERNALLINK_PATTERN,
        INVALID_TITLE_CHARS_PATTERN.replace(r'\{\}', r'')
    )).encode(),
    IGNORECASE | VERBOSE,
).finditer
# For a complete list of extension tags on your wiki, see the
# "Parser extension tags" section at the end of [[Special:Version]].
# <templatedata> and <includeonly> were manually added to the  following lists.
# A simple trick to find out if a tag should be listed here or not is as
# follows:
# Create the {{text}} template in your wiki (You can copy the source code from
# English Wikipedia). Then save the following in a test page:
# {{text|0<tagname>1}}2</tagname>3}}4
# If the ending braces in the rendered result appear between 3 and 4, then
# `tagname` is not an extension tag (e.g. <small>). Otherwise, i.e. if those
# braces appear between 1 and 2 or completely don't show up, `tagname` is
# probably an extension tag (e.g.: <pre>).
TAG_EXTENSIONS = [
    'math',
    'source',
    'syntaxhighlight',
    'pre',
    'hiero',
    'score',
    'timeline',
    'nowiki',
    'charinsert',
    'templatedata',
    'graph',
]
# Contents of the some of the extension tags can be parsed as wikitext.
# For example, templates are valid inside the poem tag:
#    <poem>{{text|Hi!}}</poem>
# But not within math or source or ...
# for more information about the <categorytree> tag see:
# https://www.mediawiki.org/wiki/Extension:CategoryTree#
#    The_.7B.7B.23categorytree.7D.7D_parser_function
PARSABLE_TAG_EXTENSIONS = [
    'ref',
    'poem',
    'includeonly',
    'categorytree',
    'references',
    'imagemap',
    'inputbox',
    'section',
    'gallery',
    'indicator',
]
TAG_BY_NAME_PATTERN = (
    r"""
    # First group is the tag name
    # Second group is indicator for PARSABLE_TAG_EXTENSIONS
    < ((?>%s)|((?>%s))) \b (?>[^>]*) (?<!/)>
    # content
    (?>
        # Contains no other tags or
        (?>[^<]+)
        |
        # the nested-tag is something else or
        < (?! \1 \b (?>[^>]*) >)
        |
        # the nested tag closes itself
        <\1\b[^>]*/>
    )*?
    # tag-end
    </\1\s*>
    """
)
# The idea of the following regex is to detect innermost HTML tags. From
# http://blog.stevenlevithan.com/archives/match-innermost-html-element
# But probably not bullet proof:
# https://stackoverflow.com/questions/3076219/
EXTENSION_TAGS_FINDITER = regex_compile((
    TAG_BY_NAME_PATTERN % (
        '|'.join(TAG_EXTENSIONS), '|'.join(PARSABLE_TAG_EXTENSIONS)
    )).encode(),
    IGNORECASE | VERBOSE,
).finditer
COMMENT_FINDITER = re_compile(rb'<!--.*?-->', DOTALL).finditer
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
        'Parameter': parameter_spans,
        'ParserFunction': parser_function_spans,
        'Template': template_spans,
        'WikiLink': wikilink_spans,
        'Comment': comment_spans,
        'ExtTag': extension_tag_spans,
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
        'Parameter': parameter_spans,
        'ParserFunction': parser_function_spans,
        'Template': template_spans,
        'WikiLink': wikilink_spans,
        'Comment': comment_spans,
        'ExtTag': extension_tag_spans,
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
    # Remove the braces inside WikiLinks.
    # WikiLinks may contain braces that interfere with
    # detection of templates. For example when parsing `{{text |[[A|}}]] }}`,
    # the span of the template should be the whole string.
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
        # Template parameters
        match = True
        while match:
            match = False
            for match in PARAMETER_FINDITER(byte_array, start, end):
                ms, me = match.span()
                parameter_spans_append([ms, me])
                byte_array[ms:me] = b'_' * (me - ms)
        match = True
        while match:
            # Parser functions
            while match:
                match = False
                for match in PARSER_FUNCTION_FINDITER(byte_array, start, end):
                    ms, me = match.span()
                    pfunction_spans_append([ms, me])
                    byte_array[ms:me] = b'_' * (me - ms)
            # Templates
            # match is False at this point
            for match in TEMPLATE_NOT_PARAM_FINDITER(byte_array, start, end):
                ms, me = match.span()
                template_spans_append([ms, me])
                byte_array[ms:me] = b'_' * (me - ms)
