"""Define the ExternalLink class."""


from .wikitext import SubWikiText


class ExternalLink(SubWikiText):

    """Create a new ExternalLink object."""

    def __init__(
        self,
        string: str or list,
        spans: list or None=None,
        index: int or None=None,
    ) -> None:
        """Run _common_init. Set _type_to_spans['extlinks'] if not spans."""
        self._common_init(string, spans)
        if spans is None:
            self._type_to_spans['extlinks'] = [(0, len(string))]
        if index is None:
            self._index = len(self._type_to_spans['extlinks']) - 1
        else:
            self._index = index

    def __repr__(self) -> str:
        """Return the string representation of the ExternalLink."""
        return 'ExternalLink(' + repr(self.string) + ')'

    def _get_span(self) -> tuple:
        """Return the self-span."""
        return self._type_to_spans['extlinks'][self._index]

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
            url = self.url
            self.replace_slice(1, len('[' + url), newurl)
        else:
            url = self.url
            self.replace_slice(0, len(url), newurl)

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
            url = self.string
            self.strins(len(url), ' ]')
            self.strins(0, '[')
            text = ''
        else:
            url = self.url
            text = self.text
        self.replace_slice(
            len('[' + url + ' '),
            len('[' + url + ' ' + text),
            newtext,
        )

    @property
    def in_brackets(self) -> bool:
        """Return true if the ExternalLink is in brackets. False otherwise."""
        return self.string.startswith('[')
