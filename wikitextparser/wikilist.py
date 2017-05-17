"""Define the class for List objects."""

from typing import List, Union, Tuple, Dict, MutableSequence, Match

import regex

from .wikitext import SubWikiText


SUBLIST_PATTERN = r'(?>^(?<pattern>{pattern})[:;#*].*(?>\n|\Z))*'
LIST_PATTERN_FORMAT = (
    r'''
    (?<fullitem>
        ^
        (?<pattern>{pattern})
        (?(?<=;\s*)
            # mark inline definition as an item
            (?<item>[^:\n]*)(?<fullitem>:(?<item>.*))?
            (?>\n|\Z)%s
            |
            # non-definition
            (?<item>.*)
            (?>\n|\Z)%s
        )
    )+
    '''
    % (SUBLIST_PATTERN, SUBLIST_PATTERN)
).format


class WikiList(SubWikiText):

    """Class to represent ordered, unordered, and definition lists."""

    def __init__(
        self,
        string: Union[str, MutableSequence[str]],
        pattern: str,
        _match: Match=None,
        _type_to_spans: Dict[str, List[List[int]]]=None,
        _span: List[int]=None,
        _type: str=None,
    ) -> None:
        super().__init__(string, _type_to_spans, _span, _type)
        self.pattern = pattern
        if _match:
            self._cached_match = _match
        else:
            self._cached_match = regex.fullmatch(
                LIST_PATTERN_FORMAT(pattern=pattern),
                self._shadow,
                regex.MULTILINE | regex.VERBOSE,
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
            LIST_PATTERN_FORMAT(pattern=self.pattern),
            self._shadow,
            regex.MULTILINE | regex.VERBOSE,
        )
        self._cached_match = match
        return match

    @property
    def items(self) -> List[str]:
        """Return items as a list of strings.

        Don't include subitems and the start pattern.

        """
        items = []  # type: List[str]
        append = items.append
        string = self.string
        match = self._match
        ms = match.start()
        for s, e in match.spans('item'):
            append(string[s - ms:e - ms])
        return items

    @property
    def fullitems(self) -> List[str]:
        """Return list of item strings. Includes their start and sub-items."""
        fullitems = []  # type: List[str]
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

        Level is a one-based index, for example the level for `* a` will be 1.

        """
        return len(self._match['pattern'])

    def sublists(
        self, i: int=None, pattern: str=None
    ) -> List['WikiList']:
        """Return the Lists inside the item with the given index.

        :i: The index if the item which its sub-lists are desired.
            The performance is likely to be better if `i` is None.

        :pattern: The starting symbol for the desired sub-lists.
            The `pattern` of the current list will be automatically added
            as prefix.
            Although this parameter is optional, but specifying it can improve
            the performance.

        """
        patterns = ('\#', '\*', '[:;]') if pattern is None \
            else (pattern,)  # type: Tuple[str, ...]
        self_pattern = self.pattern
        lists = self.lists
        sublists = []  # type: List['WikiList']
        sublists_append = sublists.append
        if i is None:
            # Any sublist is acceptable
            for pattern in patterns:
                for lst in lists(self_pattern + pattern):
                    sublists_append(lst)
            return sublists
        # Only return sub-lists that are within the given item
        match = self._match
        fullitem_spans = match.spans('fullitem')
        ss = self._span[0]
        ms = match.start()
        s, e = fullitem_spans[i]
        e -= ms - ss
        s -= ms - ss
        for pattern in patterns:
            for lst in lists(self_pattern + pattern):
                ls, le = lst._span
                if s < ls and le <= e:
                    sublists_append(lst)
        return sublists

    def convert(self, newstart: str) -> None:
        """Convert to another list type by replacing starting pattern."""
        match = self._match
        ms = match.start()
        for s, e in reversed(match.spans('pattern')):
            self[s - ms:e - ms] = newstart
        self.pattern = regex.escape(newstart)
