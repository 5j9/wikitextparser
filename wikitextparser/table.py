"""Define a class to deal with tables."""


import re
from html.parser import HTMLParser


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

    def getdata(self, span=False):
        """Return a tuple containing value of all rows.

        @param:`span` indicates if rowspans and colspans attributes should be
            expanded or not. Todo: Don't use this param. Still in development.
        
        Due to the lots of complications that it will cause, this function
        won't look inside templates, parserfunctions, etc.

        See https://www.mediawiki.org/wiki/Extension:Pipe_Escape for how
        wikitables can be inserted within templates.
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
        cell_spans = []
        if span:
            attr_spans = []
        for ss, se in rowspans:
            row = shadow[ss:se]
            if not row.lstrip():
                # When the optional `|-` for the first row is used or when 
                # there are meaningless row seprators that result in rows
                # containing no cells.
                continue
            cell_spans.append([])
            if span:
                attr_spans.append([])
            pos = 0
            lastpos = -1
            while pos != lastpos:
                lastpos = pos
                sep = None
                m = NEWLINE_CELL_REGEX.match(row, pos)
                if m:
                    sep = m.group('sep')
                    data = m.group('data')
                    cell_spans[-1].append(
                        (ss + m.end() - len(data), ss + m.end())
                    )
                    if span:
                        self._extend_attr_spans(
                            m, attr_spans, ss
                        )
                    pos = m.end()
                    if sep == '|':
                        m = INLINE_NONHAEDER_CELL_REGEX.match(row, pos)
                        while m:
                            data = m.group('data')
                            cell_spans[-1].append(
                                (ss + m.end() - len(data), ss + m.end())
                            )
                            if span:
                                self._extend_attr_spans(
                                    m, attr_spans, ss
                                )
                            pos = m.end()
                            m = INLINE_NONHAEDER_CELL_REGEX.match(row, pos)
                    elif sep == '!':
                        m = INLINE_HAEDER_CELL_REGEX.match(row, pos)
                        while m:
                            data = m.group('data')
                            cell_spans[-1].append(
                                (ss + m.end() - len(data), ss + m.end())
                            )
                            if span:
                                self._extend_attr_spans(
                                    m, attr_spans, ss
                                )
                            pos = m.end()
                            m = INLINE_HAEDER_CELL_REGEX.match(row, pos)
                    
        # rows matrix
        rows = []
        for g in cell_spans:
            rows.append([])
            for ss, se in g:
                # Spaces after the first newline can be meaningful
                rows[-1].append(string[ss:se].strip(' ').rstrip())
        if span and rows:
            self._apply_attr_spans(attr_spans, rows, string)
        return rows


    def _apply_attr_spans(self, attr_spans, rows, string):
        """Apply colspans and rowspans to rows."""
        # span cells
        
        imax = len(attr_spans) - 1
        jmax = max(len(r) for r in attr_spans)
        i = 0
        changed = True
        while changed:
            changed = False
            while i < imax:
                j = 0
                ilen = len(attr_spans[i])            
                while j < ilen:
                    try:
                        ss, se = attr_spans[i][j]
                    except:
                        from pprint import pprint as pp
                        pp(attr_spans)
                    if se is not None:
                        parsed_attrs = attrs_parser(string[ss:se])
                        if 'colspan' in parsed_attrs:
                            colspan = parsed_attrs['colspan']
                            if colspan.isdecimal():
                                colspan = min(
                                    int(colspan) - 1, # requested
                                    jmax - ilen # available
                                )
                                for c in range(colspan):
                                    rows[i].insert(j, rows[i][j])
                                    attr_spans[i].insert(j, (None, None))
                                    ilen += 1
                                    j += 1
                                changed = True
                        if 'rowspan' in parsed_attrs:
                            rowspan = parsed_attrs['rowspan']
                            if rowspan.isdecimal():
                                rowspan = min(
                                    int(rowspan) - 1, # requested
                                    imax - i # available
                                )
                                for c in range(rowspan):
                                    rows[i + c + 1].insert(j, rows[i][j])
                                    attr_spans[i + c + 1].insert(
                                        j, (None, None)
                                    )
                                changed = True
                    j += 1
                i += 1        

    def _extend_attr_spans(self, m, attr_spans, ss):
        """Extend attr_spans according to parameters.

        Sub-function of self.getdata.
        """
        attrs = m.group('attrs')
        if attrs:
            attr_spans[-1].append(
                (ss + 1, ss + 1 + len(attrs))
            )
        else:
            attr_spans[-1].append((None, None))

    def getrdata(self, i):
        """Return the data in the ith row of the table.

        i is the index and starts from 0.
        """
        return self.getdata()[i]

    def getcdata(self, i):
        """Return the data in ith column of the table as a list.

        i is the index and starts from 0.
        """
        return [r[i]  for r in self.getdata()]

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


class AttrsParser(HTMLParser):

    """A class to generate attrs_parser from."""
        
    def handle_starttag(self, tag, attrs):
        """Store parsed attrs in self.parsed and then self.reset()."""
        self.parsed = attrs
        self.reset()

    def parse(self, attrs):
        """Return list of parsed name and value pairs.

        Example:
            >>> AttrsParser().parse('''\t colspan = " 2 " rowspan=\n6 ''')
            [('colspan', ' 2 '), ('rowspan', '6')]
        """
        self.feed('<a ' + attrs + '>')
        return dict(self.parsed)


attrs_parser = AttrsParser().parse
