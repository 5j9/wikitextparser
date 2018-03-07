"""Initialize the wikitextparser."""

# Scheme: [N!]N(.N)*[{a|b|rc}N][.postN][.devN]
__version__ = '0.21.2.dev0'

import regex as _regex

from ._parameter import Parameter
from ._argument import Argument
from ._externallink import ExternalLink
from ._wikilink import WikiLink
from ._section import Section
from ._comment import Comment
from . import _wikitext
from ._table import Table
from ._template import Template
from ._parser_function import ParserFunction
from ._tag import Tag
from ._tag import START_TAG_PATTERN as _START_TAG_PATTERN
from ._tag import END_TAG_PATTERN as _END_TAG_PATTERN
from ._tag import START_TAG_FINDITER as _START_TAG_FINDITER
from ._wikilist import WikiList
from ._wikilist import LIST_PATTERN_FORMAT as _LIST_PATTERN_FORMAT


_regex.DEFAULT_VERSION = _regex.VERSION1

_wikitext.ExternalLink = ExternalLink
_wikitext.WikiLink = WikiLink
_wikitext.Template = Template
_wikitext.Comment = Comment
_wikitext.ParserFunction = ParserFunction
_wikitext.Parameter = Parameter
_wikitext.Table = Table
_wikitext.Section = Section
_wikitext.WikiList = WikiList
_wikitext.LIST_PATTERN_FORMAT = _LIST_PATTERN_FORMAT
_wikitext.Tag = _wikitext.ExtensionTag = Tag
_wikitext.START_TAG_PATTERN = _START_TAG_PATTERN
_wikitext.END_TAG_PATTERN = _END_TAG_PATTERN
_wikitext.START_TAG_FINDITER = _START_TAG_FINDITER

WikiText = _wikitext.WikiText
parse = WikiText
