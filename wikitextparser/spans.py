"""Define the functions required for parsing wikitext into spans."""


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
        INVALID_TITLE_CHARS_PATTERN.replace(rb'\{\}', rb'')
    ),
    regex.IGNORECASE | regex.VERBOSE,
)
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
    b'math',
    b'source',
    b'syntaxhighlight',
    b'pre',
    b'hiero',
    b'score',
    b'timeline',
    b'nowiki',
    b'charinsert',
    b'templatedata',
    b'graph',
]
# Contents of the some of the extension tags can be parsed as wikitext.
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
# The idea of the following regex is to detect innermost HTML tags. From
# http://blog.stevenlevithan.com/archives/match-innermost-html-element
# But probably not bullet proof:
# https://stackoverflow.com/questions/3076219/
# Todo: Will this fail if the extension tag has a "<"?
EXTENSION_TAGS_REGEX = regex.compile(
    rb"""
    # First group is the tag name
    # Second groupd is indicator for PARSABLE_TAG_EXTENSIONS
    < ((?>%s)|((?>%s))) \b (?>[^>]*) (?<!/)>
    # content
    (?:
        # Contains no other tags
        (?>[^<]+)
        |
        # the nested-tag is something else
        < (?! \1 \b (?>[^>]*) >)
        |
        # the nested tag closes itself
        <\1\b[^>]*/>
    )*?
    # tag-end
    </\1\s*>
    """ % (b'|'.join(TAG_EXTENSIONS), b'|'.join(PARSABLE_TAG_EXTENSIONS)),
    regex.IGNORECASE | regex.VERBOSE,
)
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
BRACES_TO_UNDERSCORE = b''.maketrans(b'{}', b'__')


def parse_to_spans(
    byte_array: bytearray
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
    comment_spans = []
    comment_spans_append = comment_spans.append
    extension_tag_spans = []
    extension_tag_spans_append = extension_tag_spans.append
    wikilink_spans = []
    wikilink_spans_append = wikilink_spans.append
    parameter_spans = []
    parameter_spans_append = parameter_spans.append
    parser_function_spans = []
    parser_function_spans_append = parser_function_spans.append
    template_spans = []
    template_spans_append = template_spans.append
    # HTML <!-- comments -->
    for match in COMMENT_REGEX.finditer(byte_array):
        # Todo: Parse comments?
        mspan = match.span()
        comment_spans_append(mspan)
        ms, me = mspan
        byte_array[ms:me] = b' ' * (me - ms)
    # <extension tags>
    for match in EXTENSION_TAGS_REGEX.finditer(byte_array):
        mspan = match.span()
        extension_tag_spans_append(mspan)
        ms, me = mspan
        if match[2]:  # parsable tag extension group
            parse_subbytes_to_spans(
                byte_array[ms + 3:me - 3],
                ms + 3,
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
        for match in WIKILINK_REGEX.finditer(byte_array):
            mspan = match.span()
            wikilink_spans_append(mspan)
            ms, me = mspan
            group = byte_array[ms + 2:me - 2]
            parse_to_spans_innerloop(
                group,
                ms + 2,
                parameter_spans_append,
                parser_function_spans_append,
                template_spans_append,
            )
            byte_array[ms:me] = (
                b'_[' + group.translate(BRACES_TO_UNDERSCORE) + b']_'
            )
    parse_to_spans_innerloop(
        byte_array,
        0,
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


def parse_subbytes_to_spans(
    byte_array: bytearray,
    index: int,
    wikilink_spans_append: callable,
    parameter_spans_append: callable,
    pfunction_spans_append: callable,
    template_spans_append: callable,
) -> None:
    """Parse the byte_array to spans.

    This function is basically the same as `parse_to_spans`, but accepts an
    index that indicates the starting index of the given byte_array.
    `byte_array`s that are passed to this function are the contents of
    PARSABLE_TAG_EXTENSIONS.

    """
    # Remove the braces inside WikiLinks.
    # WikiLinks may contain braces that interfere with
    # detection of templates. For example when parsing `{{text |[[A|}}]] }}`,
    # the span of the template should be the whole string.
    match = True
    while match:
        match = False
        for match in WIKILINK_REGEX.finditer(byte_array):
            ms, me = match.span()
            wikilink_spans_append((index + ms, index + me))
            group = byte_array[ms:me]
            parse_to_spans_innerloop(
                group,
                index + ms,
                parameter_spans_append,
                pfunction_spans_append,
                template_spans_append,
            )
            byte_array[ms:me] = (
                b'_[' + group[2:-2].translate(BRACES_TO_UNDERSCORE) + b'_['
            )
    parse_to_spans_innerloop(
        byte_array,
        index,
        parameter_spans_append,
        pfunction_spans_append,
        template_spans_append,
    )


def parse_to_spans_innerloop(
    byte_array: bytearray,
    index: int,
    parameter_spans_append: callable,
    pfunction_spans_append: callable,
    template_spans_append: callable,
) -> None:
    """Find the spans of parameters, parser functions, and templates.

    :byte_array: The byte_array or part of byte_array that is being parsed.
    :index: Add to every returned index.

    This is the innermost loop of the parse_to_spans function.
    If the byte_array passed to parse_to_spans contains n WikiLinks, then
    this function will be called n + 1 times. One time for the whole byte_array
    and n times for each of the n WikiLinks.

    """
    ms = True
    while ms is not None:
        # Single braces will interfere with detection of other elements and
        # should be removed beforehand.
        for m in SINGLE_BRACES_REGEX.finditer(byte_array):
            byte_array[m.start()] = 95  # 95 = ord('_')
        # Also remove empty double braces
        match = True
        while match:
            match = False
            for match in INVALID_NAME_TEMPLATE_REGEX.finditer(byte_array):
                ms, me = match.span()
                byte_array[ms:me] = (me - ms) * b'_'
        i = byte_array.rfind(125)  # 125 == ord('}')
        if i != -1:
            byte_array[i:] = byte_array[i:].replace(b'{', b'_')
        i = byte_array.find(123)  # 125 == ord('{')
        if i != -1:
            byte_array[:i] = byte_array[:i].replace(b'}', b'_')
        ms = None
        # Template parameters
        match = True
        while match:
            match = False
            for match in TEMPLATE_PARAMETER_REGEX.finditer(byte_array):
                ms, me = match.span()
                parameter_spans_append((ms + index, me + index))
                byte_array[ms:ms + 2] = byte_array[me - 2:me] = b'__'
        # Templates
        match = True
        while match:
            # Parser functions
            while match:
                match = False
                for match in PARSER_FUNCTION_REGEX.finditer(byte_array):
                    ms, me = match.span()
                    pfunction_spans_append((ms + index, me + index))
                    byte_array[ms:ms + 2] = byte_array[me - 2:me] = b'__'
            # match is False at this point
            for match in TEMPLATE_NOT_PARAM_REGEX.finditer(byte_array):
                ms, me = match.span()
                template_spans_append((ms + index, me + index))
                byte_array[ms:ms + 2] = byte_array[me - 2:me] = b'__'
