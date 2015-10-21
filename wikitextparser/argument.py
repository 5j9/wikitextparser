"""The Argument class."""


class Argument():

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
            self._index = len(self._spans['arguments']) -1
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
        pipename, equal, value = self._not_in_subspans_partition('=')
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
                    in_subspans = self._in_subspans_factory(ss, se)
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

        If this is a positional agument, convert it to keyword argument.
        """
        oldname = self.name
        if self.positional:
            self.strins(0, '|' + newname + '=')
            self.strdel(
                len('|' + newname + '='), len('|' + newname + '=|')
            )
        else:
            self.strins(0, '|' + newname)
            self.strdel(len('|' + newname), len('|' + newname + '|' + oldname))

    @property
    def positional(self):
        """Return True if there is an equal sign in the argument. Else False."""
        if self._not_in_subspans_partition('=')[1]:
            return False
        else:
            return True

    @property
    def value(self):
        """Return value of a keyword argument."""
        pipename, equal, value = self._not_in_subspans_partition('=')
        if equal:
            return value
        # Anonymous parameter
        return pipename[1:]

    @value.setter
    def value(self, newvalue):
        """Set a the value for the current argument."""
        pipename, equal, value = self._not_in_subspans_partition('=')
        if equal:
            self.strins(len(pipename + equal), newvalue)
            self.strdel(
                len(pipename + equal + newvalue),
                len(pipename + equal + newvalue + value)
            )
        else:
            self.strins(1, newvalue)
            self.strdel(
                len('|' + newvalue),
                len('|' + newvalue + pipename[1:])
            )
            
