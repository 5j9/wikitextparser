from __future__ import annotations

from bisect import insort
from collections.abc import Callable, Iterable, MutableSequence
from typing import ClassVar, NamedTuple, TypeVar

from regex import DOTALL, REVERSE, Match

from wikitextparser._spans import SpanData

from ._spans import TypeToSpans
from ._wikilist import WikiList
from ._wikitext import SECTION_HEADING, WS, SubWikiText, rc

ARG_SHADOW_FULLMATCH = rc(
    rb'[|:](?<pre_eq>(?:[^=]*+(?:'
    + SECTION_HEADING
    + rb'\R)?+)*+)(?:\Z|(?<eq>=)(?<post_eq>.*+))',
    DOTALL,
).fullmatch
ENDING_WS_MATCH = rc(r'(?>\R[ \t]*)*+', REVERSE).match

T = TypeVar('T')


class Argument(SubWikiText):
    """Create a new Argument Object.

    Note that in MediaWiki documentation `arguments` are (also) called
    parameters. In this module the convention is:
    {{{parameter}}}, {{template|argument}}.
    See https://www.mediawiki.org/wiki/Help:Templates for more information.
    """

    __slots__ = '_parent', '_shadow_match_cache'

    def __init__(
        self,
        string: str | MutableSequence[str],
        _type_to_spans: TypeToSpans | None = None,
        _span: SpanData | None = None,
        _type: str | int | None = None,
        _parent: SubWikiTextWithArgs | None = None,
    ):
        super().__init__(string, _type_to_spans, _span, _type)
        self._parent = _parent or self
        self._shadow_match_cache: tuple[bytearray | None, str | None] = (
            None,
            None,
        )

    @property
    def _shadow_match(self) -> Match[bytes]:
        cached_shadow_match, cache_string = self._shadow_match_cache
        self_string = str(self)
        if cache_string == self_string:
            return cached_shadow_match  # type: ignore
        spand_data = self._span_data
        parent = self._parent
        ps = parent._span_data.start
        shadow_match = ARG_SHADOW_FULLMATCH(
            parent._shadow[spand_data.start - ps : spand_data.end - ps]
        )
        self._shadow_match_cache = shadow_match, self_string
        return shadow_match  # type: ignore

    @property
    def name(self) -> str:
        """Argument's name.

        getter: return the position as a string, for positional arguments.
        setter: convert it to keyword argument if positional.
        """
        ss = self._span_data.start
        shadow_match = self._shadow_match
        if shadow_match['eq']:
            s, e = shadow_match.span('pre_eq')
            return self._lststr[0][ss + s : ss + e]
        # positional argument
        position = 1
        parent_find = self._parent._shadow.find
        parent_start = self._parent._span_data.start
        for spand_data in self._type_to_spans[self._type]:
            if ss <= (s := spand_data.start):
                break
            if (
                parent_find(
                    b'=', s - parent_start, spand_data.end - parent_start
                )
                != -1
            ):
                # This is a keyword argument.
                continue
            # This is a preceding positional argument.
            position += 1
        return str(position)

    @name.setter
    def name(self, newname: str) -> None:
        if self._shadow_match['eq']:
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
        return not self._shadow_match['eq']

    @positional.setter
    def positional(self, to_positional: bool) -> None:
        shadow_match = self._shadow_match
        if shadow_match['eq']:
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
        if shadow_match['eq']:
            return self(shadow_match.start('post_eq'), None)
        return self(1, None)

    @value.setter
    def value(self, newvalue: str) -> None:
        shadow_match = self._shadow_match
        if shadow_match['eq']:
            self[shadow_match.start('post_eq') :] = newvalue
        else:
            self[1:] = newvalue

    @property
    def _lists_shadow_ss(self):
        shadow_match = self._shadow_match
        if shadow_match['eq']:
            post_eq = shadow_match['post_eq']
            ls_post_eq = post_eq.lstrip()
            return (
                bytearray(ls_post_eq),
                self._span_data.start
                + shadow_match.start('post_eq')
                + len(post_eq)
                - len(ls_post_eq),
            )
        return bytearray(shadow_match[0][1:]), self._span_data.start + 1


class ArgSpacing(NamedTuple):
    before_name: str
    name_length: int
    before_value: str
    after_value: str
    last_arg_after_value: str


