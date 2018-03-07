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


class TlPfMixin(SubWikiText):

    """Define common attributes among Templates and ParserFunctions."""

    _args_matcher = NotImplemented

    @property
    def arguments(self) -> List[Argument]:
        """Parse template content. Create self.name and self.arguments."""
        arguments = []
        shadow = self._shadow
        split_spans = self._args_matcher(shadow).spans('arg')
        if split_spans:
            arguments_append = arguments.append
            type_to_spans = self._type_to_spans
            ss, se = span = self._span
            type_ = id(span)
            lststr = self._lststr
            string = lststr[0]
            arg_spans = type_to_spans.setdefault(type_, [])
            span_tuple_to_span_get = {(s[0], s[1]): s for s in arg_spans}.get
            for arg_self_start, arg_self_end in split_spans:
                s, e = arg_span = [ss + arg_self_start, ss + arg_self_end]
                old_span = span_tuple_to_span_get((s, e))
                if old_span is None:
                    insort(arg_spans, arg_span)
                else:
                    arg_span = old_span
                arg = Argument(lststr, type_to_spans, arg_span, type_)
                arg._shadow_cache = (
                    string[s:e], shadow[arg_self_start:arg_self_end])
                arguments_append(arg)
            arg_spans.sort()
        return arguments


class ParserFunction(TlPfMixin):

    """Create a new ParserFunction object."""

    _args_matcher = BAR_SPLITS_FULLMATCH

    @property
    def name(self) -> str:
        """Return name part of the current ParserFunction."""
        return self.string[2:].partition(':')[0]

    @name.setter
    def name(self, newname: str) -> None:
        """Set a new name."""
        self[2:2 + len(self.name)] = newname
