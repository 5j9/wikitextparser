﻿"""Define the functions required for parsing wikitext into spans."""


from typing import Dict, List, Tuple

import regex


# According to https://www.mediawiki.org/wiki/Manual:$wgLegalTitleChars
# illegal title characters are: r'[]{}|#<>[\u0000-\u0020]'
INVALID_TITLE_CHARS_PATTERN = rb'\x00-\x1f\|\{\}\[\]<>\n'
# Templates
TEMPLATE_PATTERN = (
    rb'''
    \{\{
    (?>\s*[^%1s]*\s*)
    (?>
        \|(?>[^{}]*)\}\}
        |
        \}\}
    )
    ''' % INVALID_TITLE_CHARS_PATTERN
)
INVALID_NAME_TEMPLATE_REGEX = regex.compile(
    rb'''
    \{\{
    (?>[\s_]*)
    (?>
        \|(?>[^{}]*)\}\}
        |
        \}\}
    )
    ''',
    regex.VERBOSE,
)
TEMPLATE_NOT_PARAM_REGEX = regex.compile(
    rb''' %s (?!\})  |  (?<!{) %s ''' % (
        TEMPLATE_PATTERN,
        TEMPLATE_PATTERN,
    ),
    regex.VERBOSE,
)
# Parameters
TEMPLATE_PARAMETER_REGEX = regex.compile(
    rb'''
    \{\{\{
    (?>[^{}]*)
    \}\}\}
    ''',
    regex.VERBOSE,
)
# Parser functions
# According to https://www.mediawiki.org/wiki/Help:Magic_words
# See also:
# https://translatewiki.net/wiki/MediaWiki:Sp-translate-data-MagicWords/fa
PARSER_FUNCTION_REGEX = regex.compile(
    rb"""
    \{\{\s*
    (?:
        \#[^{}\s]*?
        |
        # Variables acting like parser functions
        # Technical metadata
        DISPLAYTITLE|
        DEFAULT(?>CATEGORYSORT|SORTKEY|SORT)|
        # Statistics
        # The following variables accept ":R" flag
        NUM
        (?>
            BER
            (?>
                OF
                (?>PAGES|ARTICLES|FILES|EDITS|VIEWS|USERS|ADMINS|ACTIVEUSERS)|
                INGROUP
            )|
            INGROUP
        )|
        PAGESIN
        (?:CATEGORY|CAT|NS|NAMESPACE)|
        # Page names
        # These can all take a parameter, allowing
        # specification of the page to be operated on
        (?:
            (?:FULL)?|
            (?>
                SUB(?:JECT)?|
                BASE|
                ARTICLE|
                TALK|
                ROOT
            )
        )
        PAGENAMEE?|
        # Namespaces
        # Can take a full-page-name parameter
        (?>
            NAME|SUBJECT|ARTICLE|TALK
        )SPACEE?|
        NAMESPACENUMBER|
        # Parser functions
        # Technical metadata of another page
        PAGE(?>ID|SIZE)|
        PROTECTION(?>LEVEL|EXPIRY)|
        CASCADINGSOURCES|
        REVISION(?>ID|DAY2?|MONTH1?|YEAR|TIMESTAMP|USER)|
        # URL data
        (?>local|full|canonical)
        url|
        filepath|
        (?>url|anchor)encode|
        # Namespaces
        nse?|
        # Formatting
        formatnum|
        [lu]c(?:first)?|
        pad(?>left|right)|
        # Localization
        plural|
        grammar|
        gender|
        int
    )
    :[^{}]*?\}\}
    """,
    regex.VERBOSE
)
# External links
VALID_EXTLINK_CHARS_PATTERN = r'(?>[^ \\^`#<>\[\]\"\t\n{|}]*)'
# See DefaultSettings.php on MediaWiki and
# https://www.mediawiki.org/wiki/Help:Links#External_links
VALID_EXTLINK_SCHEMES_PATTERN = (
    r'''
    (?:
    http://|https://|ftp://|ftps://|bitcoin:|
    irc://|ircs://|magnet:|mailto:|mms://|news:|
    git://|geo:|gopher://|
    nntp://|redis://|
    sftp://|sip:|sips:|sms:|ssh://|svn://|tel:|telnet://|urn:|
    worldwind://|xmpp:|//
    )
    '''
)
BARE_EXTERNALLINK_PATTERN = (
    VALID_EXTLINK_SCHEMES_PATTERN.replace(r'|//', r'') +
    VALID_EXTLINK_CHARS_PATTERN
)
# Wikilinks
# https://www.mediawiki.org/wiki/Help:Links#Internal_links
WIKILINK_REGEX = regex.compile(
    rb'''
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
        BARE_EXTERNALLINK_PATTERN.encode(),
        INVALID_TITLE_CHARS_PATTERN.replace(rb'\{\}', b'')
    ),
    regex.IGNORECASE | regex.VERBOSE,
)
# For a complete list of extension tags on your wiki, see the
# "Parser extension tags" section at the end of [[Special:Version]].
# <templatedata> and <includeonly> were manually added to the  following list.
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
    'indicator',
]
# The idea of the following regex is to detect innermost HTML tags. From
# http://blog.stevenlevithan.com/archives/match-innermost-html-element
# But probably not bullet proof:
# https://stackoverflow.com/questions/3076219/
# Todo: Will this fail if the extension tag has a "<"?
EXTENSION_TAGS_REGEX = regex.compile(
    rb"""
    < ((?>%s)) \b (?>[^>]*) (?<!/)>
    # content
    (?:
        # Contains no other tags
        (?= ([^<]+) ) \2
        |
        # the nested-tag is something else
        < (?! \1 \b (?>[^>]*) >)
        |
        # the nested tag closes itself
        <\1\b[^>]*/>
    )*?
    # tag-end
    </\1\s*>
    """ % '|'.join(TAG_EXTENSIONS).encode(),
    regex.IGNORECASE | regex.VERBOSE,
)
# Contents of the some of the tags mentioned above can be parsed as wikitext.
# For example, templates are valid inside the poem tag:
#    <poem>{{text|Hi!}}</poem>
# But not within math or source or ...
# for more information about the <categorytree> tag see:
# https://www.mediawiki.org/wiki/Extension:CategoryTree#
#    The_.7B.7B.23categorytree.7D.7D_parser_function
PARSABLE_TAG_EXTENSIONS = [
    b'ref',
    b'poem',
    b'includeonly',
    b'categorytree',
    b'references',
    b'imagemap',
    b'inputbox',
    b'section',
    b'gallery',
    b'indicator',
]
COMMENT_REGEX = regex.compile(
    rb'<!--.*?-->',
    regex.DOTALL,
)
SINGLE_BRACES_REGEX = regex.compile(
    rb'''
    (?<!{) { (?=[^{])
    |
    (?<!}) } (?=[^}])
    ''',
    regex.VERBOSE,
)


def parse_to_spans(
    string: str
) -> Dict[str, List[Tuple[int, int]]]:
    """Calculate and set self._type_to_spans.

    The result is a dictionary containing lists of spans:
    {
        'Parameter': parameter_spans,
        'ParserFunction': parser_function_spans,
        'Template': template_spans,
        'Wikilink': wikilink_spans,
        'Comment': comment_spans,
        'ExtTag': extension_tag_spans,
    }

    """
    byte_array = bytearray(string.encode('ascii', 'replace'))
    comment_spans = []
    extension_tag_spans = []
    wikilink_spans = []
    parameter_spans = []
    parser_function_spans = []
    template_spans = []
    # HTML <!-- comments -->
    for match in COMMENT_REGEX.finditer(byte_array):
        # Todo: Parse comments?
        mspan = match.span()
        comment_spans.append(mspan)
        ms, me = mspan
        byte_array[ms:me] = b' ' * (me - ms)
    # <extension tags>
    for match in EXTENSION_TAGS_REGEX.finditer(byte_array):
        mspan = match.span()
        extension_tag_spans.append(mspan)
        ms, me = mspan
        group = match.group()
        group_startswith = group.startswith
        if any(
            (group_startswith(b'<' + pte) for pte in PARSABLE_TAG_EXTENSIONS)
        ):
            parse_subbytes_to_spans(
                byte_array[ms + 3:me - 3],
                ms + 3,
                wikilink_spans,
                parameter_spans,
                parser_function_spans,
                template_spans,
            )
        byte_array[ms:me] = b'_' * (me - ms)
    # Remove the braces inside WikiLinks.
    # WikiLinks may contain braces that interfere with
    # detection of templates. For example when parsing `{{text |[[A|}}]] }}`,
    # the span of the template should be the whole byte_array.
    loop = True
    while loop:
        loop = False
        for match in WIKILINK_REGEX.finditer(byte_array):
            loop = True
            mspan = match.span()
            wikilink_spans.append(mspan)
            ms, me = mspan
            group = byte_array[ms:me]
            parse_to_spans_innerloop(
                group,
                ms,
                parameter_spans,
                parser_function_spans,
                template_spans,
            )
            byte_array[ms:me] = (
                b'_[' + group[2:-2].replace(b'{', b'_').replace(b'}', b'_') +
                b']_'
            )
    parse_to_spans_innerloop(
        byte_array,
        0,
        parameter_spans,
        parser_function_spans,
        template_spans,
    )
    return {
        'Parameter': parameter_spans,
        'ParserFunction': parser_function_spans,
        'Template': template_spans,
        'WikiLink': wikilink_spans,
        'Comment': comment_spans,
        'ExtTag': extension_tag_spans,
    }


def parse_subbytes_to_spans(
    byte_array: bytearray,
    index: int,
    wikilink_spans: list,
    parameter_spans: list,
    parser_function_spans: list,
    template_spans: list,
) -> None:
    """Parse the byte_array to spans.

    This function is basically the same as `parse_to_spans`, but accepts an
    index that indicates the start of the byte_array. `byte_array`s are the
    contents of PARSABLE_TAG_EXTENSIONS.

    """
    # Remove the braces inside WikiLinks.
    # WikiLinks may contain braces that interfere with
    # detection of templates. For example when parsing `{{text |[[A|}}]] }}`,
    # the span of the template should be the whole string.
    loop = True
    while loop:
        loop = False
        for match in WIKILINK_REGEX.finditer(byte_array):
            loop = True
            ms, me = match.span()
            wikilink_spans.append((index + ms, index + me))
            group = byte_array[ms:me]
            parse_to_spans_innerloop(
                group,
                index + ms,
                parameter_spans,
                parser_function_spans,
                template_spans,
            )
            byte_array[ms:me] = (
                b'_[' + group[2:-2].replace(b'{', b'_').replace(b'}', b'_') +
                b']_'
            )
    parse_to_spans_innerloop(
        byte_array,
        index,
        parameter_spans,
        parser_function_spans,
        template_spans,
    )


def parse_to_spans_innerloop(
    byte_array: bytearray,
    index: int,
    parameter_spans: list,
    parser_function_spans: list,
    template_spans: list,
) -> None:
    """Find the spans of parameters, parser functions, and templates.

    :byte_array: The byte_array or part of byte_array that is being parsed.
    :index: Add to every returned index.

    This is the innermost loop of the parse_to_spans function.
    If the byte_array passed to parse_to_spans contains n WikiLinks, then
    this function will be called n + 1 times. One time for the whole byte_array
    and n times for each of the n WikiLinks.

    """
    while True:
        # Single braces will interfere with detection of other elements and
        # should be removed beforehand.
        for m in SINGLE_BRACES_REGEX.finditer(byte_array):
            byte_array[m.start()] = 95  # 95 = ord('_')
        # Also remove empty double braces
        loop = True
        while loop:
            loop = False
            for match in INVALID_NAME_TEMPLATE_REGEX.finditer(byte_array):
                loop = True
                ms, me = match.span()
                byte_array[ms:me] = (me - ms) * b'_'
        i = byte_array.rfind(125)  # 125 == ord('}')
        if i != -1:
            byte_array[i:] = byte_array[i:].replace(b'{', b'_')
        i = byte_array.find(123)
        if i != -1:
            byte_array[:i] = byte_array[:i].replace(b'}', b'_')
        match = None
        # Template parameters
        loop = True
        while loop:
            loop = False
            for match in TEMPLATE_PARAMETER_REGEX.finditer(byte_array):
                loop = True
                ms, me = match.span()
                parameter_spans.append((ms + index, me + index))
                byte_array[ms:ms + 2] = b'__'
                byte_array[me - 2:me] = b'__'
        # Templates
        loop = True
        while loop:
            # Parser functions
            while loop:
                loop = False
                for match in PARSER_FUNCTION_REGEX.finditer(byte_array):
                    loop = True
                    ms, me = match.span()
                    parser_function_spans.append((ms + index, me + index))
                    byte_array[ms:ms + 2] = b'__'
                    byte_array[me - 2:me] = b'__'
            # loop is False at this point
            for match in TEMPLATE_NOT_PARAM_REGEX.finditer(byte_array):
                loop = True
                ms, me = match.span()
                template_spans.append((ms + index, me + index))
                byte_array[ms:ms + 2] = b'__'
                byte_array[me - 2:me] = b'__'
        if not match:
            break
