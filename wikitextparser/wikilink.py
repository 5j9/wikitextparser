"""The WikiLink class."""


from typing import Optional

from .wikitext import SubWikiText


class WikiLink(SubWikiText):

    """Create a new WikiLink object."""

    @property
    def target(self) -> str:
        """Return target of this WikiLink."""
        head, pipe, tail = self._atomic_partition(b'|')
        if pipe:
            return head[2:].decode()
        else:
            return head[2:-2].decode()

    @target.setter
    def target(self, newtarget: str) -> None:
        """Set a new target."""
        head, pipe, tail = self._atomic_partition(b'|')
        if not pipe:
            head = head[:-2]
        self[2:len(head)] = newtarget.encode()

    @property
    def text(self) -> str:
        """Return display text of this WikiLink."""
        head, pipe, tail = self._atomic_partition(b'|')
        if pipe:
            return tail[:-2].decode()

    @text.setter
    def text(self, newtext: str=None) -> None:
        """Set self.text to newtext. Remove the text if newtext is None."""
        head, pipe, tail = self._atomic_partition(b'|')
        if pipe:
            if newtext is None:
                del self[len(head + pipe) - 1:-2]
                return
            self[len(head + pipe):-2] = newtext.encode()
            return
        # Old text is None
        if newtext is not None:
            self.insert(-2, b'|' + newtext.encode())
