""""Define the ParserFunction class."""


from typing import List

import regex

from .wikitext import SubWikiText
from .argument import Argument


BAR_SPLITS_FULLMATCH = regex.compile(
    r'{{'
    r'[^:|]*'  # name
    r'(?<arg>:[^|]*)?(?<arg>\|[^|]*)*'
    r'}}'
).fullmatch


class ParserFunction(SubWikiText):

    """Create a new ParserFunction object."""

    @property
    def arguments(self) -> List[Argument]:
        """Parse template content. Create self.name and self.arguments."""
        arguments = []
        split_spans = BAR_SPLITS_FULLMATCH(self._shadow).spans('arg')
        if split_spans:
            arguments_append = arguments.append
            type_to_spans = self._type_to_spans
            pf_span = self._span
            type_ = id(pf_span)
            lststr = self._lststr
            arg_spans = type_to_spans.setdefault(type_, [])
            arg_spans_append = arg_spans.append
            span_tuple_to_span_get = {(s[0], s[1]): s for s in arg_spans}.get
            ss = pf_span[0]
            for s, e in split_spans:
                span = [ss + s, ss + e]
                old_span = span_tuple_to_span_get((span[0], span[1]))
                if old_span is None:
                    arg_spans_append(span)
                else:
                    span = old_span
                arguments_append(Argument(lststr, type_to_spans, span, type_))
        return arguments

    @property
    def name(self) -> str:
        """Return name part of the current ParserFunction."""
        return self.string[2:].partition(':')[0]

    @name.setter
    def name(self, newname: str) -> None:
        """Set a new name."""
        name = self.name
        self[2:2 + len(name)] = newname
