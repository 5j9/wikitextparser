"""Define the functions required for parsing wikitext into spans."""
from functools import partial
from typing import Callable, Dict, Optional

from regex import DOTALL, REVERSE, compile as regex_compile, IGNORECASE

from ._config import (
    _HTML_TAG_NAME, _bare_external_link_schemes, _parsable_tag_extensions,
    _parser_functions, _unparsable_tag_extensions, regex_pattern)

# According to https://www.mediawiki.org/wiki/Manual:$wgLegalTitleChars
# illegal title characters are: r'[]{}|#<>[\u0000-\u0020]'
VALID_TITLE_CHARS = rb'[^\1-\6\|\{\}\[\]<>\n]++'
# Parser functions
# According to https://www.mediawiki.org/wiki/Help:Magic_words
# See also:
# https://translatewiki.net/wiki/MediaWiki:Sp-translate-data-MagicWords/fa
ARGS = rb'(?:\|(?>[^{}]++|{(?!{)|}(?!}))*+)?+'
PF_TL_FINDITER = regex_compile(  # noqa
    rb'\{\{(?>'
        rb'[\s\0]*+'
        rb'(?>'
            rb'\#[^{}\s:|]++'  # parser function
            rb'|' + regex_pattern(_parser_functions)[3:] +  # )
        # should not have any arguments or the arg should start with a :
        rb'(?:'
            rb':(?>[^{}]*+|}(?!})|{(?!{))*+'
        rb')?+'
        rb'\}\}()'
        rb'|'  # invalid template name
        rb'[\s\0_]*+' + ARGS +
        rb'\}\}()'
        rb'|'  # template
        rb'[\s\0]*+' + VALID_TITLE_CHARS +  # template name
        rb'[\s\0]*+' + ARGS +
    rb'\}\})').finditer
# External links
INVALID_URL_CHARS = rb' \t\n"<>\[\]'
VALID_URL_CHARS = rb'[^' + INVALID_URL_CHARS + rb']++'
# See more info on literal IPv6 see:
# https://en.wikipedia.org/wiki/IPv6_address#Literal_IPv6_addresses_in_network_resource_identifiers
# The following pattern is part of EXT_LINK_ADDR constant in
# https://github.com/wikimedia/mediawiki/blob/master/includes/parser/Parser.php
LITERAL_IPV6_AND_TAIL = rb'\[[0-9a-fA-F:.]++\][^' + INVALID_URL_CHARS + rb']*+'
# A \b is added to the beginning.
BARE_EXTERNAL_LINK_SCHEMES = (
    rb'\b' + regex_pattern(_bare_external_link_schemes))
EXTERNAL_LINK_URL_TAIL = (
    rb'(?>' + LITERAL_IPV6_AND_TAIL + rb'|' + VALID_URL_CHARS + rb')')
BARE_EXTERNAL_LINK = BARE_EXTERNAL_LINK_SCHEMES + EXTERNAL_LINK_URL_TAIL
# Wikilinks
# https://www.mediawiki.org/wiki/Help:Links#Internal_links
WIKILINK_PARAM_FINDITER = regex_compile(  # noqa
    rb'(?<!(?>^|[^\[\0])(?:(?>\[\0*+){2})*+\[\0*+)'  # != 2N + 1
    rb'\[\0*\['
    rb'(?![\ \0]*+' + BARE_EXTERNAL_LINK + rb')'
    + VALID_TITLE_CHARS +
    rb'(?>'
        rb'\|'
        rb'(?>'
            rb'(?<!\[\0*+)'
            rb'\['
        rb')?+'
        rb'(?>'
            rb'(?<!\]\0*+)'
            rb'\]'
        rb')?+'
        # single matching brackets are allowed in text e.g. [[a|[b]]]
        rb'(?>'
            rb'[^\[\]\|]*+'
            rb'\['
            rb'[^\[\]\|]*+'
            rb'\]'
            rb'(?!(?:\0*+\]){3})'
        rb')?+'
        rb'[^\[\]\|]*+'
    rb')*+'
    rb'\]\0*+\]'
    rb'|\{\{\{('
        rb'[^{}]++'
        rb'|(?<!})}(?!})'
        rb'|(?<!{){'
    rb')++\}\}\}',
    REVERSE).finditer

# these characters interfere with detection of (args|tls|wlinks|wlists)
pbba_tt = b''.maketrans(b"|[]'{}", b'\1\2\3\7\5\6')
blank_sensitive_chars = partial(regex_compile(br'[\|\{\}\n]').sub, br' ')
blank_brackets = partial(regex_compile(br'[\[\]]').sub, br' ')

PARSABLE_TAG_EXTENSION_NAME = regex_pattern(
    _parsable_tag_extensions)
