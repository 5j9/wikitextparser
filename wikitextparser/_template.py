from __future__ import annotations

from typing import TypeVar

from ._argument import Argument, SubWikiTextWithArgs
from ._comment_bold_italic import COMMENT_PATTERN
from ._wikitext import WS, rc

COMMENT_SUB = rc(COMMENT_PATTERN).sub

TL_NAME_ARGS_FULLMATCH = rc(rb'[^|}]*+(?#name)(?<arg>\|[^|]*+)*+').fullmatch

T = TypeVar('T')


class Template(SubWikiTextWithArgs):
    """Convert strings to Template objects.

    The string should start with {{ and end with }}.
    """

    __slots__ = ()

    _name_args_matcher = TL_NAME_ARGS_FULLMATCH
    _first_arg_sep = 124


    def normal_name(
        self,
        rm_namespaces=('Template',),
        *,
        code: str | None = None,
        capitalize=False,
    ) -> str:
        """Return normal form of self.name.

        - Remove comments.
        - Remove language code.
        - Remove namespace ("template:" or any of `localized_namespaces`.
        - Use space instead of underscore.
        - Remove consecutive spaces.
        - Use uppercase for the first letter if `capitalize`.
        - Remove #anchor.

        :param rm_namespaces: is used to provide additional localized
            namespaces for the template namespace. They will be removed from
            the result. Default is ('Template',).
        :param capitalize: If True, convert the first letter of the
            template's name to a capital letter. See
            [[mw:Manual:$wgCapitalLinks]] for more info.
        :param code: is the language code.

        Example:
            >>> Template(
            ...     '{{ eN : tEmPlAtE : <!-- c --> t_1 # b | a }}'
            ... ).normal_name(code='en')
            'T 1'
        """
        # Remove comments
        name = COMMENT_SUB('', self.name).strip(WS)
        # Remove code
        if code:
            head, sep, tail = name.partition(':')
            if not head and sep:
                name = tail.strip(' ')
                head, sep, tail = name.partition(':')
            if code.lower() == head.strip(' ').lower():
                name = tail.strip(' ')
        # Remove namespace
        head, sep, tail = name.partition(':')
        if not head and sep:
            name = tail.strip(' ')
            head, sep, tail = name.partition(':')
        if head:
            ns = head.strip(' ').lower()
            for namespace in rm_namespaces:
                if namespace.lower() == ns:
                    name = tail.strip(' ')
                    break
        # Use space instead of underscore
        name = name.replace('_', ' ')
        if capitalize:
            # Use uppercase for the first letter
            name = name[:1].upper() + name[1:]
        # Remove #anchor
        name, sep, tail = name.partition('#')
        return ' '.join(name.split())

    def get_last_positional_index(self) -> int:
        return super()._get_last_positional_index(ignore_equals=False)

    def get_arg(self, name: str) -> Argument | None:
        """Return the last argument with the given name.

        Return None if no argument with that name is found.
        """
        return super()._get_arg(name, ignore_equals=False)

    def has_arg(self, name: str, value: str | None = None) -> bool:
        """Return true if there is an arg named `name`.

        Also check equality of values if `value` is provided.

        Note: If you just need to get an argument and you want to LBYL, it's
            better to get_arg directly and then check if the returned value
            is None.
        """
        return super()._has_arg(name, value, ignore_equals=False)

    def set_arg(
        self,
        name: str | None,
        value: str,
        positional: bool | None = None,
        before: str | None = None,
        after: str | None = None,
        preserve_spacing: bool = False,
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
        super()._set_arg(name, value, positional, before, after, preserve_spacing, ignore_equals=False)

    def del_arg(self, name: str) -> None:
        """Delete all arguments with the given then."""
        super()._del_arg(name, ignore_equals=False)

    @property
    def templates(self) -> list[Template]:
        return super().templates[1:]
