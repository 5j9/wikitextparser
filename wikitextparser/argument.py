"""Define the Argument class."""


from .wikitext import SubWikiText


class Argument(SubWikiText):

    """Create a new Argument Object.

    Note that in mediawiki documentation `arguments` are (also) called
    parameters. In this module the convention is like this:
    {{{parameter}}}, {{t|argument}}.
    See https://www.mediawiki.org/wiki/Help:Templates for more information.
    """

    def __init__(self, string, spans=None, index=None, typeindex=None):
        """Initialize the object."""
        self._common_init(string, spans)
        if typeindex is None:
            self._typeindex = 'arguments'
        else:
            self._typeindex = typeindex
        if spans is None:
            self._spans[self._typeindex] = [(0, len(string))]
        if index is None:
            self._index = len(self._spans['arguments']) - 1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the Argument."""
        return 'Argument(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans[self._typeindex][self._index]

    @property
    def name(self):
        """Return argument's name.

        For positional arguments return the position as a string.

        """
        pipename, equal, value = self._not_in_atomic_subspans_partition('=')
        if equal:
            return pipename[1:]
        # positional argument
        position = 1
        godstring = self._lststr[0]
        for ss, se in self._spans[self._typeindex][:self._index]:
            if ss < se:
                equal_index = godstring.find('=', ss, se)
                if equal_index == -1:
                    position += 1
                else:
                    in_subspans = self._in_atomic_subspans_factory(ss, se)
                    while equal_index != -1:
                        if not in_subspans(equal_index):
                            # This is a keyword argument
                            break
                        # We don't care for this kind of equal sign.
                        # Look for the next one.
                        equal_index = godstring.find('=', equal_index + 1, se)
                    else:
                        # All the equal signs where inside a subspan.
                        position += 1
        return str(position)

    @name.setter
    def name(self, newname):
        """Set the name for this argument.

        If this is a positional argument, convert it to keyword argument.

        """
        oldname = self.name
        if self.positional:
            self.replace_slice(0, 1, '|' + newname + '=')
        else:
            self.replace_slice(1, 1 + len(oldname), newname)

    @property
    def positional(self):
        """Return True if there is an equal sign in the argument else False."""
        if self._not_in_atomic_subspans_partition('=')[1]:
            return False
        else:
            return True

    @positional.setter
    def positional(self, to_positional):
        """Change to keyword or positional accordingly.

        Raise ValueError if setting positional argument to keyword argument.

        """
        pipename, equal, value = self._not_in_atomic_subspans_partition('=')
        if equal:
            # Keyword argument
            if to_positional:
                self.strdel(1, len(pipename + '='))
            else:
                return
        elif to_positional:
            # Positional argument. to_positional is True.
            return
        else:
            # Positional argument. to_positional is False.
            raise ValueError(
                'Converting positional argument to keyword argument is not '
                'possible without knowing the new name. '
                'You can use `self.name = somename` instead.'
            )

    @property
    def value(self):
        """Return value of a keyword argument."""
        pipename, equal, value = self._not_in_atomic_subspans_partition('=')
        if equal:
            return value
        # Anonymous parameter
        return pipename[1:]

    @value.setter
    def value(self, newvalue):
        """Assign the newvalue to self."""
        pipename, equal, value = self._not_in_atomic_subspans_partition('=')
        if equal:
            pnel = len(pipename + equal)
            self.replace_slice(pnel, pnel + len(value), newvalue)
        else:
            self.replace_slice(1, len(pipename), newvalue)
