from typing import Dict, Iterable, List, Match, MutableSequence, Union
from warnings import warn

from regex import MULTILINE, escape, fullmatch

from ._wikitext import SubWikiText

SUBLIST_PATTERN = (  # noqa
    rb'(?>^'
        rb'(?&pattern)'
        rb'[:;#*].*+'
        rb'(?>\n|\Z)'
    rb')*+')
LIST_PATTERN_FORMAT = (  # noqa
    rb'(?<fullitem>^'
        rb'(?<pattern>{pattern})'
        rb'(?(?<=;\s*+)'
            # mark inline definition as an item
            rb'(?<item>[^:\n]*+)(?<fullitem>:(?<item>.*+))?+'
            rb'(?>\n|\Z)' + SUBLIST_PATTERN +
            rb'|'
            # non-definition
            rb'(?<item>.*+)'
            rb'(?>\n|\Z)' + SUBLIST_PATTERN +
        rb')'
    rb')++')


class WikiList(SubWikiText):

    """Class to represent ordered, unordered, and definition lists."""

    __slots__ = 'pattern', '_match_cache'

    def __init__(
        self,
        string: Union[str, MutableSequence[str]],
        pattern: str,
        _match: Match = None,
        _type_to_spans: Dict[str, List[List[int]]] = None,
        _span: List[int] = None,
        _type: str = None,
    ) -> None:
        super().__init__(string, _type_to_spans, _span, _type)
        self.pattern = pattern
        if _match:
            self._match_cache = _match, self.string
        else:
            self._match_cache = fullmatch(
                LIST_PATTERN_FORMAT.replace(
                    b'{pattern}', pattern.encode(), 1),
                self._shadow,
                MULTILINE,
            ), self.string

    @property
    def _match(self):
        """Return the match object for the current list."""
        cache_match, cache_string = self._match_cache
        string = self.string
        if cache_string == string:
            return cache_match
        cache_match = fullmatch(
            LIST_PATTERN_FORMAT.replace(
                b'{pattern}', self.pattern.encode(), 1),
            self._shadow,
            MULTILINE)
        self._match_cache = cache_match, string
        return cache_match

    @property
    def items(self) -> List[str]:
        """Return items as a list of strings.

        Don't include sub-items and the start pattern.
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
        self, i: int = None,
        pattern: Union[str, Iterable[str]] = (r'\#', r'\*', '[:;]')
    ) -> List['WikiList']:
        """Return the Lists inside the item with the given index.

        :param i: The index if the item which its sub-lists are desired.
        :param pattern: The starting symbol for the desired sub-lists.
            The `pattern` of the current list will be automatically added
            as prefix.
        """
        if pattern is None:
            warn('calling sublists with None pattern is deprecated; '
                 'Use the default value instead.', DeprecationWarning)
            patterns = (r'\#', r'\*', '[:;]')
        elif isinstance(pattern, str):
            patterns = (pattern,)
        else:
            patterns = pattern
        self_pattern = self.pattern
        get_lists = super().get_lists
        sublists = []  # type: List['WikiList']
        sublists_append = sublists.append
        if i is None:
            # Any sublist is acceptable
            for pattern in patterns:
                for lst in get_lists(self_pattern + pattern):
                    sublists_append(lst)
            return sublists
        # Only return sub-lists that are within the given item
        match = self._match
        fullitem_spans = match.spans('fullitem')
        ss = self._span_data[0]
        ms = match.start()
        s, e = fullitem_spans[i]
        e -= ms - ss
        s -= ms - ss
        for pattern in patterns:
            for lst in get_lists(self_pattern + pattern):
                # noinspection PyProtectedMember
                ls, le, _, _ = lst._span_data
                if s < ls and le <= e:
                    sublists_append(lst)
        return sublists

    def convert(self, newstart: str) -> None:
        """Convert to another list type by replacing starting pattern."""
        match = self._match
        ms = match.start()
        for s, e in reversed(match.spans('pattern')):
            self[s - ms:e - ms] = newstart
        self.pattern = escape(newstart)

    def get_lists(
        self, pattern: Union[str, Iterable[str]] = (r'\#', r'\*', '[:;]')
    ) -> List['WikiList']:
        if pattern is None:
            warn('calling get_lists with None pattern is deprecated; '
                 'Use the default value instead.', DeprecationWarning)
            pattern = (r'\#', r'\*', '[:;]')
        return self.sublists(pattern=pattern)