class SubWikiTextWithArgs(SubWikiText):
    """Define common attributes for `Template` and `ParserFunction`."""

    __slots__ = (
        '_first_arg_sep',
        '_name_args_matcher',
    )

    _name_args_matcher: ClassVar[Callable]
    _first_arg_sep: ClassVar[int]

    def __init__(
        self,
        string: str | MutableSequence[str],
        _type_to_spans: TypeToSpans | None = None,
        _span: SpanData | None = None,
        _type: str | int | None = None,
    ) -> None:
        super().__init__(string, _type_to_spans, _span, _type)

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
        shadow_match = self._name_args_matcher(shadow, 2, -2)
        split_spans = shadow_match.spans('arg')
        arguments = []

        if split_spans:
            arguments_append = arguments.append
            type_to_spans = self._type_to_spans
            span = self._span_data
            ss = span.start
            type_ = id(span)
            lststr = self._lststr
            arg_spans = type_to_spans.setdefault(type_, [])
            span_tuple_to_span_get = {
                (s.start, s.end): s for s in arg_spans
            }.get
            for arg_self_start, arg_self_end in split_spans:
                # todo: add byte array
                arg_span = SpanData(
                    ss + arg_self_start,
                    ss + arg_self_end,
                    None,
                    None,
                )
                old_span = span_tuple_to_span_get(
                    (arg_span.start, arg_span.end)
                )
                if old_span is None:
                    insort(arg_spans, arg_span)
                else:
                    arg_span = old_span
                arg = Argument(lststr, type_to_spans, arg_span, type_, self)
                arg._span_data.byte_array = shadow[arg_self_start:arg_self_end]
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

    def rm_first_of_dup_args(self) -> None:
        """Eliminate duplicate arguments by removing the first occurrences.

        Remove the first occurrences of duplicate arguments, regardless of
        their value. Result of the rendered wikitext should remain the same.
        Warning: Some meaningful data may be removed from wikitext.

        Also see `rm_dup_args_safe` function.
        """
        names = set()
        for a in reversed(self.arguments):
            name = a.name.strip(WS)
            if name in names:
                del a[: len(a.string)]
            else:
                names.add(name)

    def rm_dup_args_safe(self, tag: str | None = None) -> None:
        """Remove duplicate arguments in a safe manner.

        Remove the duplicate arguments only in the following situations:
            1. Both arguments have the same name AND value. (Remove one of
                them.)
            2. Arguments have the same name and one of them is empty. (Remove
                the empty one.)

        Warning: Although this is considered to be safe and no meaningful data
            is removed from wikitext, but the result of the rendered wikitext
            may actually change if the second arg is empty and removed but
            the first had had a value.

        If `tag` is defined, it should be a string that will be appended to
        the value of the remaining duplicate arguments.

        Note: The argument that replaces an empty last occurrence survives
            but is not tagged. Example::

                >>> t = Template('{{t|a=1|a=2|a=}}')
                >>> t.rm_dup_args_safe(tag='<!-- dup -->')
                >>> t.string
                '{{t|a=1<!-- dup -->|a=2}}'

        This behavior may change in the future.

        Also see `rm_first_of_dup_args` function.
        """
        name_to_lastarg_vals: dict[str, tuple[Argument, list[str]]] = {}
        # Removing positional args affects their name. By reversing the list
        # we avoid encountering those kind of args.
        for arg in reversed(self.arguments):
            name = arg.name.strip(WS)
            if arg.positional:
                # Whitespace around positional arguments is not stripped.
                val = arg.value
            else:
                # Value of keyword arguments is automatically stripped by MW.
                val = arg.value.strip(WS)
            if name in name_to_lastarg_vals:
                # This is a duplicate argument.
                if not val:
                    # This duplicate argument is empty. It's safe to remove it.
                    del arg[0 : len(arg.string)]
                else:
                    # Try to remove any of the detected duplicates of this
                    # that are empty or their value equals to this one.
                    lastarg, dup_vals = name_to_lastarg_vals[name]
                    if val in dup_vals:
                        del arg[0 : len(arg.string)]
                    elif '' in dup_vals:
                        # This happens only if the last occurrence of name has
                        # been an empty string; other empty values will
                        # be removed as they are seen.
                        # In other words index of the empty argument in
                        # dup_vals is always 0.
                        del lastarg[0 : len(lastarg.string)]
                        dup_vals.pop(0)
                        # The current value is now represented by the remaining
                        # duplicate arguments.
                        dup_vals.append(val)
                    else:
                        # It was not possible to remove any of the duplicates.
                        dup_vals.append(val)
                        if tag:
                            arg.value += tag
            else:
                name_to_lastarg_vals[name] = (arg, [val])

    def _get_next_positional_index(
        self, *, ignore_equals: bool, args: list[Argument]
    ) -> int:
        """When ignore_equals is true, all args are considered positional."""
        if ignore_equals:
            return len(args)
        idx = 0
        for arg in args:
            if arg.positional:
                idx += 1
        return idx

    def _get_arg(self, name: str, *, ignore_equals: bool) -> Argument | None:
        """Return the last argument with the given name.

        Return None if no argument with that name is found.
        """
        stripped_name = name.strip(WS)
        if ignore_equals:
            index = to_index(stripped_name)
            if index is None:
                return None
            try:
                return self.arguments[index]
            except IndexError:
                return None
        for arg in reversed(self.arguments):
            if arg.name.strip(WS) == stripped_name:
                return arg
        return None

    def _has_arg(
        self, name: str, value: str | None, *, ignore_equals: bool
    ) -> bool:
        """Return true if there is an arg named `name`.

        Also check equality of values if `value` is provided.

        Note: If you just need to get an argument and you want to LBYL, it's
            better to get_arg directly and then check if the returned value
            is None.
        """
        a = self._get_arg(name, ignore_equals=ignore_equals)
        if a is None:
            return False
        if value is None:
            return True
        if not ignore_equals:
            if a.positional:
                return a.value == value
            return a.value.strip(WS) == value.strip(WS)
        return a.string[1:].strip(WS) == value.strip(WS)

    def _set_arg(
        self,
        name: str | None,
        value: str,
        positional: bool | None,
        before: str | None,
        after: str | None,
        preserve_spacing: bool,
        *,
        ignore_equals: bool,
    ) -> None:
        """Set the value for `name` argument. Add it if it doesn't exist.

        - Use `positional`, `before` and `after` keyword arguments only when
            adding a new argument.
        - If `before` is given, ignore `after`.
        - If neither `before` nor `after` are given and it's needed to add a
            new argument, then append the new argument to the end.
        - If `positional` is True, add the given value as a positional
            argument and ignore `preserve_spacing`.
        - If positional is None (the default), mirror the kind of the last
            existing argument when the name is the next positional index
            (positional if the last arg is positional, keyword otherwise).
        """
        if self._update_existing_arg(
            name,
            value,
            positional,
            preserve_spacing,
            ignore_equals=ignore_equals,
        ):
            return

        args = self.arguments
        name, positional = self._resolve_new_arg(
            name, positional, args, ignore_equals=ignore_equals
        )

        spacing = self._get_arg_spacing(args, positional, preserve_spacing)

        addstring = self._make_arg_string(
            name, value, positional, spacing, has_args=bool(args)
        )

        self._insert_arg(
            addstring,
            before,
            after,
            args,
            positional,
            spacing,
            ignore_equals=ignore_equals,
        )

    def _update_existing_arg(
        self,
        name: str | None,
        value: str,
        positional: bool | None,
        preserve_spacing: bool,
        *,
        ignore_equals: bool,
    ) -> bool:
        if name is None:
            return False

        arg = self._get_arg(name, ignore_equals=ignore_equals)
        if arg is None:
            return False

        if ignore_equals:
            arg.string = arg.string[0] + value
            return True

        self._update_arg_name(arg, name, positional, preserve_spacing)
        self._update_arg_value(arg, value, preserve_spacing)
        return True

    def _update_arg_name(
        self,
        arg: Argument,
        name: str,
        positional: bool | None,
        preserve_spacing: bool,
    ) -> None:
        if positional:
            arg.positional = True
        elif positional is False or not arg.positional:
            if preserve_spacing:
                old_name = arg.name
                arg.name = old_name.replace(
                    old_name.strip(WS),
                    name,
                    1,
                )
            else:
                arg.name = name

    def _update_arg_value(
        self,
        arg: Argument,
        value: str,
        preserve_spacing: bool,
    ) -> None:
        if preserve_spacing:
            old_value = arg.value
            arg.value = old_value.replace(
                old_value.strip(WS),
                value,
                1,
            )
        else:
            arg.value = value

    def _resolve_new_arg(
        self,
        name: str | None,
        positional: bool | None,
        args: list[Argument],
        *,
        ignore_equals: bool,
    ) -> tuple[str, bool]:
        if name is None:
            return (
                str(
                    self._get_next_positional_index(
                        ignore_equals=ignore_equals, args=args
                    )
                    + 1
                ),
                True,
            )

        index = to_index(name.strip(WS))
        is_next_positional = (
            index is not None
            and self._get_next_positional_index(
                ignore_equals=ignore_equals, args=args
            )
            == index
        )

        if positional:
            if not is_next_positional:
                raise ValueError(f'cannot set arg {name!r} in positional form')
            return name, True

        if positional is False or not is_next_positional:
            return name, False

        # positional is None and the name can be represented positionally.
        if ignore_equals:
            return name, True

        if not args:
            # no precedent; keyword (matches current behavior)
            return name, False

        return name, args[-1].positional

    def _get_arg_spacing(
        self,
        args: list[Argument],
        positional: bool,
        preserve_spacing: bool,
    ) -> ArgSpacing | None:
        if positional or not preserve_spacing or not args:
            return None

        before_names: list[str] = []
        name_lengths: list[int] = []
        before_values: list[str] = []
        after_values: list[str] = []

        for arg in reversed(args):
            arg_name = arg.name
            name_lengths.append(len(arg_name))
            before_names.append(arg_name[: -len(arg_name.lstrip(WS))])

            arg_value = arg.value
            before_values.append(arg_value[: -len(arg_value.lstrip(WS))])
            after_values.append(
                ENDING_WS_MATCH(arg_value)[0]  # type: ignore
            )

        return ArgSpacing(
            before_name=mode(before_names),
            name_length=mode(name_lengths),
            before_value=mode(before_values),
            after_value=mode(
                [
                    self.name[len(self.name.rstrip()) :],
                    *after_values[1:],
                ]
            ),
            last_arg_after_value=after_values[0],
        )

    def _make_arg_string(
        self,
        name: str,
        value: str,
        positional: bool,
        spacing: ArgSpacing | None,
        *,
        has_args: bool,
    ) -> str:
        addsep = '|' if has_args else chr(self._first_arg_sep)

        if positional:
            return addsep + value

        if spacing is None:
            return addsep + name + '=' + value

        return (
            addsep
            + (spacing.before_name + name.strip(WS)).ljust(spacing.name_length)
            + '='
            + spacing.before_value
            + value
            + spacing.after_value
        )

    def _insert_arg(
        self,
        addstring: str,
        before: str | None,
        after: str | None,
        args: list[Argument],
        positional: bool,
        spacing: ArgSpacing | None,
        *,
        ignore_equals: bool,
    ) -> None:
        if before:
            arg = self._get_arg(before, ignore_equals=ignore_equals)
            if arg is None:
                raise ValueError(
                    f'no argument named {before!r} to insert before'
                )
            arg.insert(0, addstring)
            return

        if after:
            arg = self._get_arg(after, ignore_equals=ignore_equals)
            if arg is None:
                raise ValueError(
                    f'no argument named {after!r} to insert after'
                )
            arg.insert(len(arg.string), addstring)
            return

        self._append_arg(addstring, args, positional, spacing)

    def _append_arg(
        self,
        addstring: str,
        args: list[Argument],
        positional: bool,
        spacing: ArgSpacing | None,
    ) -> None:
        if not args or positional:
            self.insert(-2, addstring)
            return

        arg = args[-1]
        arg_string = arg.string

        if spacing is None:
            arg.insert(len(arg_string), addstring)
            return

        # Insert after the last argument while preserving the whitespace
        # before the template's closing braces.
        arg[0 : len(arg_string)] = (
            arg.string.rstrip(WS)
            + spacing.after_value
            + addstring.rstrip(WS)
            + spacing.last_arg_after_value
        )

    def _del_arg(self, name: str, ignore_equals: bool) -> list[Argument]:
        """Delete all arguments with the given name."""
        stripped_name = name.strip(WS)
        args = self.arguments
        if ignore_equals:
            index = to_index(stripped_name)
            if index is not None:
                try:
                    del self.arguments[index][:]
                except IndexError:
                    pass
            return args
        for arg in reversed(args):
            if arg.name.strip(WS) == stripped_name:
                del arg[:]
        return args


def to_index(arg_name: str) -> int | None:
    try:
        int_name = int(arg_name)
    except ValueError:
        return None
    if int_name > 0 and str(int_name) == arg_name:
        return int_name - 1


def mode(list_: list[T]) -> T:
    """Return the most common item in the list.

    Ties are broken by first occurrence in the list (deterministic,
    unlike the previous ``set``-based implementation).

    Example:

    >>> mode([1,1,2,2,])
    1
    >>> mode([1,2,2])
    2
    >>> mode([])
    ...
    ValueError: max() arg is an empty sequence
    """
    return max({k: None for k in list_}, key=list_.count)
