"""Define the Table class."""


import re
import regex
from html.parser import HTMLParser

from .wikitext import SubWikiText


CAPTION = (
    r"""
    # CAPTION start
    (?:
        # Start of caption line
        \s*\|\+
        # Optional caption attrs
        (?:
            (?P<caption_attrs>[^\n|]*)
            (?:\|)
            (?!\|)
        )?
        (?P<caption_text>[^\n]*?)
        # End of caption line
        (?:\n|\|\|[^\n]*\n)
    )?
    # CAPTION end
    """
)
SEMI_CAPTION = (
    r"""
    # SEMI_CAPTION start
    (?:
        \s*
        \|\+
        (?:.(?!\n\s*[|!]))*
        .\n
    )*
    # SEMI_CAPTION end
    """
)
ROW_SEPARATOR = (
    r"""
    # ROW_SEPARATOR start
    (?P<row_sep>
        # Treat multiple consecutive row separators as one.
        (?>\s*[|!]-[^\n]*\n)+
    )
    # ROW_SEPARATOR end
    """
)
CELL_DATA = (
    r"""
    # CELL_DATA start
    (?P<data>
        (?:
            (?:
                .(?!
                    # start of the next cell
                    \|\|
                    |(?P=sep){2}
                    |\n\s*[!|]
                )
            )*.
        )
    )\s*
    # CELL_DATA end
    """
)
CELL_ATTRS = (
    r"""
    # CELL_ATTRS start
    (?:
        # catch the matching pipe (style holder).
        (?P<cell_attrs>)\| # immediate closure (attrs='')
        |(?P<cell_attrs>
            (?(header)
                # attrs can't contain "|" (or "!" if the sep is "!")
                (?>[^|!\n]*)
                # attrs can't end with "||" (or "!!" if the sep is "!")
                (?![!|]{2}|\n).
                |
                # attrs can't contain "|" (or "!" if the sep is "!")
                (?>[^|\n]*)
                # attrs can't end with "||" (or "!!" if the sep is "!")
                (?!\|{2}|\n).
            )
        )
        |(?P<cell_attrs>) #CELLATTRS are optional
    )
    # CELL_ATTRS end
    """
)
NEWLINE_CELL = (
    r"""
    # NEWLINE_CELL start
    \s*
    (?P<sep>(?P<header>!)|\|)(?!\-)
    {CELL_ATTRS}
    {CELL_DATA}
    # NEWLINE_CELL end
    """.format(**locals())
)
# https://regex101.com/r/qK1pJ8/5
INLINE_HAEDER_CELL = (
    r"""
    # INLINE_HAEDER_CELL start
    (?:
        [|!]{{2}}
        {CELL_ATTRS}
        {CELL_DATA}
    )
    # INLINE_HAEDER_CELL end
    """.format(**locals())
)
# https://regex101.com/r/hW8aZ3/7
INLINE_NONHAEDER_CELL = (
    r"""
    # INLINE_NONHAEDER_CELL start
    (?:
        \|\| # catch the matching pipe (style holder).
        {CELL_ATTRS}
        {CELL_DATA}
    )
    # INLINE_NONHAEDER_CELL end
    """.format(**locals())
)
CELL_LINES = (
    r"""
    # CELL_LINES start
    (?:
        {NEWLINE_CELL}
        (?(header)
            {INLINE_HAEDER_CELL}*|
            {INLINE_NONHAEDER_CELL}*
        )
    )
    # CELL_LINES end
    """.format(**locals())
)
FIRST_ROW = (
    """
    # FIRST_ROW start
    (?:
        # Row separator can be omitted for the first row
        {ROW_SEPARATOR}?
        {CELL_LINES}*
    )
    # FIRST_ROW end
    """.format(**locals())
)
ROW = (
    r"""
    # ROW start
    (?:
        {ROW_SEPARATOR}
        {CELL_LINES}*
    )
    # ROW end
    """.format(**locals())
)
ROWS = (
    r"""
    # ROWS start
    # Ignorable captions
    {SEMI_CAPTION}
    (?:{FIRST_ROW}{ROW}*)?
    # ROWS end
    """.format(**locals())
)
TABLE_PATTERN = (
    r"""
    # TABLE_PATTERN start
    (?>
        {{\|
        (?P<table_attrs>[^\n]*)\s*
    )
    {CAPTION}
    # Ignorable lines
    (?:
        [^|!][^\n]*(?!\s*[|!])
    )*
    {ROWS}
    \|}}
    # TABLE_PATTERN end
    """.format(**locals())
)

