"""Define the class for List objects."""


from typing import List, Union, Tuple, Dict, MutableSequence, Match

import regex

from .wikitext import SubWikiText


SUBLIST_PATTERN = r'(?>^(?P<startchars>{startchars})[:;#*].*(?>\n|\Z))*'
LIST_PATTERN = (
    r'(?P<fullitem>^(?P<startchars>{startchars})(?P<item>.*)(?>\n|\Z)%s)+'
    % SUBLIST_PATTERN
)


class WikiList(SubWikiText):

    """Class to represent ordered, unordered, and definition lists."""

    def __init__(
        self,
        string: Union[str, MutableSequence[str]],
        startchars: str,
        _match: Match=None,
        _type_to_spans: Dict[str, List[Tuple[int, int]]]=None,
        _index: int=None,
        _type: str=None,
    ) -> None:
        super().__init__(string, _type_to_spans, _index, _type)
        if startchars == ';' or startchars == ':':
            startchars = ';:'
        self.startchars = startchars
        if _match:
            self._cached_match = _match
        else:
            self._cached_match = regex.fullmatch(
                LIST_PATTERN.format(startchars=startchars.replace('*', r'\*')),
                self._shadow,
                regex.MULTILINE,
            )

    @property
    def _match(self):
        """Return the match object for the current list."""
        match = self._cached_match
        s, e = match.span()
        shadow = self._shadow
        if s + len(shadow) == e and match.string.find(shadow) == s:
            return match
        match = regex.fullmatch(
            LIST_PATTERN.format(types=self.types),
            self._shadow,
            regex.MULTILINE,
        )
        self._cached_match = match
        return match

    @property
    def items(self) -> List[str]:
        """Return items as a list of strings.

        Don't include subitems and the startchars.

        """
        # todo: special care is needed for description lists
        items = []
        append = items.append
        string = self.string
        match = self._match
        ms = match.start()
        for s, e in match.spans('item'):
            append(string[s - ms:e - ms])
        return items

    @property
    def fullitems(self) -> List[str]:
        """Return a list item strings including their start and sub-items."""
        fullitems = []
        append = fullitems.append
        string = self.string
        match = self._match
        ms = match.start()
        for s, e in match.spans('fullitem'):
            append(string[s - ms:e - ms])
        return fullitems

    @property
    def level(self) -> int:
        """Return level of nesting for the current list.

        Level is zero-based i.e. the level for list `* a` is zero.

        """
        return len(self.startchars) - 1

    def sublists(
        self, i: int, startchars: str
    ) -> List['WikiList']:
        """Return the Lists inside the item with the given item index.

        :startchars: The starting symbol for the desired sub-lists.
            The `startchars` of the current list will be automatically added
            as prefix.

        """
        match = self._match
        ms = match.start()
        s, e = match.spans('fullitem')[i]
        s -= ms
        e -= ms
        sublists = []
        startchars = self.startchars + startchars
        for lst in self.lists(startchars):
            ls, le = lst._span
            if s < ls and le <= e:
                sublists.append(lst)
        return sublists

    def convert(self, newstartchars: str) -> None:
        """Convert to another list type by replacing List's startchars."""
        match = self._match
        ms = match.start()
        for s, e in match.spans('startchars'):
            self[s - ms:e - ms] = newstartchars


