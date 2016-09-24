"""The WikiLink class."""


from .wikitext import IndexedWikiText


class WikiLink(IndexedWikiText):

    """Create a new WikiLink object."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans)
        if index is None:
            self._index = len(self._spans['wikilinks']) - 1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the WikiLink."""
        return 'WikiLink(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['wikilinks'][self._index]

    @property
    def target(self) -> str:
        """Return target of this WikiLink."""
        head, pipe, tail = self._not_in_subspans_partition('|')
        if pipe:
            return head[2:]
        else:
            return head[2:-2]

    @target.setter
    def target(self, newtarget) -> None:
        """Set a new target."""
        head, pipe, tail = self._not_in_subspans_partition('|')
        if not pipe:
            head = head[:-2]
        self.replace_slice(2, len(head), newtarget)

    @property
    def text(self) -> str:
        """Return display text of this WikiLink."""
        head, pipe, tail = self._not_in_subspans_partition('|')
        if pipe:
            return tail[:-2]

    @text.setter
    def text(self, newtext) -> None:
        """Set self.text to newtext. Remove the text if newtext is None."""
        head, pipe, tail = self._not_in_subspans_partition('|')
        if pipe:
            if newtext is None:
                self.strdel(
                    len(head + pipe) - 1,
                    len(head + pipe + tail) - 2,
                )
            else:
                self.replace_slice(
                    len(head + pipe),
                    len(head + pipe + tail) - 2,
                    newtext
                )
        elif newtext is not None:
            self.strins(len(head) - 2, '|' + newtext)
