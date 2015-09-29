"""The WikiLink class."""


class WikiLink():

    """Create a new WikiLink object."""

    def __init__(self, string, spans=None, index=None):
        """Initialize the object."""
        self._common_init(string, spans)
        if index is None:
            self._index = len(self._spans['wl']) -1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the WikiLink."""
        return 'WikiLink(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['wl'][self._index]

    @property
    def target(self):
        """Return target of this WikiLink."""
        return self.string[2:-2].partition('|')[0]

    @target.setter
    def target(self, newtarget):
        """Set a new target."""
        target, pipe, text = self.string[2:-2].partition('|')
        self.strins(2, newtarget)
        self.strdel(len('[[' + newtarget), len('[[' + newtarget + target))

    @property
    def text(self):
        """Return display text of this WikiLink."""
        target, pipe, text = self.string[2:-2].partition('|')
        if pipe:
            return text

    @text.setter
    def text(self, newtext):
        """Set a new text."""
        target, pipe, text = self.string[2:-2].partition('|')
        self.strins(len('[[' + target + pipe), newtext)
        self.strdel(
            len('[[' + target + pipe + newtext),
            len('[[' + target + pipe + newtext + text),
        )
