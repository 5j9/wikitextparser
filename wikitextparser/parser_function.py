""""Define the ParserFunction class."""


from typing import List

from .wikitext import SubWikiText
from .argument import Argument


class ParserFunction(SubWikiText):

    """Create a new ParserFunction object."""

    @property
    def arguments(self) -> List[Argument]:
        """Parse template content. Create self.name and self.arguments."""
        barsplits = self._atomic_split_spans(b'|')
        arguments = []
        spans = self._type_to_spans
        _bytearray = self._bytearray
        typeindex = 'pfa' + str(self._index)
        if typeindex not in spans:
            spans[typeindex] = []
        known_arg_spans = spans[typeindex]
        # remove the final '}}' from the last argument.
        s, e = barsplits[-1]
        barsplits[-1] = (s, e - 2)
        # first argument
        s, e = barsplits.pop(0)
        arg_span = (s + self[:].find(b':'), e)
        if arg_span not in known_arg_spans:
            known_arg_spans.append(arg_span)
        arguments.append(
            Argument(_bytearray, spans, known_arg_spans.index(arg_span), typeindex)
        )
        # the rest of the arguments (similar to templates)
        if barsplits:
            for arg_span in barsplits:
                # include the the starting '|'
                arg_span = (arg_span[0] - 1, arg_span[1])
                if arg_span not in known_arg_spans:
                    known_arg_spans.append(arg_span)
                arguments.append(
                    Argument(_bytearray, spans, known_arg_spans.index(arg_span), typeindex)
                )
        return arguments

    @property
    def name(self) -> str:
        """Return name part of the current ParserFunction."""
        return self.string[2:].partition(':')[0]

    @name.setter
    def name(self, newname: str) -> None:
        """Set a new name."""
        name = self[2:].partition(b':')[0]
        self[2:2 + len(name)] = newname.encode()
