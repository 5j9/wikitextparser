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


_regex.DEFAULT_VERSION = _regex.VERSION1
_wikitext.ExternalLink = ExternalLink
_wikitext.WikiLink = WikiLink
_wikitext.Template = Template
_wikitext.Comment = Comment
_wikitext.ParserFunction = ParserFunction
_wikitext.Parameter = Parameter
_wikitext.Table = Table
_wikitext.Section = Section

WikiText = _wikitext.WikiText
parse = WikiText
