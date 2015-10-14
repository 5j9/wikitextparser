"""Define a class to deal with tables."""

import re


ROWSEP_REGEX = re.compile(r'^\s*[\|!]-.*?\n', re.M)
# https://regex101.com/r/hB4dX2/16
NEWLINE_CELL_REGEX = re.compile(
    r"""
    # only for matching, not searching
    \s*
    (?P<sep>[|!])
    (?:
      # catch the matching pipe (style holder).
      \| # immediate closure (attrs='').
      |
      (?P<attrs>
        (?:
          [^|\n] # attrs can't contain |
          (?!(?P=sep){2})
          # also not !! if sep is !
        )*?
      )
      (?:\|)
      (?!\|)
      # not cell seperator: ||
    )?
    # optional := the 1st sep is a single ! or |.
    (?P<data>[\s\S]*?)
    (?=
      # start of the next cell
      \|\||
      (?P=sep){2}|
      $|
      \n\s*[!|]
    )
    """,
    re.VERBOSE
)
# https://regex101.com/r/qK1pJ8/5
INLINE_HAEDER_CELL_REGEX = re.compile(
    r"""
    [|!]{2}
    (?:
      # catch the matching pipe (style holder).
      \| # immediate closure (attrs='').
      |
      (?P<attrs>
        (?:
          [^|\n] # attrs can't contain |
          (?!\!\!)
          # also not !! if sep is !
        )*?
      )
      (?:\|)
      (?!\|)
      # not cell seperator: ||
    )?
    # optional := the 1st sep is a single ! or |.
    (?P<data>[\s\S]*?)
    (?=
      # start of the next cell
      \|\||
      \!\!|
      $|
      \n\s*[!|]
    )
    """,
    re.VERBOSE
)
# https://regex101.com/r/hW8aZ3/7
INLINE_NONHAEDER_CELL_REGEX = re.compile(
    r"""
    \|\| # catch the matching pipe (style holder).
    (?:
      # immediate closure (attrs='').
      \||
      (?P<attrs>
        [^|\n]*? # attrs can't contain |
      )
      (?:\|)
      # not cell seperator: ||
      (?!\|)
    )
    # optional := the 1st sep is a single ! or |.
    ?
    (?P<data>[\s\S]*?)
    # start of the next cell
    (?=\|\||$|\n\s*[!|])
    """,
    re.VERBOSE
)
# Captions are optional and should only be placed
# between table-start and the first row. Others captions not part of table.
# The semi-captions regex below will match these invalid captions, too.
SEMICAPTION_REGEX = re.compile(
    r"""
    ^\s*
    (?:\|\+[\s\S]*?)+
    (?=^\s*[|!])
    """,
    re.MULTILINE|re.VERBOSE
)
# https://regex101.com/r/tH3pU3/6
CAPTION_REGEX = re.compile(
    r"""
    # Everything until the caption line
    (?P<preattrs>
      # Start of table
      {\|
      (?:
        (?:
          (?!\n\s*\|)
          [\s\S]
        )*?
      )
      # Start of caption line
      \n\s*\|\+
    )
    # Optional capation attrs
    (?:
      (?P<attrs>[^\n|]*)
      (?:\|)
      (?!\|)
    )?
    (?P<caption>.*?)
    # End of caption line
    (?:\n|\|\|)
    """,
    re.VERBOSE
)


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
        """Return a tuple containing value of all rows.

        Due to the lots of complications it will cause, this function
        won't look inside templates, parserfunction, etc.

        See https://www.mediawiki.org/wiki/Extension:Pipe_Escape for how
        wikitables can be inserted within templates.

        Todo: Do something about rowspans and colspans.
        """
        string = self.string
        length = len(string)
        shadow = self._shadow()
        # Remove table-start and table-end marks.
        shadow = shadow[:-2].partition('\n')[2].lstrip()
        # Remove everything until the first row
        while not (shadow.startswith('!') or shadow.startswith('|')):
            shadow = shadow.partition('\n')[2].lstrip()
            if '\n' not in shadow:
                break
        string = string[length - len(shadow) - 2:-2]
        # Remove all semi-captions.
        ss, se = self._get_span()
        m = SEMICAPTION_REGEX.search(shadow)
        while m:
            ss, se = m.span()
            shadow = shadow[:ss] + shadow[se:]
            string = string[:ss] + string[se:]
            m = SEMICAPTION_REGEX.search(shadow)
        rowspans = [[0]]
        for m in ROWSEP_REGEX.finditer(shadow):
            rowspans[-1].append(m.start())
            rowspans.append([m.end()])
        rowspans[-1].append(-1)
        grouped_spans = []
        for ss, se in rowspans:
            row = shadow[ss:se]
            if not row.lstrip():
                # When the optional `|-` for the first row is used or when 
                # there are meaningless row seprators that result in rows
                # containing no cells.
                continue
            grouped_spans.append([])
            endpos = ss - se
            pos = 0
            lastpos = -1
            while pos != lastpos:
                lastpos = pos
                sep = None
                m = NEWLINE_CELL_REGEX.match(row, pos)
                if m:
                    sep = m.group('sep')
                    data = m.group('data')
                    grouped_spans[-1].append(
                        (ss + m.end() - len(data), ss + m.end())
                    )
                    pos = m.end()
                    if sep == '|':
                        m = INLINE_NONHAEDER_CELL_REGEX.match(row, pos)
                        while m:
                            data = m.group('data')
                            grouped_spans[-1].append(
                                (ss + m.end() - len(data), ss + m.end())
                            )
                            pos = m.end()
                            m = INLINE_NONHAEDER_CELL_REGEX.match(row, pos)
                    elif sep == '!':
                        m = INLINE_HAEDER_CELL_REGEX.match(row, pos)
                        while m:
                            data = m.group('data')
                            grouped_spans[-1].append(
                                (ss + m.end() - len(data), ss + m.end())
                            )
                            pos = m.end()
                            m = INLINE_HAEDER_CELL_REGEX.match(row, pos)
        rows = []
        for g in grouped_spans:
            rows.append([])
            for ss, se in g:
                # Spaces after the first newline can be meaningful
                rows[-1].append(string[ss:se].strip(' ').rstrip())
        return rows

    def getrow(self, i):
        """Return the ith row of the table. Note that i starts from 0."""
        return self.rows[i]

    def getcol(self, i):
        """Return the ith column of the table as a list.

        Note that i is the index and starts from 0.
        """
        return [r[i]  for r in self.rows]

    @property
    def caption(self):
        """Return caption of the table."""
        m = CAPTION_REGEX.match(self.string)
        if m:
            return m.group('caption')

    @caption.setter
    def caption(self, newcaption):
        """Set a new caption."""
        m = CAPTION_REGEX.match(self.string)
        if m:
            preattrs = m.group('preattrs')
            attrs = m.group('attrs') or ''
            oldcaption = m.group('caption')
            self.strins(len(preattrs + attrs), newcaption)
            self.strdel(
                len(preattrs + attrs + newcaption),
                len(preattrs + attrs + newcaption + oldcaption),
            )
        else:
            # There is no caption. Create one.
            string = self.string
            h, s, t = string.partition('\n')
            # Insert caption after the first one.
            self.strins(len(h + s), '|+' + newcaption + '\n')

    @property
    def table_attrs(self):
        """Return table attributes.

        Placing attributes after the table start tag ({|) applies
        attributes to the entire table.
        See [[mw:Help:Tables#Attributes on tables]] for more info.
        """
        return self.string.partition('\n')[0][2:]

    @table_attrs.setter
    def table_attrs(self, attrs):
        """Set new attributes for this table."""
        h = self.string.partition('\n')[0]
        self.strins(2, attrs)
        self.strdel(2 + len(attrs), 2 + len(attrs) + len(h[2:]))
        
    @property
    def caption_attrs(self):
        """Return caption attributes."""
        m = CAPTION_REGEX.match(self.string)
        if m:
            return m.group('attrs')

    @caption_attrs.setter
    def caption_attrs(self, attrs):
        """Set new caption attributes."""
        string = self.string
        h, s, t = string.partition('\n')
        m = CAPTION_REGEX.match(string)
        if not m:
            # There is no caption-line
            self.strins(len(h + s), '|+' + attrs + '|\n')
        else:
            preattrs = m.group('preattrs')
            oldattrs = m.group('attrs') or ''
            # Caption and attrs or Caption but no attrs
            self.strins(len(preattrs), attrs)
            self.strdel(
                len(preattrs + attrs),
                len(preattrs + attrs + oldattrs),
            )
