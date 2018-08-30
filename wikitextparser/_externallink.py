"""Define the ExternalLink class."""

from typing import Optional

from regex import compile as regex_compile

from ._wikitext import SubWikiText, BRACKET_EXTERNAL_LINK_URL


URL_MATCH = regex_compile(BRACKET_EXTERNAL_LINK_URL).match


class ExternalLink(SubWikiText):

    """Create a new ExternalLink object."""

    @property
    def url(self) -> str:
        """Return the url."""
        if self[0] == '[':
            return self[1:URL_MATCH(self._ext_link_shadow, 1).end()]
        return self.string

    @url.setter
    def url(self, newurl: str) -> None:
        """Set a new url."""
        if self[0] == '[':
            self[1:len('[' + self.url)] = newurl
        else:
            self[0:len(self.url)] = newurl

    @property
    def text(self) -> Optional[str]:
        """Return the text part (the part after the first space).

        Return None if this is a bare link or has no associated text.
        """
        string = self.string
        if string[0] == '[':
            end_match = URL_MATCH(self._ext_link_shadow, 1)
            url_end = end_match.end()
            end_char = string[url_end]
            if end_char == ']':
                return None
            if end_char == ' ':
                return string[url_end + 1:-1]
            return string[url_end:-1]

    @text.setter
    def text(self, newtext: str) -> None:
        """Set a new text.

        Automatically put the ExternalLink in brackets if it's not already.
        """
        string = self.string
        if string[0] == '[':
            text = self.text
            if text:
                self[-len(text) - 1:-1] = newtext
                return
            self.insert(-1, ' ' + newtext)
            return
        self.insert(len(string), ' ' + newtext + ']')
        self.insert(0, '[')

    @property
    def in_brackets(self) -> bool:
        """Return true if the ExternalLink is in brackets. False otherwise."""
        return self[0] == '['
