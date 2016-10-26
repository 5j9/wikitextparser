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
        spans: list or None=None,
        index: int or None=None,
    ) -> None:
        """Initialize the object."""
        self._common_init(string, spans)
        if index is None:
            self._index = len(self._type_to_spans['templates']) - 1
        else:
            self._index = index

    def __repr__(self) -> str:
        """Return the string representation of the Template."""
        return 'Template(' + repr(self.string) + ')'

    def _get_span(self) -> tuple:
        """Return the self-span."""
        return self._type_to_spans['templates'][self._index]

    @property
    def arguments(self) -> list:
        """Parse template content. Create self.name and self.arguments."""
        barsplits = self._not_in_atomic_subspans_split_spans('|')[1:]
        arguments = []
        spans = self._type_to_spans
        lststr = self._lststr
        typeindex = 'ta' + str(self._index)
        if typeindex not in spans:
            spans[typeindex] = []
        aspans = spans[typeindex]
        if barsplits:
            # remove the final '}}' from the last argument.
            barsplits[-1] = (barsplits[-1][0], barsplits[-1][1] - 2)
            for aspan in barsplits:
                # include the the starting '|'
                aspan = (aspan[0] + -1, aspan[1])
                if aspan not in aspans:
                    aspans.append(aspan)
                arguments.append(
                    Argument(
                        lststr,
                        spans,
                        aspans.index(aspan),
                        typeindex,
                    )
                )
        return arguments

    @property
    def name(self) -> str:
        """Return template's name (includes whitespace)."""
        p0 = self._not_in_atomic_subspans_partition('|')[0]
        if len(p0) == len(self.string):
            return p0[2:-2]
        else:
            return p0[2:]

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

        Remove the duplicate arguments only if:
        1. Both arguments have the same name AND value.
        2. Arguments have the same name and one of them is empty. (Remove the
            empty one.)

        Warning: Although this is considered to be safe as no meaningful data
            is removed but the result of the renedered wikitext may actually
            change if the second arg is empty and removed but the first has a
            value.

        If `tag` is defined, it should be a string, tag the remaining
        arguments by appending the provided tag to their value.

        Also see `rm_first_of_dup_args` function.

        """
        name_args_vals = {}
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
            if name in name_args_vals:
                # This is a duplicate argument.
                if not val:
                    # This duplicate argument is empty. It's safe to remove it.
                    del arg[0:len(arg.string)]
                else:
                    # Try to remove any of the detected duplicates of this
                    # that are empty or their value equals to this one.
                    name_args = name_args_vals[name][0]
                    name_vals = name_args_vals[name][1]
                    if val in name_vals:
                        del arg[0:len(arg.string)]
                    elif '' in name_vals:
                        i = name_vals.index('')
                        a = name_args.pop(i)
                        del a[0:len(a.string)]
                        name_vals.pop(i)
                    else:
                        # It was not possible to remove any of the duplicates.
                        name_vals.append(arg)
                        name_vals.append(val)
                        if tag:
                            arg.value += tag
            else:
                name_args_vals[name] = ([arg], [val])

    def set_arg(
        self, name: str,
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
        if positional is None and not name:
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
                # Insert after the last argument.
                # The addstring needs to be recalculated because we don't
                # want to change the the whitespace before the final braces.
                arg = args[0]
                arg_string = arg.string
                arg[0:len(arg_string)] = (
                    arg.string.rstrip() + after_value + addstring.rstrip() +
                    after_values[0]
                )
            else:
                # The template has no arguments or the new arg is
                # positional AND is to be added at the end of the template.
                self.insert(-2, addstring)

    def get_arg(self, name: str) -> Argument or None:
        """Return the last argument with the given name.

        Return None if no such argument is found.

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
