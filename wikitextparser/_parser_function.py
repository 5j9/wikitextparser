""""Define the ParserFunction class."""


from bisect import insort
from typing import List

import regex

from ._wikitext import SubWikiText
from ._argument import Argument


BAR_SPLITS_FULLMATCH = regex.compile(
    rb'{{'
    rb'[^:|}]*+'  # name
    rb'(?<arg>:[^|}]*+)?+(?<arg>\|[^|}]*+)*+'
    rb'}}'
).fullmatch


class ParserFunction(SubWikiText):

    """Create a new ParserFunction object."""

    @property
    def arguments(self) -> List[Argument]:
        """Parse template content. Create self.name and self.arguments."""
        arguments = []
        shadow = self._shadow
        split_spans = BAR_SPLITS_FULLMATCH(shadow).spans('arg')
        if split_spans:
            arguments_append = arguments.append
            type_to_spans = self._type_to_spans
            ss, se = span = self._span
            type_ = id(span)
            lststr = self._lststr
            string = lststr[0]
            arg_spans = type_to_spans.setdefault(type_, [])
            span_tuple_to_span_get = {(s[0], s[1]): s for s in arg_spans}.get
            for arg_f_start, arg_f_end in split_spans:
                arg_f_start, arg_f_end = span = [
                    ss + arg_f_start, ss + arg_f_end]
                old_span = span_tuple_to_span_get((arg_f_start, arg_f_end))
                if old_span is None:
                    insort(arg_spans, span)
                else:
                    span = old_span
                arg = Argument(lststr, type_to_spans, span, type_)
                arg._shadow_cache = (
                    string[arg_f_start:arg_f_end],
                    shadow[arg_f_start:arg_f_end],
                )
                arguments_append(arg)
            arg_spans.sort()
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
