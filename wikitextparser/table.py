"""Define a class to deal with tables."""


import re
from html.parser import HTMLParser


ROWSEP_REGEX = re.compile(r'^\s*[\|!]-.*?\n', re.M)
# https://regex101.com/r/hB4dX2/17
NEWLINE_CELL_REGEX = re.compile(
    r"""
    # only for matching, not searching
    (?P<whitespace>\s*)
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
    re.MULTILINE | re.VERBOSE
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

    def getdata(self, span=True):
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
        dataspans = [[0]]
        for m in ROWSEP_REGEX.finditer(shadow):
            dataspans[-1].append(m.start())
            dataspans.append([m.end()])
        dataspans[-1].append(-1)
        cell_spans = []
        if span:
            attr_spans = []
        for ss, se in dataspans:
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
                            # The leading whitespace in newline-cells
                            # must be ignored
                            m, attr_spans, ss + len(m.group('whitespace'))
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
                                    m, attr_spans, ss + 1
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
                                    m, attr_spans, ss + 1
                                )
                            pos = m.end()
                            m = INLINE_HAEDER_CELL_REGEX.match(row, pos)
        data = []
        for g in cell_spans:
            data.append([])
            for ss, se in g:
                # Spaces after the first newline can be meaningful
                data[-1].append(string[ss:se].strip(' ').rstrip())
        if span and data:
            data = self._apply_attr_spans(attr_spans, data, string)
        return data

    def _apply_attr_spans(self, attr_spans, data, string):
        """Apply colspans to data and return data."""
        # Todo: maybe it's better to do this parsing in self.getdata?
        attrs = []
        for r in attr_spans:
            attrs.append([])
            for ss, se in r:
                if se is not None:
                    attrs[-1].append(attrs_parser(string[ss:se]))
                else:
                    attrs[-1].append(None)
        # The following code is based on the table forming algorithm described
        # at http://www.w3.org/TR/html5/tabular-data.html#processing-model-1
        # Some comments indicate the step in that algorithm.
        # 1
        xwidth = 0
        # 2
        yheight = 0
        # 4
        # The xwidth and yheight variables give the table's dimensions.
        # The table is initially empty.
        table = []
        # 5
        if not data:
            return data
        # 10
        ycurrent = 0
        # 11
        downward_growing_cells = []
        # 13, 18
        # Algorithm for processing rows
        for i, row in enumerate(data):
            # 13.1 ycurrent is never greater than yheight
            if yheight == ycurrent:
                yheight += 1
                table.append([None] * xwidth)
            # 13.2
            xcurrent = 0
            # 13.3
            # The algorithm for growing downward-growing cells
            for cell, cellx, width in downward_growing_cells:
                r = table[ycurrent]
                for x in range(cellx, cellx + width):
                    r[x] = cell
            # 13.4 will be handled by the following for-loop.
            # 13.5, 13.16
            for j, current_cell in enumerate(row):
                # 13.6
                while (
                    xcurrent < xwidth and
                    table[ycurrent][xcurrent] is not None
                ):
                    xcurrent += 1
                # 13.7
                if xcurrent == xwidth:
                    # xcurrent is never greater than xwidth
                    xwidth += 1
                    for r in table:
                        if xwidth > len(r):
                            r.extend([None] * (xwidth - len(r)))
                # 13.8
                try:
                    colspan = int(attrs[i][j]['colspan'])
                    if colspan == 0:
                        colspan = 1
                except Exception:
                    colspan = 1
                # 13.9
                try:
                    rowspan = int(attrs[i][j]['rowspan'])
                except Exception:
                    rowspan = 1
                # 13.10
                if rowspan == 0:
                    cell_grows_downward = True
                    rowspan = 1
                else:
                    cell_grows_downward = False
                # 13.11
                if xwidth < xcurrent + colspan:
                    xwidth = xcurrent + colspan
                    for r in table:
                        if xwidth > len(r):
                            r.extend([None] * (xwidth - len(r)))
                # 13.12
                if yheight < ycurrent + rowspan:
                    yheight = ycurrent + rowspan
                    while len(table) < yheight:
                        table.append([None] * xwidth)
                # 13.13
                for y in range(ycurrent, ycurrent + rowspan):
                    r = table[y]
                    for x in range(xcurrent, xcurrent + colspan):
                        # If any of the slots involved already had a cell
                        # covering them, then this is a table model error.
                        # Those slots now have two cells overlapping.
                        r[x] = current_cell
                        # Skipping algorithm for assigning header cells
                # 13.14
                if cell_grows_downward:
                    downward_growing_cells.append(
                        (current_cell, xcurrent, colspan)
                    )
                # 13.15
                xcurrent += colspan
            # 13.16
            ycurrent += 1
        # 14
        # The algorithm for ending a row group
        # 14.1
        while ycurrent < yheight:
            # 14.1.1
            # Run the algorithm for growing downward-growing cells.
            for cell, cellx, width in downward_growing_cells:
                for x in range(cellx, cellx + width):
                    table[ycurrent][x] = cell
            # 14.2.2
            ycurrent += 1
        # 14.2
        downward_growing_cells = []
        # 20 If there exists a row or column in the table containing only
        # slots that do not have a cell anchored to them,
        # then this is a table model error.
        return table

    def _extend_attr_spans(self, m, attr_spans, ss):
        """Extend attr_spans according to parameters.

        Sub-function of self.getdata.
        """
        attrs = m.group('attrs')
        if attrs:
            attrs_start = ss + m.start() + 1
            attr_spans[-1].append(
                (attrs_start, attrs_start + len(attrs))
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
        return [r[i] for r in self.getdata()]

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
            self.replace_slice(
                len(preattrs + attrs),
                len(preattrs + attrs + oldcaption),
                newcaption,
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
        self.replace_slice(2, 2 + len(h[2:]), attrs)

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
            self.replace_slice(len(preattrs), len(preattrs + oldattrs), attrs)


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
