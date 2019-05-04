"""The WikiLink class."""


from typing import Optional
from warnings import warn

from ._wikitext import SubWikiText


class WikiLink(SubWikiText):
    """Define a class to represent WikiLinks."""

    @property
    def target(self) -> str:
        """Return target of this WikiLink."""
        head, pipe, tail = self._atomic_partition(124)
        if pipe:
            return head[2:]
        else:
            return head[2:-2]

    @target.setter
    def target(self, newtarget: str) -> None:
        """Set a new target."""
        head, pipe, tail = self._atomic_partition(124)
        if not pipe:
            head = head[:-2]
        self[2:len(head)] = newtarget

    @property
    def text(self) -> Optional[str]:
        """Return the text of this WikiLink. Do not include linktrail."""
        pipe = self._shadow.find(124)
        if pipe == -1:
            return None
        return self[pipe + 1:-2]

    @text.setter
    def text(self, newtext: str) -> None:
        """Set self.text to newtext. Do not change the linktrail."""
        if newtext is None:
            warn('Using None as a value for text is deprecated; '
                 'Use `del WikiLink.text` instead', DeprecationWarning)
            del self.text
            return
        pipe = self._shadow.find(124)
        if pipe == -1:
            self.insert(-2, '|' + newtext)
            return
        self[pipe + 1:-2] = newtext

    @text.deleter
    def text(self):
        """Delete self.text."""
        pipe = self._shadow.find(124)
        if pipe == -1:
            return
        del self[pipe:-2]

    @property
    def fragment(self) -> Optional[str]:
        """Return the fragment identifier."""
        shadow_find = self._shadow.find
        pipe = shadow_find(124)
        hash_ = shadow_find(35)
        if pipe == -1:
            if hash_ == -1:
                return None
            return self[hash_ + 1:-2]
        if hash_ == -1 or pipe < hash_:
            return None
        return self[hash_ + 1:pipe]

    @fragment.setter
    def fragment(self, value: str):
        """Set a new fragment."""
        shadow_find = self._shadow.find
        pipe = shadow_find(124)
        hash_ = shadow_find(35)
        if pipe == -1:
            if hash_ == -1:
                self.insert(-2, '#' + value)
                return
            self[hash_ + 1:-2] = value
            return
        if hash_ == -1 or hash_ > pipe:
            self.insert(pipe, '#' + value)
            return
        self[hash_ + 1:pipe] = value
        return

    @fragment.deleter
    def fragment(self):
        """Delete fragment."""
        shadow_find = self._shadow.find
        hash_ = shadow_find(35)
        if hash_ == -1:
            return
        pipe = shadow_find(124)
        if pipe == -1:
            del self[hash_:-2]
        if pipe < hash_:
            return
        del self[hash_:pipe]
