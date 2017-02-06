"""Initialize the wikitextparser."""


import regex as _regex

from .parameter import Parameter
from .argument import Argument
from .externallink import ExternalLink
from .wikilink import WikiLink
from .section import Section
from .comment import Comment
from . import wikitext as _wikitext
from .table import Table
from .template import Template
from .parser_function import ParserFunction
from .tag import Tag
from .tag import START_TAG_PATTERN as _START_TAG_PATTERN
from .tag import END_TAG_BYTES_PATTERN as _END_TAG_BYTES_PATTERN
from .tag import START_TAG_FINDITER as _START_TAG_FINDITER
from .wikilist import WikiList
from .wikilist import LIST_PATTERN_FORMAT as _LIST_PATTERN_FORMAT


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
_wikitext.Tag = Tag
_wikitext.START_TAG_PATTERN = _START_TAG_PATTERN
_wikitext.END_TAG_BYTES_PATTERN = _END_TAG_BYTES_PATTERN
_wikitext.START_TAG_FINDITER = _START_TAG_FINDITER

WikiText = _wikitext.WikiText
parse = WikiText
