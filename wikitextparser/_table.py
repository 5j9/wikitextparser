"""Define the Table class."""


from bisect import insort_right
from typing import List, Any, Union, Optional, TypeVar, Dict, Tuple

from regex import compile as regex_compile, VERBOSE

from ._cell import (
    Cell,
    NEWLINE_CELL_MATCH,
    INLINE_HAEDER_CELL_MATCH,
    INLINE_NONHAEDER_CELL_MATCH
)
from ._tag import SubWikiTextWithAttrs
from ._spans import ATTRS_MATCH
from ._wikitext import WS


CAPTION_MATCH = regex_compile(
    r"""
    # Everything until the caption line
    (?P<preattrs>
        # Start of table
        {\|
        (?:
            (?:
                (?!\n\s*+\|)
                [\s\S]
            )*?
        )
        # Start of caption line
        \n\s*+\|\+
    )
    # Optional caption attrs
    (?:
        (?P<attrs>[^\n|]*+)
        (?:\|)
        (?!\|)
    )?
    (?P<caption>.*?)
    # End of caption line
    (?:
        \n|
        \|\|
    )
    """,
    VERBOSE
).match
T = TypeVar('T')


COL_ROW_DIGITS = regex_compile(rb'\s*+\d+').match


def head_int(value):
    if value is None:
        return 1
    match = COL_ROW_DIGITS(value)
    return 1 if match is None else int(match[0])


