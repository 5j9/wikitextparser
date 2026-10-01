from __future__ import annotations

from bisect import insort
from collections.abc import Callable, Iterable, MutableSequence
from typing import ClassVar, TypeVar

from regex import DOTALL, REVERSE, Match

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
        _span: list[int] | None = None,
        _type: str | int | None = None,
        _parent: SubWikiTextWithArgs | None = None,
    ):
        super().__init__(string, _type_to_spans, _span, _type)
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
        if shadow_match['eq']:
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
                self._span_data[0]
                + shadow_match.start('post_eq')
                + len(post_eq)
                - len(ls_post_eq),
            )
        return bytearray(shadow_match[0][1:]), self._span_data[0] + 1


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
        _span: list | None = None,
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

    def _get_next_positional_index(self, *, ignore_equals: bool) -> int:
        """When ignore_equals is true, all args are considered positional."""
        if ignore_equals:
            return len(self.arguments)
        idx = 0
        for arg in self.arguments:
            if arg.positional:
                idx += 1
        return idx

    def _get_arg(self, name: str, *, ignore_equals: bool) -> Argument | None:
        """Return the last argument with the given name.

        Return None if no argument with that name is found.
        """
        if ignore_equals:
            index = to_index(name)
            if index is None:
                return None
            try:
                return self.arguments[index]
            except IndexError:
                return None
        for arg in reversed(self.arguments):
            if arg.name.strip(WS) == name.strip(WS):
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
        - If `positional` is True, try to add the given value as a positional
            argument. Ignore `preserve_spacing` if positional is True.
            If it's None, do what seems more appropriate.
        """
        if name is not None:
            arg = self._get_arg(name, ignore_equals=ignore_equals)
            # Updating an existing argument.
            if arg is not None:
                if not ignore_equals:
                    if positional:
                        arg.positional = True
                    elif (
                        positional is False or not arg.positional
                    ):  # the second condition handles positional=None
                        if preserve_spacing:
                            old_name = arg.name
                            arg.name = old_name.replace(
                                old_name.strip(WS), name, 1
                            )
                        else:
                            arg.name = name
                    if preserve_spacing:
                        val = arg.value
                        arg.value = val.replace(val.strip(WS), value, 1)
                    else:
                        arg.value = value
                else:
                    arg.string = arg.string[0] + value
                return
            index = to_index(name)
            if positional or positional is None:
                if index is None or (
                    self._get_next_positional_index(
                        ignore_equals=ignore_equals
                    )
                    != index
                ):
                    if positional:
                        raise ValueError(
                            f'cannot set arg {name!r} in positional form'
                        )
                    positional = False
        else:
            name = f'{self._get_next_positional_index(ignore_equals=ignore_equals) + 1}'
            positional = True

        # Calculate the whitespace needed before arg-name and after arg-value.
        if not positional and preserve_spacing and len(self.arguments) > 0:
            before_names = []
            name_lengths = []
            before_values = []
            after_values = []
            for arg in reversed(self.arguments):
                aname = arg.name
                name_lengths.append(len(aname))
                before_names.append(aname[: -len(aname.lstrip(WS))])
                arg_value = arg.value
                before_values.append(arg_value[: -len(arg_value.lstrip(WS))])
                after_values.append(ENDING_WS_MATCH(arg_value)[0])  # type: ignore
            pre_name_ws_mode = mode(before_names)
            name_length_mode = mode(name_lengths)
            self_name = self.name
            post_value_ws_mode = mode(
                [self_name[len(self_name.rstrip()) :], *after_values[1:]]
            )
            pre_value_ws_mode = mode(before_values)
        else:
            preserve_spacing = False
        # Calculate the string that needs to be added to the Template.
        addsep = chr(self._first_arg_sep) if len(self.arguments) == 0 else '|'
        if positional:
            # Ignore preserve_spacing for positional args.
            addstring = addsep + value
        else:
            if preserve_spacing:
                addstring = (
                    addsep
                    + (pre_name_ws_mode + name.strip(WS)).ljust(  # type: ignore
                        name_length_mode  # type: ignore
                    )
                    + '='
                    + pre_value_ws_mode  # type: ignore
                    + value
                    + post_value_ws_mode  # type: ignore
                )
            else:
                addstring = addsep + name + '=' + value
        # Place the addstring in the right position.
        if before:
            arg = self._get_arg(before, ignore_equals=ignore_equals)
            if arg is None:
                raise ValueError(
                    f'no argument named {before!r} to insert before'
                )
            arg.insert(0, addstring)
        elif after:
            arg = self._get_arg(after, ignore_equals=ignore_equals)
            if arg is None:
                raise ValueError(
                    f'no argument named {after!r} to insert after'
                )
            arg.insert(len(arg.string), addstring)
        else:
            if len(self.arguments) > 0 and not positional:
                arg = self.arguments[-1]
                arg_string = arg.string
                if preserve_spacing:
                    # Insert after the last argument.
                    # The addstring needs to be recalculated because we don't
                    # want to change the the whitespace before final braces.
                    # noinspection PyUnboundLocalVariable
                    arg[0 : len(arg_string)] = (
                        arg.string.rstrip(WS)
                        + post_value_ws_mode  # type: ignore
                        + addstring.rstrip(WS)
                        + after_values[0]  # type: ignore
                    )
                else:
                    arg.insert(len(arg_string), addstring)
            else:
                # The template has no arguments or the new arg is
                # positional AND is to be added at the end of the template.
                self.insert(-2, addstring)

    def _del_arg(self, name: str, ignore_equals: bool) -> None:
        """Delete all arguments with the given name."""
        if ignore_equals:
            index = to_index(name)
            if index is not None:
                try:
                    del self.arguments[index][:]
                except IndexError:
                    pass
            return
        for arg in reversed(self.arguments):
            if arg.name.strip(WS) == name.strip(WS):
                del arg[:]


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
