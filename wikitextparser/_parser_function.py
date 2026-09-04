from __future__ import annotations

from collections.abc import Iterable

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
    _ignore_equals = True


    def normal_name(self) -> str:
        """Return normal form of self.name.

        - Remove comments.
        - Lowercase
        """
        return COMMENT_SUB('', self.name).lstrip(WS).lower()

    def set_arg(
        self,
        name: str | None,
        value: str,
    ) -> None:
        """Set the value for `name` argument. Add it if it doesn't exist.
        """
        args = (*reversed(self.arguments),)
        if name is not None:
            # Invalid
            if not is_positive_integer(name):
                return

            # Updating an existing argument.
            arg = get_arg(name, args)
            if arg:
                arg.positional = True
                arg.value = value
                return

        last_idx = get_last_idx_positional_args(args)

        # Invalid, as it would need to fill the pf with empty arguments
        if name and (last_idx != int(name) - 1):
            return

        # Adding a new argument
        addstring = (':' if last_idx == 0 else '|') + value
        self.insert(-2, addstring)

    def get_arg(self, name: str) -> Argument | None:
        """Return the last argument with the given name.

        Return None if no argument with that name is found.
        """
        return get_arg(name, reversed(self.arguments))

    def has_arg(self, name: str, value: str | None = None) -> bool:
        """Return true if the is an arg named `name`.

        Also check equality of values if `value` is provided.

        Note: If you just need to get an argument and you want to LBYL, it's
            better to get_arg directly and then check if the returned value
            is None.
        """
        for arg in reversed(self.arguments):
            if arg.name.strip(WS) == name.strip(WS):
                if value:
                    return arg.value == value
                return True
        return False

    def del_arg(self, name: str) -> None:
        """Delete all arguments with the given then."""
        for arg in reversed(self.arguments):
            if arg.name.strip(WS) == name.strip(WS):
                del arg[:]

    @property
    def parser_functions(self) -> list[ParserFunction]:
        return super().parser_functions[1:]


def is_positive_integer(x):
    try:
        return int(x) > 0
    except ValueError:
        return False

def get_arg(name: str, args: Iterable[Argument]) -> Argument | None:
    """Return the first argument in the args that has the given name.

    Return None if no such argument is found.

    As the computation of self.arguments is a little costly, this
    function was created so that other methods that have already computed
    the arguments use it instead of calling self.get_arg directly.
    """
    for arg in args:
        if arg.name.strip(WS) == name.strip(WS):
            return arg
    return None

def get_last_idx_positional_args(args: Iterable[Argument]) -> int:
    idx = 0
    for arg in args:
        if arg.positional:
            idx += 1
    return idx