TABLE_REGEX = regex.compile(TABLE_PATTERN, regex.VERBOSE | regex.DOTALL)
from pyperclip import *
copy(TABLE_REGEX.pattern)


class Table(SubWikiText):

    """Create a new Table object."""

    def __init__(
        self,
        string: str or list,
        spans: list or None=None,
        index: int or None=None,
    ) -> None:
        """Run _common_init. Set _type_to_spans['tables'] if spans is None."""
        self._common_init(string, spans)
        if spans is None:
            self._type_to_spans['tables'] = [(0, len(string))]
        if index is None:
            self._index = len(self._type_to_spans['tables']) - 1
        else:
            self._index = index

    def __repr__(self) -> str:
        """Return the string representation of the Table."""
        return 'Table(' + repr(self.string) + ')'

    def _get_span(self) -> tuple:
        """Return the self-span."""
        return self._type_to_spans['tables'][self._index]

    def _match(self, string):
        """Match the table to TABLE_REGEX and return the match object."""
        shadow = self._shadow()
        return TABLE_REGEX.match(shadow)

    def getdata(self, span: bool=True) -> list:
        """Return a list containing lists of row values.

        :span: If true, calculate rows according to rowspan and colspan
            attributes. Otherwise ignore them.

        Note: Values will be stripped.

        Due to lots of complications that it may cause, this function
        won't look inside templates, parser functions, etc.

        See https://www.mediawiki.org/wiki/Extension:Pipe_Escape for how
        wikitables can be inserted within templates.

        """
        string = self.string
        m = self._match(string)
        data_span_rows = []
        attr_span_rows = []
        row_separator_starts = list(reversed(m.starts('row_sep')))
        data_starts = m.starts('data')
        data_spans = m.spans('data')
        attr_spans = m.spans('cell_attrs')
        if row_separator_starts and row_separator_starts[-1] < data_starts[0]:
            # Ignore the first optional row separator.
            row_separator_starts.pop()
        data_span_row = []
        attr_span_row = []
        for i, data_capture in enumerate(data_spans):
            data_start = data_starts[i]
            if row_separator_starts and row_separator_starts[-1] < data_start:
                # Start a new row
                data_span_rows.append(data_span_row)
                attr_span_rows.append(attr_span_row)
                data_span_row = [data_capture]
                attr_span_row = [attr_spans[i]]
                row_separator_starts.pop()
            else:
                data_span_row.append(data_capture)
                attr_span_row.append(attr_spans[i])
        # Append the data for the last row.
        data_span_rows.append(data_span_row)
        attr_span_rows.append(attr_span_row)
        # Note: We have used spans to avoid conflicting templates and pfs.
        # Parse attributes
        for i, r in enumerate(attr_span_rows):
            attr_span_row = attr_span_rows[i]
            for j, (s, e) in enumerate(r):
                attr_span_row[j] = attrs_parser(string[s:e])
        # Convert spans to strings
        for i, r in enumerate(data_span_rows):
            data_span_row = data_span_rows[i]
            for j, (s, e) in enumerate(r):
                data_span_row[j] = string[s:e].strip(' ')
        if span and data_span_rows:
            data_span_rows = _apply_attr_spans(
                attr_span_rows,
                data_span_rows,
                string,
            )
        return data_span_rows

    def getrdata(self, i: int) -> list:
        """Return the data in the ith row of the table.

        i is the index and starts from 0.

        """
        # Todo: Cache self.getdata?
        return self.getdata()[i]

    def getcdata(self, i: int) -> list:
        """Return the data in ith column of the table as a list.

        i is the index and starts from 0.
        """
        return [r[i] for r in self.getdata()]

    @property
    def caption(self) -> str or None:
        """Return caption of the table."""
        m = CAPTION_REGEX.match(self.string)
        if m:
            return m.group('caption')

    @caption.setter
    def caption(self, newcaption: str) -> None:
        """Set a new caption."""
        m = CAPTION_REGEX.match(self.string)
        if m:
            preattrs = m.group('preattrs')
            attrs = m.group('attrs') or ''
            oldcaption = m.group('caption')
            self[len(preattrs + attrs):len(preattrs + attrs + oldcaption)] =\
                newcaption
        else:
            # There is no caption. Create one.
            string = self.string
            h, s, t = string.partition('\n')
            # Insert caption after the first one.
            self.insert(len(h + s), '|+' + newcaption + '\n')

    @property
    def table_attrs(self) -> str:
        """Return table attributes.

        Placing attributes after the table start tag ({|) applies
        attributes to the entire table.
        See [[mw:Help:Tables#Attributes on tables]] for more info.

        """
        return self.string.partition('\n')[0][2:]

    @table_attrs.setter
    def table_attrs(self, attrs: str) -> None:
        """Set new attributes for this table."""
        h = self.string.partition('\n')[0]
        self[2:2 + len(h[2:])] = attrs

    @property
    def caption_attrs(self) -> str or None:
        """Return caption attributes."""
        m = CAPTION_REGEX.match(self.string)
        if m:
            return m.group('attrs')

    @caption_attrs.setter
    def caption_attrs(self, attrs: str):
        """Set new caption attributes."""
        string = self.string
        h, s, t = string.partition('\n')
        m = CAPTION_REGEX.match(string)
        if not m:
            # There is no caption-line
            self.insert(len(h + s), '|+' + attrs + '|\n')
        else:
            preattrs = m.group('preattrs')
            oldattrs = m.group('attrs') or ''
            # Caption and attrs or Caption but no attrs
            self[len(preattrs):len(preattrs + oldattrs)] = attrs