UNPARSABLE_TAG_EXTENSION_NAME = regex_pattern(
    _unparsable_tag_extensions)

# The idea of the following regex is to detect innermost HTML tags. From
# http://blog.stevenlevithan.com/archives/match-innermost-html-element
# But it's not bullet proof:
# https://stackoverflow.com/questions/3076219/
CONTENT_AND_END = (  # noqa
    rb'\b[^>]*+'
    rb'(?>'
        rb'(?<=/)>'  # self-closing
        # group c captures contents
        rb'|>(?<c>'
            rb'.*?'
        rb')</\g<n>\s*+>'
    rb')')
EXTENSION_TAGS_FINDITER = regex_compile(  # noqa
    rb'<(?>'
        # group m captures comments
        rb'(?<m>!--[\s\S]*?(?>-->|(?=</\g<n>\s*+>)|\Z))'
        # u captures unparsable tag extensions and n captures the name
        rb'|(?<u>(?<n>' + UNPARSABLE_TAG_EXTENSION_NAME + rb')'
            + CONTENT_AND_END
        + rb')'
        # p captures parsable tag extensions and n captures the name
        rb'|(?<p>(?<n>' + PARSABLE_TAG_EXTENSION_NAME + rb')'
            + CONTENT_AND_END
        + rb')'
    rb')', DOTALL | IGNORECASE).finditer

# HTML tags
# Tags:
# https://infra.spec.whatwg.org/#ascii-whitespace
SPACE_CHARS = rb' \t\n\u000C\r'  # \s - \v
# http://stackoverflow.com/a/93029/2705757
# chrs = (chr(i) for i in range(sys.maxunicode))
# control_chars = ''.join(c for c in chrs if unicodedata.category(c) == 'Cc')
CONTROL_CHARS = rb'\x00-\x1f\x7f-\x9f'
# https://www.w3.org/TR/html5/syntax.html#syntax-attributes
ATTR_NAME = (
    rb'(?<attr_name>[^' + SPACE_CHARS + CONTROL_CHARS + rb'"\'>/=]++)')
EQ_WS = rb'=[' + SPACE_CHARS + rb']*+'
UNQUOTED_ATTR_VAL = (
    rb'(?<attr_value>[^' + SPACE_CHARS + rb'"\'=<>`]++)')
QUOTED_ATTR_VAL = rb'(?<quote>[\'"])(?<attr_value>.*?)(?P=quote)'
# May include character references, but for now, ignore the fact that they
# cannot contain an ambiguous ampersand.
ATTR_VAL = (
    # If an empty attribute is to be followed by the optional
    # "/" character, then there must be a space character separating
    # the two. This rule is ignored here.
    rb'(?>[' + SPACE_CHARS + rb']*+'  # noqa
        + EQ_WS + rb'(?>' + UNQUOTED_ATTR_VAL + rb'|' + QUOTED_ATTR_VAL + rb')'
        + rb'|(?<attr_value>)'  # empty attribute
    + rb')')
# Ignore ambiguous ampersand for the sake of simplicity.
ATTRS_PATTERN = ( # noqa
    rb'(?<attr>'
        rb'[' + SPACE_CHARS + rb']++(?>' + ATTR_NAME + ATTR_VAL + rb')'
        # Invalid attribute. Todo: could the / be removed? see
        # https://stackoverflow.com/a/3558200/2705757
        + rb'|(?>[^>/]++|/(?!\s*+>))++'
    rb')*+(?<attr_insert>)')
ATTRS_MATCH = regex_compile(
    # Leading space is not required at the start of the attribute string.
    ATTRS_PATTERN.replace(b'++', b'*+', 1),
).match
# VOID_ELEMENTS = (
#     'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'keygen',
#     'link', 'meta', 'param', 'source', 'track', 'wbr'
# )
# RAW_TEXT_ELEMENTS = ('script', 'style')
# ESCAPABLE_RAW_TEXT_ELEMENTS = ('textarea', 'title')
# Detecting foreign elements in MathML and SVG namespaces is not implemented
# yet. See
# https://developer.mozilla.org/en/docs/Web/SVG/Namespaces_Crash_Course
# for an overview.
# note that end tags do not accept attributes, but MW currently cleans up and
# ignores such attributes
END_TAG_PATTERN = rb'(?<end_tag></{name}(?:>|[' + SPACE_CHARS + rb'][^>]*+>))'
START_TAG_PATTERN = ( # noqa
    rb'(?<start_tag>'
        rb'<{name}' + ATTRS_PATTERN +
        rb'[' + SPACE_CHARS + rb']*+'
        rb'(?:(?<self_closing>/[' + SPACE_CHARS + b']*+>)|>)'
    rb')')