class Table(SubWikiTextWithAttrs):

    __slots__ = '_attrs_match_cache'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attrs_match_cache = None, None

    @property
    def nesting_level(self) -> int:
        """Return the nesting level of self.

        The minimum nesting_level is 0. Being part of any Table increases
        the level by one.
        """
        return self._nesting_level(('Table',)) - 1

    @property
    def _table_shadow(self) -> bytearray:
        """Remove Table spans from shadow and return it."""
        shadow = self._shadow[:]
        ss = self._span_data[0]
        for s, e, _, _ in self._subspans('Table'):
            if s == ss:
                continue
            shadow[s - ss:e - ss] = b'#' * (e - s)
        return shadow

    @property
    def _match_table(self) -> List[List[Any]]:
        """Return match_table."""
        table_shadow = self._table_shadow
        # Remove table-start and table-end marks.
        pos = table_shadow.find(10)  # ord('\n')
        lsp = _lstrip_increase(table_shadow, pos)
        # Remove everything until the first row
        while table_shadow[lsp] not in b'!|':
            nlp = table_shadow.find(10, lsp)  # ord('\n')
            pos = nlp
            lsp = _lstrip_increase(table_shadow, pos)
        # Start of the first row
        match_table = []
        pos = _semi_caption_increase(table_shadow, pos)
        rsp = _row_separator_increase(table_shadow, pos)
        pos = -1
        while pos != rsp:
            pos = rsp
            # We have a new row.
            m = NEWLINE_CELL_MATCH(table_shadow, pos)
            # Don't add a row if there are no new cells.
            if m:
                match_row = []  # type: List[Any]
                match_table.append(match_row)
                while m:
                    match_row.append(m)
                    sep = m['sep']
                    pos = m.end()
                    if sep == b'|':
                        m = INLINE_NONHAEDER_CELL_MATCH(table_shadow, pos)
                        while m:
                            match_row.append(m)
                            pos = m.end()
                            m = INLINE_NONHAEDER_CELL_MATCH(table_shadow, pos)
                    elif sep == b'!':
                        m = INLINE_HAEDER_CELL_MATCH(table_shadow, pos)
                        while m:
                            match_row.append(m)
                            pos = m.end()
                            m = INLINE_HAEDER_CELL_MATCH(table_shadow, pos)
                    pos = _semi_caption_increase(table_shadow, pos)
                    m = NEWLINE_CELL_MATCH(table_shadow, pos)
            rsp = _row_separator_increase(table_shadow, pos)
        return match_table

    def data(
        self, span: bool = True,
        strip: bool = True,
        row: int = None,
        column: int = None
    ) -> Union[List[List[str]], List[str], str]:
        """Return a list containing lists of row values.

        :param span: If true, calculate rows according to rowspans and colspans
            attributes. Otherwise ignore them.
        :param row: Return the specified row only. Zero-based index.
        :param column: Return the specified column only. Zero-based index.
        :param strip: strip data values

        Note: Due to the lots of complications that it may cause, this function
            won't look inside templates, parser functions, etc.
            See https://www.mediawiki.org/wiki/Extension:Pipe_Escape for how
            wiki-tables can be inserted within templates.
        """
        match_table = self._match_table
        # Note string is only used for extracting data, matching is done over
        # the shadow.
        string = self.string
        table_data = []  # type: List[List[str]]
        if strip:
            for match_row in match_table:
                row_data = []  # type: List[str]
                table_data.append(row_data)
                for m in match_row:
                    # Spaces after the first newline can be meaningful
                    s, e = m.span('data')
                    row_data.append(string[s:e].lstrip(' ').rstrip(WS))
        else:
            for match_row in match_table:
                row_data = []
                table_data.append(row_data)
                for m in match_row:
                    s, e = m.span('data')
                    row_data.append(string[s:e])
        if table_data:
            if span:
                table_attrs = []  # type: List[List[Dict[str, str]]]
                for match_row in match_table:
                    row_attrs = []  # type: List[Dict[str, str]]
                    table_attrs.append(row_attrs)
                    row_attrs_append = row_attrs.append
                    for m in match_row:
                        s, e = m.span('attrs')
                        captures = ATTRS_MATCH(
                            string.encode('ascii', 'replace'), s, e).captures
                        row_attrs_append(dict(zip(
                            captures('attr_name'), captures('attr_value')
                        )))
                table_data = _apply_attr_spans(table_attrs, table_data)
        if row is None:
            if column is None:
                return table_data
            return [r[column] for r in table_data]
        if column is None:
            return table_data[row]
        return table_data[row][column]

    def cells(
        self, row: int = None, column: int = None, span: bool = True,
    ) -> Union[List[List[Cell]], List[Cell], Cell]:
        """Return a list of lists containing Cell objects.

        :param span: If is True, rearrange the result according to colspan and
            rospan attributes.
        :param row: Return the specified row only. Zero-based index.
        :param column: Return the specified column only. Zero-based index.

        If both row and column are provided, return the relevant cell object.

        If only need the values inside cells, then use the ``data`` method
        instead.
        """
        tbl_span = self._span_data
        ss = tbl_span[0]
        match_table = self._match_table
        shadow = self._shadow
        type_ = id(tbl_span)
        type_to_spans = self._type_to_spans
        spans = type_to_spans.setdefault(type_, [])
        table_cells = []  # type: List[List[Cell]]
        table_attrs = []  # type: List[List[Dict[str, str]]]
        attrs_match = None
        for match_row in match_table:
            row_cells = []  # type: List[Cell]
            table_cells.append(row_cells)
            header = match_row[0]['sep'] == '!'
            if span:
                row_attrs = []  # type: List[Dict[str, str]]
                table_attrs.append(row_attrs)
                row_attrs_append = row_attrs.append
            for m in match_row:
                ms, me = m.span()
                cell_span = [ss + ms, ss + me, None, shadow[ms:me]]
                if span:
                    s, e = m.span('attrs')
                    # Note: ATTRS_MATCH always matches, even to empty strings.
                    # Also ATTRS_MATCH should match against the cell string
                    # so that it can be used easily as cache later in Cells.
                    attrs_match = ATTRS_MATCH(shadow[ms:me], s - ms, e - ms)
                    captures = attrs_match.captures
                    # noinspection PyUnboundLocalVariable
                    row_attrs_append(dict(zip(
                        captures('attr_name'), captures('attr_value')
                    )))
                old_span = next((s for s in spans if s == cell_span), None)
                if old_span is None:
                    insort_right(spans, cell_span)
                else:
                    cell_span = old_span
                row_cells.append(
                    Cell(
                        self._lststr,
                        header,
                        type_to_spans,
                        cell_span,
                        type_,
                        m,
                        attrs_match,
                    )
                )
        if table_cells and span:
            table_cells = _apply_attr_spans(table_attrs, table_cells)
        if row is None:
            if column is None:
                return table_cells
            return [r[column] for r in table_cells]
        if column is None:
            return table_cells[row]
        return table_cells[row][column]

    @property
    def caption(self) -> Optional[str]:
        """Caption of the table. Support get and set."""
        m = CAPTION_MATCH(self.string)
        if m:
            return m['caption']
        return None

    @caption.setter
    def caption(self, newcaption: str) -> None:
        m = CAPTION_MATCH(self.string)
        if m:
            preattrs = m['preattrs']
            attrs = m['attrs'] or ''
            oldcaption = m['caption']
            self[len(preattrs + attrs):len(preattrs + attrs + oldcaption)] =\
                newcaption
        else:
            # There is no caption. Create one.
            string = self.string
            h, s, t = string.partition('\n')
            # Insert caption after the first one.
            self.insert(len(h + s), '|+' + newcaption + '\n')

    @property
    def _attrs_match(self) -> Any:
        cache_match, cache_string = self._attrs_match_cache
        string = self.string
        if cache_string == string:
            return cache_match
        shadow = self._shadow
        attrs_match = ATTRS_MATCH(shadow, 2, shadow.find(10))  # ord('\n')
        self._attrs_match_cache = attrs_match, string
        return attrs_match

    @property
    def caption_attrs(self) -> Optional[str]:
        """Caption attributes. Support get and set operations."""
        m = CAPTION_MATCH(self.string)
        if m:
            return m['attrs']
        return None

    @caption_attrs.setter
    def caption_attrs(self, attrs: str) -> None:
        string = self.string
        h, s, t = string.partition('\n')
        m = CAPTION_MATCH(string)
        if not m:
            # There is no caption-line
            self.insert(len(h + s), '|+' + attrs + '|\n')
        else:
            preattrs = m['preattrs']
            oldattrs = m['attrs'] or ''
            # Caption and attrs or Caption but no attrs
            self[len(preattrs):len(preattrs + oldattrs)] = attrs


