"""Define the Tag class."""


# HTML elements all have names that only use alphanumeric ASCII characters
# https://www.w3.org/TR/html5/syntax.html#syntax-tag-name
TAGNAME = r'(?P<tagname>[A-Za-z0-9]+)'
# https://www.w3.org/TR/html5/infrastructure.html#space-character
SPACE_CHARACTERS = r' \t\n\u000C\r'
# http://stackoverflow.com/a/93029/2705757
# chrs = (chr(i) for i in range(sys.maxunicode))
# control_chars = ''.join(c for c in chrs if unicodedata.category(c) == 'Cc')
CONTROL_CHARACTERS = r'\x00-\x1f\x7f-\x9f'
# https://www.w3.org/TR/html5/syntax.html#syntax-attributes
ATTRNAME = (
    r'(?P<attrname>[^' + SPACE_CHARACTERS + CONTROL_CHARACTERS +
    r'\u0000"\'>/=])'
)
# Ignore ambiguous ampersand for the sake of simplicity.
UNQUOTED_ATTRIBUTE_VALUE = r'([' + SPACE_CHARACTERS + ']*)'
ATTR = r'(?P<attr> +)'
STARTTAG = r'(?P<start><' + TAGNAME + r')'

ATTRIBUTE_VALUES =

import re
re.sub()

class ExternalLink():

    """Create a new ExternalLink object."""

    def __init__(self, string, spans=None, index=None):
        """Run self._common_init. Set self._spans['extlinks'] if spans is None."""
        self._common_init(string, spans)
        if spans is None:
            self._spans['extlinks'] = [(0, len(string))]
        if index is None:
            self._index = len(self._spans['extlinks']) - 1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the ExternalLink."""
        return 'ExternalLink(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['extlinks'][self._index]

    @property
    def url(self):
        """Return the url part of the ExternalLink."""
        if self.in_brackets:
            return self.string[1:-1].partition(' ')[0]
        return self.string

    @url.setter
    def url(self, newurl):
        """Set a new url for the current ExternalLink."""
        if self.in_brackets:
            url = self.url
            self.replace_slice(1, len('[' + url), newurl)
        else:
            url = self.url
            self.replace_slice(0, len(url), newurl)

    @property
    def text(self):
        """Return the display text of the external link.

        Return self.string if this is a bare link.
        Return
        """
        if self.in_brackets:
            return self.string[1:-1].partition(' ')[2]
        return self.string

    @text.setter
    def text(self, newtext):
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
    def in_brackets(self):
        """Return true if the ExternalLink is in brackets. False otherwise."""
        return self.string.startswith('[')
