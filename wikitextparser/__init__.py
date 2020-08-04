# Scheme: [N!]N(.N)*[{a|b|rc}N][.postN][.devN]
__version__ = '0.42.2'

from ._parameter import Parameter
from ._argument import Argument
from ._externallink import ExternalLink
from ._wikilink import WikiLink
from ._section import Section
from ._comment_bold_italic import Comment, Bold, Italic
from . import _wikitext
from ._table import Table
from ._template import Template
from ._parser_function import ParserFunction
from ._tag import Tag
from ._wikilist import WikiList
from ._wikilist import LIST_PATTERN_FORMAT as _LIST_PATTERN_FORMAT


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