class Cell(SubWikiText):

    """Create a new Cell object."""

    def __init__(
        self,
        string: str or list,
        spans: list or None=None,
        index: int or None=None,
    ) -> None:
        """Run _common_init. Set _type_to_spans['tables'] if spans is None."""
        self._common_init(string, spans)
        if spans is None:
            self._type_to_spans['cells'] = [(0, len(string))]
        if index is None:
            self._index = len(self._type_to_spans['cells']) - 1
        else:
            self._index = index

    def __repr__(self) -> str:
        """Return the string representation of the Cell."""
        return 'Cell(' + repr(self.string) + ')'

    def _get_span(self) -> tuple:
        """Return the self-span."""
        return self._type_to_spans['cells'][self._index]


class AttrsParser(HTMLParser):

    """Define the class to construct the attrs_parser from it."""

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Store parsed attrs in self.parsed and then self.reset().

        The `tag` argument is the name of the tag converted to lower case.
        The `attrs` argument is a list of (name, value) pairs containing the
            attributes found inside the tag’s <> brackets.

        """
        self.parsed = attrs
        self.reset()

    def parse(self, attrs: str) -> dict:
        """Return a dict of parsed name and value pairs.

        Example:
            >>> AttrsParser().parse('''\t colspan = " 2 " rowspan=\n6 ''')
            [('colspan', ' 2 '), ('rowspan', '6')]
        """
        self.feed('<a ' + attrs + '>')
        return dict(self.parsed)


def _apply_attr_spans(attr_spans: list, data_spans: list, string: str) -> list:
    """Apply row and column spans and return data_spans."""
    # The following code is based on the table forming algorithm described
    # at http://www.w3.org/TR/html5/tabular-data.html#processing-model-1
    # Numbered comments indicate the step in that algorithm.
    # 1
    xwidth = 0
    # 2
    yheight = 0
    # 4
    # The xwidth and yheight variables give the table's dimensions.
    # The table is initially empty.
    table = []
    # getdata won't call this function if data_spans is empty.
    # 5
    # if not data_spans:
    #     return data_spans
    # 10
    ycurrent = 0
    # 11
    downward_growing_cells = []
    # 13, 18
    # Algorithm for processing rows
    for i, row in enumerate(data_spans):
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
                colspan = int(attr_spans[i][j]['colspan'])
                if colspan == 0:
                    # Note: colspan="0" tells the browser to span the cell to
                    # the last column of the column group (colgroup)
                    # http://www.w3schools.com/TAGS/att_td_colspan.asp
                    colspan = 1
            except Exception:
                colspan = 1
            # 13.9
            try:
                rowspan = int(attr_spans[i][j]['rowspan'])
            except Exception:
                rowspan = 1
            # 13.10
            if rowspan == 0:
                # Note: rowspan="0" tells the browser to span the cell to the
                # last row of the table.
                # http://www.w3schools.com/tags/att_td_rowspan.asp
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
    # downward_growing_cells = []
    # 20 If there exists a row or column in the table containing only
    # slots that do not have a cell anchored to them,
    # then this is a table model error.
    return table


attrs_parser = AttrsParser().parse
