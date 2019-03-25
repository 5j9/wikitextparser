"""Define the ParserFunction class."""
from bisect import insort
from typing import List

import regex

from ._wikitext import SubWikiText
from ._argument import Argument
from ._wikilist import WikiList


BAR_SPLITS_FULLMATCH = regex.compile(
    rb'{{'
    rb'[^:|}]*+'  # name
    rb'(?<arg>:[^|}]*+)?+(?<arg>\|[^|}]*+)*+'
    rb'}}'
).fullmatch


class SubWikiTextWithArgs(SubWikiText):

    """Define common attributes for `Template` and `ParserFunction`."""

    _args_matcher = NotImplemented
    _first_arg_sep = 0

    @property
    def arguments(self) -> List[Argument]:
        """Parse template content. Create self.name and self.arguments."""
        shadow = self._shadow
        split_spans = self._args_matcher(shadow).spans('arg')
        if not split_spans:
            return []
        arguments = []
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
        return arguments

    def lists(self, pattern: str = None) -> List[WikiList]:
        """Return the lists in all arguments.

        For performance reasons it is usually preferred to get a specific
        Argument and use the `lists` method of that argument instead.
        """
        return [
            lst for arg in self.arguments for lst in arg.lists(pattern) if lst]

    @property
    def name(self) -> str:
        """Return template's name (includes whitespace)."""
        h = self._atomic_partition(self._first_arg_sep)[0]
        if len(h) == len(self.string):
            return h[2:-2]
        return h[2:]

    @name.setter
    def name(self, newname: str) -> None:
        """Set the new name."""
        self[2:2 + len(self.name)] = newname


class ParserFunction(SubWikiTextWithArgs):

    """Create a new ParserFunction object."""

    _args_matcher = BAR_SPLITS_FULLMATCH
    _first_arg_sep = 58
