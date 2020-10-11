# Scheme: [N!]N(.N)*[{a|b|rc}N][.postN][.devN]
__version__ = '0.45.3'

from . import _wikitext
from ._argument import Argument
from ._comment_bold_italic import Bold, Comment, Italic
from ._externallink import ExternalLink
from ._parameter import Parameter
from ._parser_function import ParserFunction
from ._section import Section
from ._table import Table
from ._tag import Tag
from ._template import Template
from ._wikilink import WikiLink
from ._wikilist import LIST_PATTERN_FORMAT as _LIST_PATTERN_FORMAT, WikiList

_wikitext.ExternalLink = ExternalLink
_wikitext.WikiLink = WikiLink
_wikitext.Template = Template
_wikitext.Comment = Comment
_wikitext.Bold = Bold
_wikitext.Italic = Italic
_wikitext.ParserFunction = ParserFunction
_wikitext.Parameter = Parameter
_wikitext.Table = Table
_wikitext.Section = Section
_wikitext.WikiList = WikiList
_wikitext.LIST_PATTERN_FORMAT = _LIST_PATTERN_FORMAT
_wikitext.Tag = _wikitext.ExtensionTag = Tag

WikiText = _wikitext.WikiText
parse = WikiText
remove_markup = _wikitext.remove_markup