HTML_START_TAG_FINDITER = regex_compile(
    START_TAG_PATTERN.replace(b'{name}', _HTML_TAG_NAME, 1)).finditer
HTML_END_TAG_FINDITER = regex_compile(
    END_TAG_PATTERN.replace(b'{name}', _HTML_TAG_NAME, 1)).finditer


def parse_to_spans(byte_array: bytearray) -> Dict[str, list]:
    """Calculate and set self._type_to_spans.

    Extracted spans will be removed from byte_array.
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
    comment_spans = []
    cms_append = comment_spans.append
    extension_tag_spans = []
    ets_append = extension_tag_spans.append
    wikilink_spans = []
    wls_append = wikilink_spans.append
    parameter_spans = []
    pms_append = parameter_spans.append
    parser_function_spans = []
    pfs_append = parser_function_spans.append
    template_spans = []
    tls_append = template_spans.append
    # <extension tags>
    extract_tag_extensions(
        byte_array, ets_append, cms_append, None, None,
        pms_append, pfs_append, tls_append, wls_append)
    _parse_sub_spans(
        byte_array, 0, None, pms_append, pfs_append, tls_append, wls_append)
    return {
        'Comment': comment_spans,
        'ExtensionTag': sorted(extension_tag_spans),
        'Parameter': sorted(parameter_spans),
        'ParserFunction': sorted(parser_function_spans),
        'Template': sorted(template_spans),
        'WikiLink': sorted(wikilink_spans)}


def extract_tag_extensions(
    byte_array, ets_append, cms_append, start, end,
    pms_append, pfs_append, tls_append, wls_append
):
    for match in EXTENSION_TAGS_FINDITER(byte_array, start, end):
        span = match.span
        s, e = span('m')  # comment
        if s != -1:
            s -= 1  # <
            cms_append([s, e, None, byte_array[s:e]])
            byte_array[s:e] = b'\0' * (e - s)
            continue
        s, e = span('u')  # unparsable
        if s != -1:
            s -= 1  # <
            ets_append([s, e, match, byte_array[s:e]])
            byte_array[s:e] = (e - s) * b'_'
            continue
        s, e = span('p')  # parsable
        if s != -1:
            s -= 1  # <
            ets_append([s, e, match, byte_array[s:e]])
            cs, ce = span('c')  # content
            extract_tag_extensions(
                byte_array, ets_append, cms_append, cs, ce,
                pms_append, pfs_append, tls_append, wls_append)
            _parse_sub_spans(
                byte_array, s, e,
                pms_append, pfs_append, tls_append, wls_append)
            byte_array[cs:ce] = b'_' * (ce - cs)
            continue


def _parse_sub_spans(
    byte_array: bytearray, start: int, end: Optional[int],
    pms_append: Callable, pfs_append: Callable,
    tls_append: Callable, wls_append: Callable,
) -> None:
    start_and_end_tags = *HTML_START_TAG_FINDITER(byte_array, start, end),\
        *HTML_END_TAG_FINDITER(byte_array, start, end)
    for match in start_and_end_tags:
        ms, me = match.span()
        byte_array[ms:me] = blank_brackets(byte_array[ms:me])
    while True:
        while True:
            match = None
            for match in WIKILINK_PARAM_FINDITER(byte_array, start, end):
                ms, me = match.span()
                if match[1] is None:
                    wls_append([ms, me, match, byte_array[ms:me]])
                    _parse_sub_spans(
                        byte_array, ms + 2, me - 2,
                        pms_append, pfs_append, tls_append, wls_append)
                    byte_array[ms:me] = byte_array[ms:me].translate(pbba_tt)
                else:
                    pms_append([ms, me, match, byte_array[ms:me]])
                    _parse_sub_spans(
                        byte_array, ms + 2, me - 2,
                        pms_append, pfs_append, tls_append, wls_append)
                    byte_array[ms:me] = b'_' * (me - ms)
            if match is None:
                break
        for match in PF_TL_FINDITER(byte_array, start, end):
            ms, me = match.span()
            if match[1] is not None:
                pfs_append([ms, me, match, byte_array[ms:me]])
                byte_array[ms:me] = b'X' * (me - ms)
            elif match[2] is not None:  # invalid template name
                byte_array[ms:me] = b'_' * (me - ms)
                byte_array[ms+1] = 123
                continue
            else:
                tls_append([ms, me, match, byte_array[ms:me]])
                byte_array[ms:me] = b'X' * (me - ms)
        if match is None:
            break
    for match in start_and_end_tags:
        ms, me = match.span()
        byte_array[ms:me] = blank_sensitive_chars(byte_array[ms:me])
