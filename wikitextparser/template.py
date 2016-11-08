""""Define the Template class."""


import re

from .wikitext import SubWikiText
from .argument import Argument
from .spans import COMMENT_REGEX


class Template(SubWikiText):

    """Convert strings to Template objects.

    The string should start with {{ and end with }}.

    """

    def __init__(
        self,
        string: str or list,
        type_to_spans: list or None=None,
        index: int or None=None,
    ) -> None:
        """Initialize the object."""
        self._common_init(string, type_to_spans)
        self._index = len(
            self._type_to_spans['templates']
        ) - 1 if index is None else index

    def __repr__(self) -> str:
        """Return the string representation of the Template."""
        return 'Template(' + repr(self.string) + ')'

    @property
    def _span(self) -> tuple:
        """Return the self-span."""
        return self._type_to_spans['templates'][self._index]

    @property
    def arguments(self) -> list:
        """Parse template content. Create self.name and self.arguments."""
        bar_spans = self._not_in_atomic_subspans_split_spans('|')[1:]
        arguments = []
        type_to_spans = self._type_to_spans
        lststr = self._lststr
        type_ = 'ta' + str(self._index)
        if type_ not in type_to_spans:
            type_to_spans[type_] = []
        arg_spans = type_to_spans[type_]
        if bar_spans:
            # remove the final '}}' from the last argument.
            bar_spans[-1] = (bar_spans[-1][0], bar_spans[-1][1] - 2)
            for bar_span in bar_spans:
                # include the the starting '|'
                bar_span = (bar_span[0] + -1, bar_span[1])
                index = next(
                    (i for i, s in enumerate(arg_spans) if s == bar_span),
                    None
                )
                if index is None:
                    index = len(arg_spans)
                    arg_spans.append(bar_span)
                arguments.append(Argument(lststr, type_to_spans, index, type_))
        return arguments

    @property
    def name(self) -> str:
        """Return template's name (includes whitespace)."""
        h = self._not_in_atomic_subspans_partition('|')[0]
        if len(h) == len(self.string):
            return h[2:-2]
        else:
            return h[2:]

    @name.setter
    def name(self, newname: str) -> None:
        """Set the new name for the template."""
        name = self.name
        self[2:2 + len(name)] = newname

    def normal_name(
        self,
        rm_namespaces=('Template',),
        code: str or None=None,
    ) -> str:
        """Return normal form of the name.

        # Remove comments.
        # Remove language code.
        # Remove namespace ("template:" or any of `localized_namespaces`.
        # Use space instead of underscore.
        # Remove consecutive spaces.
        # Use uppercase for the first letter.
        # Remove #anchor.

        :rm_namespaces: is used to provide additional localized namespaces
            for the template namespace. They will be removed from the result.
            Default is ('Template',).
        :code: is the language code.

        Example:
            >>> Template(
            ...     '{{ eN : tEmPlAtE : <!-- c --> t_1 # b | a }}'
            ... ).normal_name(code='en')
            'T 1'

        """
        # Remove comments
        name = COMMENT_REGEX.sub('', self.name).strip()
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
        # Use uppercase for the first letter
        n0 = name[0]
        if n0.islower():
            name = n0.upper() + name[1:]
        # Remove #anchor
        name, sep, tail = name.partition('#')
        return ' '.join(name.split())

    def rm_first_of_dup_args(self) -> None:
        """Eliminate duplicate arguments by removing the first occurrences.

        Remove first occurrences of duplicate arguments-- no matter what their
        value is. Result of the rendered wikitext should remain the same.
        Warning: Some meaningful data may be removed from wikitext.

        Also see `rm_dup_args_safe` function.

        """
        names = []
        for a in reversed(self.arguments):
            name = a.name.strip()
            if name in names:
                del a[0:len(a.string)]
            else:
                names.append(name)

    def rm_dup_args_safe(self, tag: str or None=None) -> None:
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
        name_to_lastarg_vals = {}
        # Removing positional args affects their name. By reversing the list
        # we avoid encountering those kind of args.
        for arg in reversed(self.arguments):
            name = arg.name.strip()
            if arg.positional:
                # Value of keyword arguments is automatically stripped by MW.
                val = arg.value
            else:
                # But it's not OK to strip whitespace in positional arguments.
                val = arg.value.strip()
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
        self, name: str or None,
        value: str,
        positional: bool or None=None,
        before: str or None=None,
        after: str or None=None,
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
                arg.value = val.replace(val.strip(), value)
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
                before_names.append(re.match(r'\s*', aname).group())
                name_lengths.append(len(aname))
                bv, av = re.match(r'(\s*).*(\s*)$', arg.value).groups()
                before_values.append(bv)
                after_values.append(av)
            before_name = mode(before_names)
            name_length = mode(name_lengths)
            after_value = mode(
                [re.match(r'.*?(\s*)\|', self.string).group(1)] +
                after_values[1:]
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
                    '|' + (before_name + name.strip()).ljust(name_length) +
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
                    # want to change the the whitespace before the final braces.
                    arg[0:len(arg_string)] = (
                        arg.string.rstrip() + after_value + addstring.rstrip() +
                        after_values[0]
                    )
                else:
                    arg.insert(len(arg_string), addstring)
            else:
                # The template has no arguments or the new arg is
                # positional AND is to be added at the end of the template.
                self.insert(-2, addstring)

    def get_arg(self, name: str) -> Argument or None:
        """Return the last argument with the given name.

        Return None if no argument with that name is found.

        """
        return get_arg(name, reversed(self.arguments))

    def has_arg(self, name: str, value: str or None=None) -> bool:
        """Return true if the is an arg named `name`.

        Also check equality of values if `value` is provided.

        Note: If you just need to get an argument and you want to LBYL, it's
            better to get_arg directly and then check if the returned value
            is None.

        """
        for arg in reversed(self.arguments):
            if arg.name.strip() == name.strip():
                if value:
                    if arg.positional:
                        if arg.value == value:
                            return True
                        else:
                            return False
                    else:
                        if arg.value.strip() == value.strip():
                            return True
                        else:
                            return False
                else:
                    return True
        return False


def mode(list_: list):
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


def get_arg(name: str, args) -> Argument or None:
    """Return the first argument in the args that has the given name.

    Return None if no such argument is found.

    As the computation of self.arguments is a little costly, this
    function was created so that other methods that have already computed
    the arguments use it instead of calling self.get_arg directly.

    """
    for arg in args:
        if arg.name.strip() == name.strip():
            return arg
