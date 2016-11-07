""""Define the ParserFunction class."""


from .wikitext import SubWikiText
from .argument import Argument


class ParserFunction(SubWikiText):

    """Create a new ParserFunction object."""

    def __init__(
        self,
        string: str or list,
        type_to_spans: list or None=None,
        index: int or None=None,
    ) -> None:
        """Initialize the object."""
        self._common_init(string, type_to_spans)
        self._index = len(
            self._type_to_spans['functions']
        ) - 1 if index is None else index

    def __repr__(self) -> str:
        """Return the string representation of the ParserFunction."""
        return 'ParserFunction(' + repr(self.string) + ')'

    @property
    def _span(self) -> tuple:
        """Return the self-span."""
        return self._type_to_spans['functions'][self._index]

    @property
    def arguments(self) -> list:
        """Parse template content. Create self.name and self.arguments."""
        barsplits = self._not_in_atomic_subspans_split_spans('|')
        arguments = []
        spans = self._type_to_spans
        lststr = self._lststr
        typeindex = 'pfa' + str(self._index)
        if typeindex not in spans:
            spans[typeindex] = []
        aspans = spans[typeindex]
        ss, se = self._span
        # remove the final '}}' from the last argument.
        barsplits[-1] = (barsplits[-1][0], barsplits[-1][1] - 2)
        # first argument
        aspan = barsplits.pop(0)
        aspan = (aspan[0] + self.string.find(':'), aspan[1])
        if aspan not in aspans:
            aspans.append(aspan)
        arguments.append(
            Argument(lststr, spans, aspans.index(aspan), typeindex)
        )
        # the rest of the arguments (similar to templates)
        if barsplits:
            for aspan in barsplits:
                # include the the starting '|'
                aspan = (aspan[0] - 1, aspan[1])
                if aspan not in aspans:
                    aspans.append(aspan)
                arguments.append(
                    Argument(lststr, spans, aspans.index(aspan), typeindex)
                )
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
