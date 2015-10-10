"""Define a class to deal with tables."""

import re


ROWSEP_REGEX = re.compile(r'(?:(?<=\n)|^)\s*[\|!]-.*?\n')
CELLSEP_REGEX = re.compile(
    r'(?:\s*[\|!][^|\n]*?[\|!](?![\|!]) *|(?:(?<=\n)|^)\s*[\|!] *)'
)
CAPTION_REGEX = re.compile(r'\|\+.*?\n')


class Table:

    """Create a new Table object."""

    def __init__(self, string, spans=None, index=None):
        """Run _common_init. Set self._spans['tables'] if spans is None."""
        self._common_init(string, spans)
        if spans is None:
            self._spans['tables'] = [(0, len(string))]
        if index is None:
            self._index = len(self._spans['tables']) - 1
        else:
            self._index = index

    def __repr__(self):
        """Return the string representation of the Table."""
        return 'Table(' + repr(self.string) + ')'

    def _get_span(self):
        """Return the self-span."""
        return self._spans['tables'][self._index]

    @property
    def rows(self):
        """Return a tuple containing all rows.

        Due to the lots of complications it will cause, this function
        won't look inside templates, parserfunction, etc.

        See https://www.mediawiki.org/wiki/Extension:Pipe_Escape for how
        wikitables can be inserted within templates.
        """
        rawstring = self.string
        ss, se = self._get_span()
        for type_ in (
            'templates', 'wikilinks', 'functions',
            'exttags', 'comments'
        ):
            for sss, sse in self._gen_subspan_indices(type_):
                rawstring = (
                    rawstring[:sss - ss] +
                    (sss - sse) * '_' +
                    rawstring[sse - ss:]
                )
        # Remove table-start and table-end marks.
        rawstring = rawstring[:-2].partition('\n')[2].strip()
        # Remove table caption.
        # Captions are optional and can only be placed
        # between table-start and the first row.
        while rawstring.startswith('|+'):
            rawstring = rawstring.partition('\n')[2].lstrip()
        print('rawstring:', rawstring)
        rawrows = ROWSEP_REGEX.split(rawstring)
        if not rawrows[0].rstrip():
            # When optional `|-` is used on first row.
            rawrows.pop(0)
        rows = []
        for row in rawrows:
            print('row:', row)
            cells = []
            for cell in CELLSEP_REGEX.split(row)[1:]:
                # Spaces can be meaningful after the first newline
                cells.append(cell.strip(' ').rstrip())
            print('cells:', cells)
            rows.append(cells)
        return rows

    def getrow(self, n):
        """Return the nth row of the Table."""
        return self.rows[n]

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
        self.strins(len('[' + url + ' '), newtext)
        self.strdel(
            len('[' + url + ' ' + newtext),
            len('[' + url + ' ' + newtext + text),
        )

    @property
    def in_brackets(self):
        """Return true if the ExternalLink is in brackets. False otherwise."""
        return self.string.startswith('[')
    
