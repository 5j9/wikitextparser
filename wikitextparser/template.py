""""Define the Template class."""

import re
import regex
from typing import List, Optional, TypeVar, Iterable, Dict, Tuple

from .wikitext import SubWikiText
from .argument import Argument


COMMENT_SUB = re.compile(
    r'<!--.*?-->',
    re.DOTALL,
).sub

BAR_SPLITS_FULLMATCH = regex.compile(
    r'{{'
    r'[^|]*'  # name
    r'(?<arg>\|[^|]*)*'
    r'}}'
).fullmatch

T = TypeVar('T')

WS = '\r\n\t '


class Template(SubWikiText):

    """Convert strings to Template objects.

    The string should start with {{ and end with }}.

    """

    @property
    def arguments(self) -> List[Argument]:
        """Parse template content. Create self.name and self.arguments."""
        arguments = []
        split_spans = BAR_SPLITS_FULLMATCH(self._shadow).spans('arg')
        if split_spans:
            arguments_append = arguments.append
            type_to_spans = self._type_to_spans
            tl_span = self._span
            type_ = id(tl_span)
            lststr = self._lststr
            arg_spans = type_to_spans.setdefault(type_, [])
            arg_spans_append = arg_spans.append
            span_tuple_to_span_get = {(s[0], s[1]): s for s in arg_spans}.get
            ss = tl_span[0]
            for s, e in split_spans:
                arg_span = [ss + s, ss + e]
                old_span = span_tuple_to_span_get((arg_span[0], arg_span[1]))
                if old_span is None:
                    arg_spans_append(arg_span)
                else:
                    arg_span = old_span
                arguments_append(
                    Argument(lststr, type_to_spans, arg_span, type_)
                )
        return arguments

    @property
    def name(self) -> str:
        """Return template's name (includes whitespace)."""
        h = self._atomic_partition('|')[0]
        if len(h) == len(self.string):
            return h[2:-2]
        return h[2:]

    @name.setter
    def name(self, newname: str) -> None:
        """Set the new name for the template."""
        name = self.name
        self[2:2 + len(name)] = newname

    def normal_name(
        self,
        rm_namespaces=('Template',),
        capital_links=False,
        code: str=None,
    ) -> str:
        """Return normal form of self.name.

        - Remove comments.
        - Remove language code.
        - Remove namespace ("template:" or any of `localized_namespaces`.
        - Use space instead of underscore.
        - Remove consecutive spaces.
        - Use uppercase for the first letter if `capital_links`.
        - Remove #anchor.

        :rm_namespaces: is used to provide additional localized namespaces
            for the template namespace. They will be removed from the result.
            Default is ('Template',).
        :capital_links: If True, convert the first letter of the template's
            name to a capital letter. See [[mw:Manual:$wgCapitalLinks]] for
            more info.
        :code: is the language code.

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
        if capital_links:
            # Use uppercase for the first letter
            n0 = name[0]
            if n0.islower():
                name = n0.upper() + name[1:]
        # Remove #anchor
        name, sep, tail = name.partition('#')
        return ' '.join(name.split())

    def rm_first_of_dup_args(self) -> None:
        """Eliminate duplicate arguments by removing the first occurrences.

        Remove the first occurrences of duplicate arguments, regardless of
        their value. Result of the rendered wikitext should remain the same.
        Warning: Some meaningful data may be removed from wikitext.

        Also see `rm_dup_args_safe` function.

        """
        names = set()  # type: set
        for a in reversed(self.arguments):
            name = a.name.strip(WS)
            if name in names:
                del a[:len(a.string)]
            else:
                names.add(name)

    def rm_dup_args_safe(self, tag: str=None) -> None:
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

        Also see `rm_first_of_dup_args` function.

        """
        name_to_lastarg_vals = {} \
            # type: Dict[str, Tuple[Argument, List[str]]]
        # Removing positional args affects their name. By reversing the list
        # we avoid encountering those kind of args.
        for arg in reversed(self.arguments):
            name = arg.name.strip(WS)
            if arg.positional:
                # Value of keyword arguments is automatically stripped by MW.
                val = arg.value
            else:
                # But it's not OK to strip whitespace in positional arguments.
                val = arg.value.strip(WS)
            if name in name_to_lastarg_vals:
                # This is a duplicate argument.
                if not val:
                    # This duplicate argument is empty. It's safe to remove it.
                    del arg[0:len(arg.string)]
                else:
                    # Try to remove any of the detected duplicates of this
                    # that are empty or their value equals to this one.
                    lastarg, dup_vals = name_to_lastarg_vals[name]
                    if val in dup_vals:
                        del arg[0:len(arg.string)]
                    elif '' in dup_vals:
                        # This happens only if the last occurrence of name has
                        # been an empty string; other empty values will
                        # be removed as they are seen.
                        # In other words index of the empty argument in
                        # dup_vals is always 0.
                        del lastarg[0:len(lastarg.string)]
                        dup_vals.pop(0)
                    else:
                        # It was not possible to remove any of the duplicates.
                        dup_vals.append(val)
                        if tag:
                            arg.value += tag
            else:
                name_to_lastarg_vals[name] = (arg, [val])

    def set_arg(
        self, name: str,
        value: str,
        positional: bool=None,
        before: str=None,
        after: str=None,
        preserve_spacing: bool=True
    ) -> None:
        """Set the value for `name` argument. Add it if it doesn't exist.

        Use `positional`, `before` and `after` keyword arguments only when
            adding a new argument.
        If `before` is passed, ignore `after`.
        If neither `before` nor `after` are passed and it's needed to add a new
            argument, then append the new argument to the end.
        If `positional` is passed and it's True, try to add the given value
            as a positional argument. If it's None, do as appropriate.
            Ignore `preserve_spacing` if positional is True.

        """
        args = list(reversed(self.arguments))
        arg = get_arg(name, args)
        # Updating an existing argument.
        if arg:
            if positional:
                arg.positional = positional
            if preserve_spacing:
                val = arg.value
                arg.value = val.replace(val.strip(WS), value)
            else:
                arg.value = value
            return
        # Adding a new argument
        if not name and positional is None:
            positional = True
        # Calculate the whitespace needed before arg-name and after arg-value.
        if not positional and preserve_spacing and args:
            before_names = []
            name_lengths = []
            before_values = []
            after_values = []
            for arg in args:
                aname = arg.name
                before_names.append(regex.match(r'\s*', aname)[0])
                name_lengths.append(len(aname))
                bv, av = regex.match(r'(\s*).*(\s*)$', arg.value).groups()
                before_values.append(bv)
                after_values.append(av)
            before_name = mode(before_names)
            name_length = mode(name_lengths)
            after_value = mode(
                [regex.match(r'.*?(\s*)\|', self.string)[1]] + after_values[1:]
            )
            before_value = mode(before_values)
        else:
            preserve_spacing = False
        # Calculate the string that needs to be added to the Template.
        if positional:
            # Ignore preserve_spacing for positional args.
            addstring = '|' + value
        else:
            if preserve_spacing:
                addstring = (
                    '|' + (before_name + name.strip(WS)).ljust(name_length) +
                    '=' + before_value + value + after_value
                )
            else:
                addstring = '|' + name + '=' + value
        # Place the addstring in the right position.
        if before:
            arg = get_arg(before, args)
            arg.insert(0, addstring)
        elif after:
            arg = get_arg(after, args)
            arg.insert(len(arg.string), addstring)
        else:
            if args and not positional:
                arg = args[0]
                arg_string = arg.string
                if preserve_spacing:
                    # Insert after the last argument.
                    # The addstring needs to be recalculated because we don't
                    # want to change the the whitespace before final braces.
                    arg[0:len(arg_string)] = (
                        arg.string.rstrip(WS) + after_value +
                        addstring.rstrip(WS) + after_values[0]
                    )
                else:
                    arg.insert(len(arg_string), addstring)
            else:
                # The template has no arguments or the new arg is
                # positional AND is to be added at the end of the template.
                self.insert(-2, addstring)

    def get_arg(self, name: str) -> Optional[Argument]:
        """Return the last argument with the given name.

        Return None if no argument with that name is found.

        """
        return get_arg(name, reversed(self.arguments))

    def has_arg(self, name: str, value: str=None) -> bool:
        """Return true if the is an arg named `name`.

        Also check equality of values if `value` is provided.

        Note: If you just need to get an argument and you want to LBYL, it's
            better to get_arg directly and then check if the returned value
            is None.

        """
        for arg in reversed(self.arguments):
            if arg.name.strip(WS) == name.strip(WS):
                if value:
                    if arg.positional:
                        if arg.value == value:
                            return True
                        return False
                    if arg.value.strip(WS) == value.strip(WS):
                        return True
                    return False
                return True
        return False


def mode(list_: List[T]) -> T:
    """Return the most common item in the list.

    Return the first one if there are more than one most common items.

    Example:

    >>> mode([1,1,2,2,])
    1
    >>> mode([1,2,2])
    2
    >>> mode([])
    ...
    ValueError: max() arg is an empty sequence

    """
    return max(set(list_), key=list_.count)


def get_arg(name: str, args: Iterable[Argument]) -> Optional[Argument]:
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
