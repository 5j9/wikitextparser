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
            self._typeindex = 'a'
        else:
            self._typeindex = typeindex
        if spans is None:
            self._spans[self._typeindex] = [(0, len(string))]
        if index is None:
            self._index = len(self._spans['a']) -1
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
        """Return arg's name-part. Return the position for positional args."""
        pipename, equal, value = self._not_in_subspans_partition('=')
        if equal:
            return pipename[1:]
        # positional argument
        position = 1
        godstring = self._lststr[0]
        for span0, span1 in self._spans[self._typeindex][:self._index]:
            if span0 < span1 and '=' not in godstring[span0:span1]:
                position += 1
        return str(position)

    @name.setter
    def name(self, newname):
        """Changes the name of the argument."""
        name = self.name
        self.strins(1, newname)
        self.strdel(len('|' + newname), len('|' + name + newname))

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
        # anonymous parameters
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
            
