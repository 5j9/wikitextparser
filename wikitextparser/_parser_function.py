from __future__ import annotations

from ._argument import Argument, SubWikiTextWithArgs
from ._comment_bold_italic import COMMENT_PATTERN
from ._wikitext import WS, rc

COMMENT_SUB = rc(COMMENT_PATTERN).sub

PF_NAME_ARGS_FULLMATCH = rc(
    rb'[^:|}]*+(?#name)' rb'(?<arg>:[^|]*+)?+(?<arg>\|[^|]*+)*+'
).fullmatch


class ParserFunction(SubWikiTextWithArgs):
    """Convert strings to ParserFunction objects.

    The string should start with {{ and end with }}.
    """
    __slots__ = ()

    _name_args_matcher = PF_NAME_ARGS_FULLMATCH
    _first_arg_sep = 58


    def normal_name(self) -> str:
        """Return normal form of self.name.

        - Remove comments.
        - Lowercase.
        """
        return COMMENT_SUB('', self.name).lstrip(WS).lower()

    def get_last_positional_index(self, ignore_equals: bool) -> int:
        return super()._get_last_positional_index(ignore_equals=ignore_equals)

    def get_arg(self, name: str, *, ignore_equals: bool) -> Argument | None:
        """Return the last argument with the given name.

        Return None if no argument with that name is found.
        """
        return super()._get_arg(name, ignore_equals=ignore_equals)

    def has_arg(self, name: str, value: str | None = None, *, ignore_equals: bool) -> bool:
        """Return true if there is an arg named `name`.

        Also check equality of values if `value` is provided.

        Note: If you just need to get an argument and you want to LBYL, it's
            better to get_arg directly and then check if the returned value
            is None.
        """
        return super()._has_arg(name, value, ignore_equals=ignore_equals)

    def set_arg(
        self,
        name: str | None,
        value: str,
        positional: bool | None = None,
        before: str | None = None,
        after: str | None = None,
        preserve_spacing: bool = False,
        *,
        ignore_equals: bool
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
        super()._set_arg(name, value, positional, before, after, preserve_spacing, ignore_equals=ignore_equals)

    def del_arg(self, name: str, *, ignore_equals: bool) -> None:
        """Delete all arguments with the given then."""
        super()._del_arg(name, ignore_equals=ignore_equals)

    @property
    def parser_functions(self) -> list[ParserFunction]:
        return super().parser_functions[1:]