def _apply_attr_spans(
    table_attrs: List[List[Dict[str, str]]], table_data: List[List[T]]
) -> List[List[T]]:
    """Apply row and column spans and return table_data."""
    # The following code is based on the table forming algorithm described
    # at http://www.w3.org/TR/html5/tabular-data.html#processing-model-1
    # Numeral comments indicate the steps in that algorithm.
    # 1, 2, 10
    ycurrent = yheight = xwidth = 0
    # 4
    # The xwidth and yheight variables give the table's dimensions.
    # The table is initially empty.
    table = []  # type: List[List[Optional[T]]]
    append_row = table.append
    # Table.data won't call this function if table_data is empty.
    # 5
    # if not table_data:
    #     return table_data
    # 11
    downward_growing_cells = []  # type: List[Tuple[Optional[T], int, int]]
    # 13, 18
    # Algorithm for processing rows
    for attrs_row, row in zip(table_attrs, table_data):
        # 13.1 ycurrent is never greater than yheight
        if yheight == ycurrent:
            yheight += 1
            append_row([None] * xwidth)
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
        for attrs, current_cell in zip(attrs_row, row):
            # 13.6
            attrs_get = attrs.get
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
            colspan = head_int(attrs_get(b'colspan'))
            if colspan == 0:
                # Note: colspan="0" tells the browser to span the cell to
                # the last column of the column group (colgroup)
                # http://www.w3schools.com/TAGS/att_td_colspan.asp
                colspan = 1
            # 13.9
            rowspan = head_int(attrs_get(b'rowspan'))
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
                    append_row([None] * xwidth)
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
                    (current_cell, xcurrent, colspan))
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


def _lstrip_increase(shadow: bytearray, pos: int) -> int:
    """Return the new position to lstrip the shadow."""
    length = len(shadow)
    while pos < length and shadow[pos] in {0, 9, 10, 32}:  # \0 \t \n space
        pos += 1
    return pos


def _semi_caption_increase(shadow: bytearray, pos: int) -> int:
    """Return the position after the starting semi-caption.

    Captions are optional and only one should be placed between table-start
    and the first row. Others captions are not part of the table and will
    be ignored. We call these semi-captions.
    """
    lsp = _lstrip_increase(shadow, pos)
    while shadow[lsp:lsp + 2] == b'|+':
        pos = shadow.find(10, lsp + 2)  # ord('\n')
        lsp = _lstrip_increase(shadow, pos)
        while shadow[lsp] not in b'!|':
            # This line is a continuation of semi-caption line.
            nlp = shadow.find(10, lsp + 1)  # ord('\n')
            pos = nlp
            lsp = _lstrip_increase(shadow, nlp)
    return pos


def _row_separator_increase(shadow: bytearray, pos: int) -> int:
    """Return the position after the starting row separator line.

    Also skips any semi-caption lines before and after the separator.
    """
    # General format of row separators: r'\|-[^\n]*\n'
    scp = _semi_caption_increase(shadow, pos)
    lsp = _lstrip_increase(shadow, scp)
    while shadow[lsp:lsp + 2] == b'|-':
        # We are on a row separator line.
        pos = shadow.find(10, lsp + 2)  # ord('\n')
        pos = _semi_caption_increase(shadow, pos)
        lsp = _lstrip_increase(shadow, pos)
    return pos
