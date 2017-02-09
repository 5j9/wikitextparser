"""The WikiLink class."""


from typing import Optional

from .wikitext import SubWikiText


class WikiLink(SubWikiText):

    """Create a new WikiLink object."""

    @property
    def target(self) -> str:
        """Return target of this WikiLink."""
        head, pipe, tail = self._atomic_partition('|')
        if pipe:
            return head[2:]
        else:
            return head[2:-2]

    @target.setter
    def target(self, newtarget: str) -> None:
        """Set a new target."""
        head, pipe, tail = self._atomic_partition('|')
        if not pipe:
            head = head[:-2]
        self[2:len(head)] = newtarget

    @property
    def text(self) -> Optional[str]:
        """Return display text of this WikiLink."""
        head, pipe, tail = self._atomic_partition('|')
        if pipe:
            return tail[:-2]
        return None  # pragma: no cover

    @text.setter
    def text(self, newtext: Optional[str]) -> None:
        """Set self.text to newtext. Remove the text if newtext is None."""
        head, pipe, tail = self._atomic_partition('|')
        if pipe:
            if newtext is None:
                del self[len(head + pipe) - 1:len(head + pipe + tail) - 2]
            else:
                self[len(head + pipe):len(head + pipe + tail) - 2] = newtext
        elif newtext is not None:
            self.insert(-2, '|' + newtext)
