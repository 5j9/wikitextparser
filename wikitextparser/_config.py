"""Utilities to override default configurations."""


from collections import defaultdict as _defaultdict
from typing import List as _List


def _plant_trie(strings: _List[str]) -> dict:
    """Create a Trie out of a list of words and return an atomic regex pattern.

    The corresponding Regex should match much faster than a simple Regex union.
    """
    # plant the trie
    trie = {}
    for string in strings:
        d = trie
        for char in string:
            d[char] = char in d and d[char] or {}
            d = d[char]
        d[''] = None  # EOS
    return trie


def _pattern(trie: dict) -> str:
    """Convert a trie to a regex pattern."""
    if '' in trie:
        if len(trie) == 1:
            return ''
        optional = True
        del trie['']
    else:
        optional = False

    subpattern_to_chars = _defaultdict(list)

    for char, sub_trie in trie.items():
        subpattern = _pattern(sub_trie)
        subpattern_to_chars[subpattern].append(char)

    alts = []
    for subpattern, chars in subpattern_to_chars.items():
        if len(chars) == 1:
            alts.append(chars[0] + subpattern)
        else:
            chars.sort(reverse=True)
            alts.append('[' + ''.join(chars) + ']' + subpattern)

    if len(alts) == 1:
        result = alts[0]
        if optional:
            if len(result) == 1:
                result += '?+'
            else:  # more than one character in alts[0]
                result = '(?:' + result + ')?+'
    else:
        alts.sort(reverse=True)
        result = '(?>' + '|'.join(alts) + ')'
        if optional:
            result += '?+'
    return result


def regex_pattern(words: _List[str]) -> str:
    """Convert words to a regex pattern that matches any of them."""
    return _pattern(_plant_trie(words))


# Contents of the some of the extension tags can be parsed as wikitext.
# For example, templates are valid inside the poem tag:
#    <poem>{{text|Hi!}}</poem>
# But not within math or source or ...
# for more information about the <categorytree> tag see:
# https://www.mediawiki.org/wiki/Extension:CategoryTree#
#    The_.7B.7B.23categorytree.7D.7D_parser_function
_parsable_tag_extensions = {
    'categorytree',
    'gallery',
    'imagemap',
    'includeonly',
    'indicator',
    'inputbox',
    'poem',
    'ref',
    'references',
    'section',
}
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
# a tag extension (e.g.: <pre>).
_unparsable_tag_extensions = {
    'charinsert',
    'graph',
    'hiero',
    'math',
    'nowiki',
    'pre',
    'score',
    'source',
    'syntaxhighlight',
    'templatedata',
    'timeline',
}
_tag_extensions = _parsable_tag_extensions | _unparsable_tag_extensions

# Copied from DefaultSettings.php
# https://phabricator.wikimedia.org/source/mediawiki/browse/master/includes/DefaultSettings.php
# See also: https://www.mediawiki.org/wiki/Help:Links#External_links
_bare_external_link_schemes = {
  'bitcoin:', 'ftp://', 'ftps://', 'geo:', 'git://', 'gopher://', 'http://',
  'https://', 'irc://', 'ircs://', 'magnet:', 'mailto:', 'mms://', 'news:',
  'nntp://', 'redis://', 'sftp://', 'sip:', 'sips:', 'sms:', 'ssh://',
  'svn://', 'tel:', 'telnet://', 'urn:', 'worldwind://', 'xmpp:',  # '//'
}

_parser_functions = {
    'ARTICLEPAGENAME',
    'ARTICLEPAGENAMEE',
    'ARTICLESPACE',
    'ARTICLESPACEE',
    'BASEPAGENAME',
    'BASEPAGENAMEE',
    'CASCADINGSOURCES',
    'DEFAULTCATEGORYSORT',
    'DEFAULTSORT',
    'DEFAULTSORTKEY',
    'DISPLAYTITLE',
    'FULLPAGENAME',
    'FULLPAGENAMEE',
    'NAMESPACE',
    'NAMESPACEE',
    'NAMESPACENUMBER',
    'NUMBERINGROUP',
    'NUMBEROFACTIVEUSERS',
    'NUMBEROFADMINS',
    'NUMBEROFARTICLES',
    'NUMBEROFEDITS',
    'NUMBEROFFILES',
    'NUMBEROFPAGES',
    'NUMBEROFUSERS',
    'NUMBEROFVIEWS',
    'NUMINGROUP',
    'PAGEID',
    'PAGENAME',
    'PAGENAMEE',
    'PAGESINCAT',
    'PAGESINCATEGORY',
    'PAGESINNAMESPACE',
    'PAGESINNS',
    'PAGESIZE',
    'PROTECTIONEXPIRY',
    'PROTECTIONLEVEL',
    'REVISIONDAY',
    'REVISIONDAY2',
    'REVISIONID',
    'REVISIONMONTH',
    'REVISIONMONTH1',
    'REVISIONTIMESTAMP',
    'REVISIONUSER',
    'REVISIONYEAR',
    'ROOTPAGENAME',
    'ROOTPAGENAMEE',
    'SUBJECTPAGENAME',
    'SUBJECTPAGENAMEE',
    'SUBJECTSPACE',
    'SUBJECTSPACEE',
    'SUBPAGENAME',
    'SUBPAGENAMEE',
    'TALKPAGENAME',
    'TALKPAGENAMEE',
    'TALKSPACE',
    'TALKSPACEE',
    'anchorencode',
    'canonicalurl',
    'filepath',
    'formatnum',
    'fullurl',
    'gender',
    'grammar',
    'int',
    'lc',
    'lcfirst',
    'localurl',
    'ns',
    'nse',
    'padleft',
    'padright',
    'plural',
    'uc',
    'ucfirst',
    'urlencode',
}
