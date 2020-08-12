"""Define the WikiLink class."""


from typing import List, Optional

from regex import DOTALL, compile

from ._wikitext import SubWikiText

FULLMATCH = compile(
    rb'\[\0*+\['
    rb'('  # 1: target
    rb'([^|#\]]*+)'  # 2: title
    rb'(?>#([^|\]]*+))?'  # 3: fragment
    rb')'
    rb'(?:\|(.*))?'  # 4: text
    rb'\]\0*+\]', DOTALL).fullmatch


class WikiLink(SubWikiText):

    __slots__ = '_cached_match'

    @property
    def _match(self):
        shadow = self._shadow
        cached_match = getattr(self, '_cached_match', None)
        if cached_match is not None and cached_match.string == shadow:
            return cached_match
        self._cached_match = match = FULLMATCH(shadow)
        return match

    @property
    def target(self) -> str:
        """WikiLink's target, including the fragment.

        Do not include the pipe (|) in setter and getter.
        Deleter: delete the link target, including the pipe character.
            Use `self.target = ''` if you don't want to remove the pipe.
        """
        b, e = self._match.span(1)
        return self(b, e)

    @target.setter
    def target(self, s: str) -> None:
        b, e = self._match.span(1)
        self[b:e] = s

    @target.deleter
    def target(self) -> None:
        m = self._match
        b, e = m.span(1)
        if m[4] is None:
            del self[b:e]
            return
        del self[b:e + 1]

    @property
    def text(self) -> Optional[str]:
        """The [[inner text| of WikiLink ]] (not including the [[link]]trail).

        setter: set a new value for self.text. Do not include the pipe.
        deleter: delete self.text, including the pipe.
        """
        b, e = self._match.span(4)
        if b == -1:
            return None
        return self(b, e)

    @text.setter
    def text(self, s: str) -> None:
        m = self._match
        b, e = m.span(4)
        if b == -1:
            self.insert(m.end(1), '|' + s)
            return
        self[b:e] = s

    @text.deleter
    def text(self):
        b, e = self._match.span(4)
        if b == -1:
            return
        del self[b - 1:e]

    @property
    def fragment(self) -> Optional[str]:
        """Fragment identifier.

        getter: target's fragment identifier (do not include the # character)
        setter: set a new fragment (do not include the # character)
        deleter: delete fragment, including the # character.
        """
        b, e = self._match.span(3)
        if b == -1:
            return None
        return self(b, e)

    @fragment.setter
    def fragment(self, s: str):
        m = self._match
        b, e = m.span(3)
        if b == -1:
            self.insert(m.end(2), '#' + s)
            return
        self[b:e] = s

    @fragment.deleter
    def fragment(self):
        b, e = self._match.span(3)
        if b == -1:
            return
        del self[b - 1:e]

    @property
    def title(self) -> str:
        """Target's title

        getter: get target's title (do not include the # character)
        setter: set a new title (do not include the # character)
        deleter: return new title, including the # character.
        """
        s, e = self._match.span(2)
        return self(s, e)

    @title.setter
    def title(self, s) -> None:
        b, e = self._match.span(2)
        self[b:e] = s

    @title.deleter
    def title(self) -> None:
        m = self._match
        s, e = m.span(2)
        if m[3] is None:
            del self[s:e]
        else:
            del self[s:e + 1]

    @property
    def wikilinks(self) -> List['WikiLink']:
        return super().wikilinks[1:]

    @property
    def _relative_contents_end(self) -> tuple:
        return self._match.span(4)
