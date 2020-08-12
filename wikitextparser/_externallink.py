"""Define the ExternalLink class."""

from typing import List, Optional

from regex import compile as regex_compile

from ._wikitext import BRACKET_EXTERNAL_LINK_URL, SubWikiText

URL_MATCH = regex_compile(BRACKET_EXTERNAL_LINK_URL).match


class ExternalLink(SubWikiText):

    __slots__ = ()

    @property
    def url(self) -> str:
        """URL of the current ExternalLink object.

        getter: Return the URL.
        setter: Set a new value for URL. Convert add brackets for bare
            external links.
        """
        if self(0) == '[':
            return self(1, URL_MATCH(self._ext_link_shadow, 1).end())
        return self.string

    @url.setter
    def url(self, newurl: str) -> None:
        if self(0) == '[':
            self[1:len('[' + self.url)] = newurl
        else:
            self[0:len(self.url)] = newurl

    @property
    def text(self) -> Optional[str]:
        """The text part (the part after the first space).

        getter: Return None if this is a bare link or has no associated text.
        setter: Automatically put the ExternalLink in brackets if it's not
            already.
        deleter: Delete self.text, including the space before it.
        """
        string = self.string
        if string[0] == '[':
            url_end = URL_MATCH(self._ext_link_shadow, 1).end()
            end_char = string[url_end]
            if end_char == ']':
                return None
            if end_char == ' ':
                return string[url_end + 1:-1]
            return string[url_end:-1]

    @text.setter
    def text(self, newtext: str) -> None:
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

    @text.deleter
    def text(self) -> None:
        string = self.string
        if string[0] != '[':
            return
        text = self.text
        if text:
            del self[-len(text) - 2:-1]

    @property
    def in_brackets(self) -> bool:
        """Return true if the ExternalLink is in brackets. False otherwise."""
        return self(0) == '['

    @property
    def external_links(self) -> List['ExternalLink']:
        return []
