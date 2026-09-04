from __future__ import annotations

from bisect import insort
from collections.abc import Iterable, MutableSequence

from regex import DOTALL, Match

from ._spans import TypeToSpans
from ._wikilist import WikiList
from ._wikitext import SECTION_HEADING, SubWikiText, rc

ARG_SHADOW_FULLMATCH = rc(
    rb'[|:](?<pre_eq>(?:[^=]*+(?:'
    + SECTION_HEADING
    + rb'\R)?+)*+)(?:\Z|(?<eq>=)(?<post_eq>.*+))',
    DOTALL,
).fullmatch


class Argument(SubWikiText):
    """Create a new Argument Object.

    Note that in MediaWiki documentation `arguments` are (also) called
    parameters. In this module the convention is:
    {{{parameter}}}, {{template|argument}}.
    See https://www.mediawiki.org/wiki/Help:Templates for more information.
    """

    __slots__ = '_ignore_equals', '_parent', '_shadow_match_cache'

    def __init__(
        self,
        string: str | MutableSequence[str],
        _type_to_spans: TypeToSpans | None = None,
        _span: list[int] | None = None,
        _type: str | int | None = None,
        _parent: SubWikiTextWithArgs | None = None,
    ):
        super().__init__(string, _type_to_spans, _span, _type)
        self._ignore_equals = _parent._ignore_equals if _parent != None else False
        self._parent = _parent or self
        self._shadow_match_cache = None, None

    @property
    def _shadow_match(self) -> Match[bytes]:
        cached_shadow_match, cache_string = self._shadow_match_cache
        self_string = str(self)
        if cache_string == self_string:
            return cached_shadow_match  # type: ignore
        ss, se, _, _ = self._span_data
        parent = self._parent
        ps = parent._span_data[0]
        shadow_match = ARG_SHADOW_FULLMATCH(parent._shadow[ss - ps : se - ps])
        self._shadow_match_cache = shadow_match, self_string
        return shadow_match  # type: ignore

    @property
    def name(self) -> str:
        """Argument's name.

        getter: return the position as a string, for positional arguments.
        setter: convert it to keyword argument if positional.
        """
        ss = self._span_data[0]
        shadow_match = self._shadow_match
        if not self._ignore_equals and shadow_match['eq']:
            s, e = shadow_match.span('pre_eq')
            return self._lststr[0][ss + s : ss + e]
        # positional argument
        position = 1
        parent_find = self._parent._shadow.find
        parent_start = self._parent._span_data[0]
        for s, e, _, _ in self._type_to_spans[self._type]:
            if ss <= s:
                break
            if parent_find(b'=', s - parent_start, e - parent_start) != -1:
                # This is a keyword argument.
                continue
            # This is a preceding positional argument.
            position += 1
        return str(position)

    @name.setter
    def name(self, newname: str) -> None:
        if not self._ignore_equals and self._shadow_match['eq']:
            self[1 : 1 + len(self._shadow_match['pre_eq'])] = newname
        else:
            self.insert(1, newname + '=')

    @property
    def positional(self) -> bool:
        """True if self is positional, False if keyword.

        setter:
            If set to False, convert self to keyword argumentn.
            Raise ValueError on trying to convert positional to keyword
            argument.
        """
        return self._ignore_equals or not self._shadow_match['eq']

    @positional.setter
    def positional(self, to_positional: bool) -> None:
        shadow_match = self._shadow_match
        if not self._ignore_equals and shadow_match['eq']:
            # Keyword argument
            if to_positional:
                del self[1 : shadow_match.end('eq')]
            else:
                return
        if to_positional:
            # Positional argument. to_positional is True.
            return
        # Positional argument. to_positional is False.
        raise ValueError(
            'Converting positional argument to keyword argument is not '
            'possible without knowing the new name. '
            'You can use `self.name = somename` instead.'
        )

    @property
    def value(self) -> str:
        """Value of self.

        Support both keyword or positional arguments.
        getter:
            Return value of self.
        setter:
            Assign a new value to self.
        """
        shadow_match = self._shadow_match
        if not self._ignore_equals and shadow_match['eq']:
            return self(shadow_match.start('post_eq'), None)
        return self(1, None)

    @value.setter
    def value(self, newvalue: str) -> None:
        shadow_match = self._shadow_match
        if not self._ignore_equals and shadow_match['eq']:
            self[shadow_match.start('post_eq') :] = newvalue
        else:
            self[1:] = newvalue

    @property
    def _lists_shadow_ss(self):
        shadow_match = self._shadow_match
        if not self._ignore_equals and shadow_match['eq']:
            post_eq = shadow_match['post_eq']
            ls_post_eq = post_eq.lstrip()
            return (
                bytearray(ls_post_eq),
                self._span_data[0]
                + shadow_match.start('post_eq')
                + len(post_eq)
                - len(ls_post_eq),
            )
        return bytearray(shadow_match[0][1:]), self._span_data[0] + 1


class SubWikiTextWithArgs(SubWikiText):
    """Define common attributes for `Template` and `ParserFunction`."""

    __slots__ = ()

    _name_args_matcher = NotImplemented
    _first_arg_sep = 0
    _ignore_equals = False

    @property
    def _content_span(self) -> tuple[int, int]:
        return 2, -2

    @property
    def nesting_level(self) -> int:
        """Return the nesting level of self.

        The minimum nesting_level is 0. Being part of any Template or
        ParserFunction increases the level by one.
        """
        return self._nesting_level(('Template', 'ParserFunction'))

    @property
    def arguments(self) -> list[Argument]:
        """Parse template content. Create self.name and self.arguments."""
        shadow = self._shadow
        split_spans = self._name_args_matcher(shadow, 2, -2).spans('arg')
        if not split_spans:
            return []
        arguments = []
        arguments_append = arguments.append
        type_to_spans = self._type_to_spans
        ss, se, _, _ = span = self._span_data
        type_ = id(span)
        lststr = self._lststr
        arg_spans = type_to_spans.setdefault(type_, [])
        span_tuple_to_span_get = {(s[0], s[1]): s for s in arg_spans}.get
        for arg_self_start, arg_self_end in split_spans:
            # todo: add byte array
            s, e, _, _ = arg_span = [
                ss + arg_self_start,
                ss + arg_self_end,
                None,
                None,
            ]
            old_span = span_tuple_to_span_get((s, e))
            if old_span is None:
                insort(arg_spans, arg_span)
            else:
                arg_span = old_span
            arg = Argument(lststr, type_to_spans, arg_span, type_, self)
            arg._span_data[3] = shadow[arg_self_start:arg_self_end]
            arguments_append(arg)
        return arguments

    def get_lists(
        self, pattern: str | Iterable[str] = (r'\#', r'\*', '[:;]')
    ) -> list[WikiList]:
        """Return the lists in all arguments.

        For performance reasons it is usually preferred to get a specific
        Argument and use the `get_lists` method of that argument instead.
        """
        return [
            lst
            for arg in self.arguments
            for lst in arg.get_lists(pattern)
            if lst
        ]

    @property
    def name(self) -> str:
        """Template's name (includes whitespace).

        getter: Return the name.
        setter: Set a new name.
        """
        sep = self._shadow.find(self._first_arg_sep)
        if sep == -1:
            return self(2, -2)
        return self(2, sep)

    @name.setter
    def name(self, newname: str) -> None:
        self[2 : 2 + len(self.name)] = newname
