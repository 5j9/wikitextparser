""""Define the ParserFunction class."""


from .wikitext import IndexedWikiText
from .argument import Argument

class ParserFunction(IndexedWikiText):

    """Create a new ParserFunction object."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans)
        if index is None:
            self._index = len(self._spans['functions']) - 1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the ParserFunction."""
        return 'ParserFunction(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['functions'][self._index]

    @property
    def arguments(self):
        """Parse template content. Create self.name and self.arguments."""
        barsplits = self._not_in_subspans_split_spans('|')
        arguments = []
        spans = self._spans
        lststr = self._lststr
        typeindex = 'pfa' + str(self._index)
        if typeindex not in spans:
            spans[typeindex] = []
        aspans = spans[typeindex]
        ss, se = self._get_span()
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
    def name(self):
        """Return name part of the current ParserFunction."""
        return self.string[2:].partition(':')[0]

    @name.setter
    def name(self, newname):
        """Set a new name."""
        name = self.name
        self.replace_slice(2, 2 + len(name), newname)
