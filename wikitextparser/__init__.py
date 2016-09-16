"""Initialize the wikitextparser."""


from .parameter import Parameter
from .argument import Argument
from .externallink import ExternalLink
from .wikilink import WikiLink
from .section import Section
from .comment import Comment
from . import wikitext
from .table import Table
from .template import Template
from .parser_function import ParserFunction


wikitext.ExternalLink = ExternalLink
wikitext.WikiLink = WikiLink
wikitext.Template = Template
wikitext.Comment = Comment
wikitext.ParserFunction = ParserFunction
wikitext.Parameter = Parameter
wikitext.Table = Table
wikitext.Section = Section

WikiText = wikitext.WikiText
parse = WikiText
