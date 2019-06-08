"""Define the WikiLink class."""


from typing import Optional
from warnings import warn

from ._wikitext import SubWikiText


class WikiLink(SubWikiText):
    """Define a class to represent WikiLinks."""

    @property
    def target(self) -> str:
        """WikiLink's target, including the fragment, without the linktrail.

        Do not include the pipe (|) in setter and getter.
        Deleter: delete the link target, including the pipe character.
            Use `self.target = ''` if you don't want to remove the pipe.
        """
        pipe = self._shadow.find(124)
        if pipe == -1:
            return self(2, -2)
        return self(2, pipe)

    @target.setter
    def target(self, newtarget: str) -> None:
        pipe = self._shadow.find(124)
        if pipe == -1:
            self[2:-2] = newtarget
            return
        self[2:pipe] = newtarget

    @target.deleter
    def target(self) -> None:
        pipe = self._shadow.find(124)
        if pipe == -1:
            del self[2:-2]
            return
        del self[2:pipe + 1]

    @property
    def text(self) -> Optional[str]:
        """The [[inner text| of WikiLink ]] (not including the [[link]]trail).

        setter: set a new value for self.text. Do not include the pipe.
        deleter: delete self.text, including the pipe.
        """
        pipe = self._shadow.find(124)
        if pipe == -1:
            return None
        return self(pipe + 1, -2)

    @text.setter
    def text(self, newtext: str) -> None:
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
        pipe = self._shadow.find(124)
        if pipe == -1:
            return
        del self[pipe:-2]

    @property
    def fragment(self) -> Optional[str]:
        """Fragment identifier.

        getter: target's fragment identifier (do not include the # character)
        setter: set a new fragment (do not include the # character)
        deleter: delete fragment, including the # character.
        """
        shadow_find = self._shadow.find
        pipe = shadow_find(124)
        hash_ = shadow_find(35)
        if pipe == -1:
            if hash_ == -1:
                return None
            return self(hash_ + 1, -2)
        if hash_ == -1 or pipe < hash_:
            return None
        return self(hash_ + 1, pipe)

    @fragment.setter
    def fragment(self, value: str):
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

    @property
    def title(self) -> str:
        """Target's title

        getter: get target's title (do not include the # character)
        setter: set a new title (do not include the # character)
        deleter: return new title, including the # character.
        """
        shadow_find = self._shadow.find
        hash_ = shadow_find(35)
        pipe = shadow_find(124)
        if hash_ == -1:
            if pipe == -1:
                return self(2, -2)
            return self(2, pipe)
        if pipe == -1:
            return self(2, hash_)
        if hash_ < pipe:
            return self(2, hash_)
        return self(2, pipe)

    @title.setter
    def title(self, newtitle) -> None:
        shadow_find = self._shadow.find
        hash_ = shadow_find(35)
        pipe = shadow_find(124)
        if hash_ == -1:
            if pipe == -1:
                self[2:-2] = newtitle
                return
            self[2:pipe] = newtitle
            return
        if pipe == -1:
            self[2:hash_] = newtitle
            return
        if hash_ < pipe:
            self[2:hash_] = newtitle
            return
        self[2:pipe] = newtitle

    @title.deleter
    def title(self) -> None:
        shadow_find = self._shadow.find
        hash_ = shadow_find(35)
        pipe = shadow_find(124)
        if hash_ == -1:
            if pipe == -1:
                del self[2:-2]
                return
            del self[2:pipe]
            return
        if pipe == -1:
            del self[2:hash_ + 1]
            return
        if hash_ < pipe:
            del self[2:hash_ + 1]
            return
        del self[2:pipe]
