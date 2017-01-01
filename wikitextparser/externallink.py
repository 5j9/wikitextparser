"""Define the ExternalLink class."""


from .wikitext import SubWikiText


class ExternalLink(SubWikiText):

    """Create a new ExternalLink object."""

    @property
    def url(self) -> str:
        """Return the url part of the ExternalLink."""
        if self.in_brackets:
            return self.string[1:-1].partition(' ')[0]
        return self.string

    @url.setter
    def url(self, newurl: str) -> None:
        """Set a new url for the current ExternalLink."""
        if self.in_brackets:
            bracket_url, space, text_bracket = self[:].partition(b' ')
            if space:
                self[1:len(bracket_url)] = newurl.encode()
                return
            self[1:-1] = newurl.encode()
            return
        # self is a bare URL
        self[:] = newurl.encode()

    @property
    def text(self) -> str:
        """Return the display text of the external link.

        Return self.string if this is a bare link.
        Return
        """
        if self.in_brackets:
            return self.string[1:-1].partition(' ')[2]
        return self.string

    @text.setter
    def text(self, newtext: str) -> None:
        """Set a new text for the current ExternalLink.

        Automatically puts the ExternalLink in brackets if it's not already.
        """
        if not self.in_brackets:
            # It's OK to overwrite pure URLs
            self[:] = b'[' + self[:] + b' ' + newtext.encode() + b']'
            return
        url, space, text = self[:].partition(b' ')
        if text:
            self[len(url) + 1:-1] = newtext.encode()
            return
        # In brackets, with no text
        self.insert(-1, newtext.encode())

    @property
    def in_brackets(self) -> bool:
        """Return true if the ExternalLink is in brackets. False otherwise."""
        s = self._span[0]
        return self._bytearray[s] == 91  # ord('[')
