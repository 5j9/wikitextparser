"""Define a class to deal with tables."""

import re


ROWSEP_REGEX = re.compile(r'(?:(?<=\n)|^)\s*[\|!]-.*?\n')
CELLSEP_REGEX = re.compile(
    r'\s*[|!][^|\n]*?\|(?!\|) *|(?:(?<=\n)|^)\s*[|!] *'
    #r'\s*([|!]{2}|[|!](?:[^|\n]*\|)?)\s*'
)
START_CELLSEP_REGEX = re.compile(r"""
(?:(?<=\n)|^) # catch the starting sep. and style
\s*
(?P<sep>[|!])
(?: # catch the matching pipe (style holder).
\| # immediate closure (style='')
|
(?P<style>.*?)
(?<!\|) # double-pipes are cell seperators
(?:\|)
(?!\|) # double-pipes are cell seperators
)? # optional := the 1st sep is a single ! or |.
""", re.VERBOSE
)
                                 
CELL_REGEX = re.compile(
    r'(?:(?<=\n)|^)\s*[|!]{1,2}(.*?)(?:\|\|(.*?))*$|',
    re.DOTALL,
)    
CAPTION_REGEX = re.compile(r'(?<=(?<=\n)|^)\s*(?:\|\+[\s\S]*?)+(?=\||\!)')
EVERYTHING_UNTIL_THE_FIRST_ROW_REGEX = re.compile(
    r'.*?(?=' + CELLSEP_REGEX.pattern + r')'
)
EE = re.compile(r'!!')
E = re.compile(r'!')
VV = re.compile(r'||')
V = re.compile(r'|')



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
        string = self.string
        length = len(string)
        shadow = string
        ss, se = self._get_span()
        for type_ in (
            'templates', 'wikilinks', 'functions',
            'exttags', 'comments'
        ):
            for sss, sse in self._spans[type_]:
                if sss < ss or sse > se:
                    continue
                shadow = (
                    shadow[:sss - ss] +
                    (sse - sss) * '_' +
                    shadow[sse - ss:]
                )
        # Remove table-start and table-end marks.
        shadow = shadow[:-2].partition('\n')[2].lstrip()
        # Remove everything until the first row
        while not (shadow.startswith('!') or shadow.startswith('|')):
            shadow = shadow.partition('\n')[2].lstrip()
            if '\n' not in shadow:
                break
        string = string[length - len(shadow) - 2:-2]
        # Remove table captions.
        # Captions are optional and should only be placed
        # between table-start and the first row; Others are not part of table.
        for m in CAPTION_REGEX.finditer(shadow):
            ss, se = m.span()
            shadow = shadow[:ss] + shadow[se:]
            string = string[:ss] + string[se:]
        rowspans = [[0]]
        for m in ROWSEP_REGEX.finditer(shadow):
            rowspans[-1].append(m.start())
            rowspans.append([m.end()])
        rowspans[-1].append(-1)
        grouped_spans = []
        for ss, se in rowspans:
            tail = shadow[rss:rse]
            tail = tail.lstrip()
            if not tail:
                # Todo: this condition may be removed alltogether in the future
                # When the optional `|-` for the first row is used or when 
                # there are meaningless row seprators that result in rows
                # containing no cells.
                continue
            len0 = se - ss + 1
            tdspans = []
            if tail.startswith('||'):
                # Cells in this type of rows can only be seperated using `||`.
                head, sep, tail = tail.partition('||')
                while sep:
                    head, sep, tail = tail.partition('||')
                    tdspans.append(
                        ss + len0 - len(head + sep + tail),
                        ss + len0 - len(sep + tail),
                    )
            elif tail.startswith('!!'):
                rowtail = rowtail[2:]
                
                while True:
                    td, s, rowtail = rowtail.partition('||')
                    if not s:
                        break
                    cellspans.append(td)
            cellspans = [[0]]
            for m in CELLSEP_REGEX.finditer(shadow[ss:se]):
                cellspans[-1].append(ss + m.start())
                cellspans.append([ss + m.end()])
            cellspans[-1].append(se)
            grouped_cellspans.append(cellspans)
        grouped_cellspans
        rows = []
        for g in grouped_cellspans:
            # The first CELLSEP is always at the beginning of the string.
            g.pop(0)
            rows.append([])
            for ss, se in g:
                # Spaces after the first newline can be meaningful
                rows[-1].append(string[ss:se].strip(' ').rstrip())
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
    
