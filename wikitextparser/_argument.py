"""Define the Argument class."""


from ._wikitext import SubWikiText
from ._spans import parse_to_spans


class Argument(SubWikiText):

    """Create a new Argument Object.

    Note that in mediawiki documentation `arguments` are (also) called
    parameters. In this module the convention is like this:
    {{{parameter}}}, {{t|argument}}.
    See https://www.mediawiki.org/wiki/Help:Templates for more information.
    """

    @property
    def name(self) -> str:
        """Return argument's name.

        For positional arguments return the position as a string.
        """
        pipename, equal, value = self._atomic_partition(61)
        if equal:
            return pipename[1:]
        # positional argument
        position = 1
        lststr0 = self._lststr[0]
        ss = self._span[0]
        # Todo: if we had the index of self._span, we could only look-up
        # the head of the self._type_to_spans.
        for s, e in self._type_to_spans[self._type]:
            if ss <= s:
                break
            arg_str = lststr0[s:e]
            if '=' in arg_str:
                # The argument may is still be positional if the equal sign is
                # inside an atomic sub-spans.
                byte_array = bytearray(arg_str, 'ascii', 'replace')
                parse_to_spans(byte_array)  # Remove sub-spans from byte_array
                if b'=' in byte_array:
                    # This is a keyword argument.
                    continue
            # This is a preceding positional argument.
            position += 1
        return str(position)

    @name.setter
    def name(self, newname: str) -> None:
        """Set the name for this argument.

        If this is a positional argument, convert it to keyword argument.
        """
        oldname = self.name
        if self.positional:
            self[0:1] = '|' + newname + '='
        else:
            self[1:1 + len(oldname)] = newname

    @property
    def positional(self) -> bool:
        """Return True if there is an equal sign in the argument else False."""
        if self._atomic_partition(61)[1]:
            return False
        return True

    @positional.setter
    def positional(self, to_positional: bool) -> None:
        """Change to keyword or positional accordingly.

        Raise ValueError if setting positional argument to keyword argument.
        """
        pipename, equal, value = self._atomic_partition(61)
        if equal:
            # Keyword argument
            if to_positional:
                del self[1:len(pipename + '=')]
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
        """Return value of a keyword argument."""
        pipename, equal, value = self._atomic_partition(61)
        if equal:
            return value
        # Anonymous parameter
        return pipename[1:]

    @value.setter
    def value(self, newvalue: str) -> None:
        """Assign the newvalue to self."""
        pipename, equal, value = self._atomic_partition(61)
        if equal:
            pnel = len(pipename + '=')
            self[pnel:pnel + len(value)] = newvalue
        else:
            self[1:len(pipename)] = newvalue
