"""Test the functionalities of table.py module."""
# Todo: addrow, addcol, shiftrow, shiftcol, ...
# addrow([], -1)
# addcol([], -1)
#
# shiftrow(n,m)
# shiftcol(n,m)
#
# sort?
# transpose?


import unittest

from wikitextparser import Table, WikiText


class Data(unittest.TestCase):

    """Test the data method of the table class."""

    def test_each_row_on_a_newline(self):
        table = Table(
            '{|\n'
            '|Orange\n'
            '|Apple\n'
            '|-\n'
            '|Bread\n'
            '|Pie\n'
            '|-\n'
            '|Butter\n'
            '|Ice cream \n'
            '|}'
        )
        self.assertEqual(
            table.data(),
            [['Orange', 'Apple'], ['Bread', 'Pie'], ['Butter', 'Ice cream']],
        )

    def test_with_optional_rowseprator_on_first_row(self):
        table = Table(
            '{| class=wikitable | g\n'
            ' |- 132131 |||\n'
            '  | a | b\n'
            ' |-\n'
            '  | c\n'
            '|}'
        )
        self.assertEqual(
            table.data(),
            [['b'], ['c']],
        )

    def test_all_rows_are_on_a_single_line(self):
        table = Table(
            '{|\n'
            '|a||b||c\n'
            '|-\n'
            '|d||e||f\n'
            '|-\n'
            '|g||h||i\n'
            '|}'
        )
        self.assertEqual(
            table.data(),
            [['a', 'b', 'c'], ['d', 'e', 'f'], ['g', 'h', 'i']],
        )

    def test_extra_spaces_have_no_effect(self):
        table = Table(
            '{|\n|  Orange    ||   Apple   ||   more\n|-\n'
            '|   Bread    ||   Pie     ||   more\n|-\n'
            '|   Butter   || Ice cream ||  and more\n|}'
        )
        self.assertEqual(
            table.data(),
            [
                ['Orange', 'Apple', 'more'],
                ['Bread', 'Pie', 'more'],
                ['Butter', 'Ice cream', 'and more']],
        )

    def test_longer_text_and_only_rstrip(self):
        table = Table(
            '{|\n|multi\nline\ntext. \n\n2nd paragraph. \n|'
            '\n* ulli1\n* ulli2\n* ulli3\n|}'
        )
        self.assertEqual(
            table.data(),
            [
                [
                    'multi\nline\ntext. \n\n2nd paragraph.',
                    '\n* ulli1\n* ulli2\n* ulli3'
                ]
            ]
        )

    def test_strip_is_false(self):
        table = Table(
            '{|class=wikitable\n| a || b \n|}'
        )
        self.assertEqual(table.data(strip=False), [[' a ', ' b ']])

    def test_doublepipe_multiline(self):
        table = Table(
            '{|\n|| multi\nline\n||\n 1\n|}'
        )
        self.assertEqual(table.data(), [['multi\nline', '\n 1']])

    def test_with_headers(self):
        table = Table(
            '{|\n! style="text-align:left;"| Item\n! Amount\n! Cost\n|-\n'
            '|Orange\n|10\n|7.00\n|-\n|Bread\n|4\n|3.00\n|-\n'
            '|Butter\n|1\n|5.00\n|-\n!Total\n|\n|15.00\n|}'
        )
        self.assertEqual(
            table.data(), [
                ['Item', 'Amount', 'Cost'],
                ['Orange', '10', '7.00'],
                ['Bread', '4', '3.00'],
                ['Butter', '1', '5.00'],
                ['Total', '', '15.00'],
            ]
        )

    def test_with_caption(self):
        table = Table(
            '{|\n|+Food complements\n|-\n|Orange\n|Apple\n|-\n'
            '|Bread\n|Pie\n|-\n|Butter\n|Ice cream \n|}'
        )
        self.assertEqual(
            table.data(),
            [['Orange', 'Apple'], ['Bread', 'Pie'], ['Butter', 'Ice cream']],
        )

    def test_with_caption_attrs(self):
        table = Table(
            '{|class=wikitable\n'
            '|+ sal | no\n'
            '|a \n'
            '|}'
        )
        self.assertEqual(table.data(), [['a']])

    def test_second_caption_is_ignored(self):
        table = Table(
            '{|\n'
            '  |+ c1\n'
            '  |+ c2\n'
            '|-\n'
            '|1\n'
            '|2\n'
            '|}')
        self.assertEqual(table.data(), [['1', '2']])

    def test_unneeded_newline_after_table_start(self):
        table = Table('{|\n\n|-\n|c1\n|c2\n|}')
        self.assertEqual(table.data(), [['c1', 'c2']])

    def test_text_after_tablestart_is_not_actually_inside_the_table(self):
        table = Table(
            '{|\n'
            '  text\n'
            '|-\n'
            '|c1\n'
            '|c2\n'
            '|}'
        )
        self.assertEqual(table.data(), [['c1', 'c2']])

    def test_empty_table(self):
        table = Table('{|class=wikitable\n|}')
        self.assertEqual(table.data(), [])

    def test_empty_table_comment_end(self):
        table = Table(
            '{|class=wikitable\n'
            '<!-- c -->|}'
        )
        self.assertEqual(table.data(), [])

    def test_empty_table_semi_caption_comment(self):
        table = Table('{|class=wikitable\n|+\n<!-- c -->|}')
        self.assertEqual(table.data(), [])

    def test_empty_cell(self):
        table = Table('{|class=wikitable\n||a || || c\n|}')
        self.assertEqual(table.data(), [['a', '', 'c']])

    def test_pipe_as_text(self):
        table = Table('{|class=wikitable\n||a | || c\n|}')
        self.assertEqual(table.data(), [['a |', 'c']])

    def test_meaningless_rowsep(self):
        table = Table(
            '{|class=wikitable\n'
            '||a || || c\n'
            '|-\n'
            '|}'
        )
        self.assertEqual(table.data(), [['a', '', 'c']])

    def test_template_inside_table(self):
        table = Table('{|class=wikitable\n|-\n|{{text|a}}\n|}')
        self.assertEqual(table.data(), [['{{text|a}}']])

    def test_only_pipes_can_seprate_attributes(self):
        """According to the note at mw:Help:Tables#Table_headers."""
        table = Table(
            '{|class=wikitable\n! style="text-align:left;"! '
            'Item\n! Amount\n! Cost\n|}'
        )
        self.assertEqual(table.data(), [
            ['style="text-align:left;"! Item', 'Amount', 'Cost']
        ])
        table = Table(
            '{|class=wikitable\n! style="text-align:left;"| '
            'Item\n! Amount\n! Cost\n|}'
        )
        self.assertEqual(table.data(), [
            ['Item', 'Amount', 'Cost']
        ])

    def test_double_exclamation_marks_are_valid_on_header_rows(self):
        table = Table('{|class=wikitable\n!a!!b!!c\n|}')
        self.assertEqual(table.data(), [['a', 'b', 'c']])

    def test_double_exclamation_marks_are_valid_only_on_header_rows(self):
        # Actually I'm not sure about this in general.
        table = Table('{|class=wikitable\n|a!!b!!c\n|}')
        self.assertEqual(table.data(), [['a!!b!!c']])

    def test_caption_in_row_is_treated_as_pipe_and_plut(self):
        table = Table('{|class=wikitable\n|a|+b||c\n|}')
        self.assertEqual(table.data(), [['+b', 'c']])

    def test_odd_case1(self):
        table = Table(
            '{|class=wikitable\n'
            '  [[a]]\n'
            ' |+ cp1\n'
            'cp1\n'
            '! h1 ||+ h2\n'
            '|-\n'
            '! h3 !|+ h4\n'
            '|-\n'
            '! h5 |!+ h6\n'
            '|-\n'
            '|c1\n'
            '|+t [[w]]\n\n'
            'text\n'
            '|c2\n'
            '|}'
        )
        self.assertEqual(table.data(span=False), [
            ['h1', '+ h2'],
            ['+ h4'],
            ['!+ h6'],
            ['c1', 'c2']
        ])

    def test_colspan_and_rowspan_and_span_false(self):
        table = Table(
            '{| class="wikitable"\n!colspan= 6 |11\n|-\n'
            '|rowspan="2"|21\n|22\n|23\n|24\n|colspan="2"|25\n|-\n'
            '|31\n|colspan="2"|32\n|33\n|34\n|}'
        )
        self.assertEqual(table.data(span=False), [
            ['11'],
            ['21', '22', '23', '24', '25'],
            ['31', '32', '33', '34'],
        ])

    def test_colspan_and_rowspan_and_span_true(self):
        table = Table(
            '{| class="wikitable"\n!colspan= 6 |11\n|-\n'
            '|rowspan="2"|21\n|22\n|23\n|24\n  |colspan="2"|25\n|-\n'
            '|31\n|colspan="2"|32\n|33\n|34\n|}'
        )
        self.assertEqual(table.data(span=True), [
            ['11', '11', '11', '11', '11', '11'],
            ['21', '22', '23', '24', '25', '25'],
            ['21', '31', '32', '32', '33', '34'],
        ])

    def test_inline_colspan_and_rowspan(self):
        table = Table(
            '{| class=wikitable\n'
            ' !a !! b !!  c !! rowspan = 2 | d \n'
            ' |- \n'
            ' | e || colspan = "2"| f\n'
            '|}'
        )
        self.assertEqual(table.data(span=True), [
            ['a', 'b', 'c', 'd'],
            ['e', 'f', 'f', 'd']
        ])

    def test_growing_downward_growing_cells(self):
        table = Table(
            '{|class=wikitable\n'
            '| a || rowspan=0 | b\n'
            '|-\n'
            '| c\n'
            '|}'
        )
        self.assertEqual(table.data(span=True), [
            ['a', 'b'],
            ['c', 'b'],
        ])

    def test_colspan_0(self):
        table = Table(
            '{|class=wikitable\n'
            '| colspan=0 | a || b\n'
            '|-\n'
            '| c || d\n'
            '|}'
        )
        self.assertEqual(table.data(span=True), [
            ['a', 'b'],
            ['c', 'd'],
        ])

    def test_ending_row_group(self):
        table = Table(
            '{|class=wikitable\n'
            '| rowspan = 3 | a || b\n'
            '|-\n'
            '| c\n'
            '|}'
        )
        self.assertEqual(table.data(span=True), [
            ['a', 'b'],
            ['a', 'c'],
            ['a', None],
        ])

    def test_ending_row_group_and_rowspan_0(self):
        table = Table(
            '{|class=wikitable\n'
            '| rowspan = 3 | a || rowspan = 0 | b || c\n'
            '|-\n'
            '| d\n'
            '|}'
        )
        self.assertEqual(table.getdata(span=True), [
            ['a', 'b', 'c'],
            ['a', 'b', 'd'],
            ['a', 'b', None],
        ])

    def test_row_data(self):
        table = Table('{|\n|a||b||c\n|-\n|d||e||f\n|-\n|g||h||i\n|}')
        self.assertEqual(table.getrdata(1), ['d', 'e', 'f'])

    def test_column_data(self):
        table = Table('{|\n|a||b||c\n|-\n|d||e||f\n|-\n|g||h||i\n|}')
        self.assertEqual(table.getcdata(1), ['b', 'e', 'h'])

    def test_column_and_row_data(self):
        table = Table('{|\n|a||b||c\n|-\n|d||e||f\n|-\n|g||h||i\n|}')
        self.assertEqual(table.data(column=1, row=1), 'e')

    def test_header_attr_with_exclamation_mark(self):
        table = Table(
            '{|class=wikitable\n! 1 !! a1 ! a2 | 2 || class=a3 ! id=a4 | 3\n|}'
        )
        self.assertEqual(table.data(), [['1', '2', '3']])

    def test_nonheader_attr_with_exclamation_mark(self):
        table = Table(
            '{|class=wikitable\n'
            '| 1 !! 1 ! 1 |||| 3 || a4 ! a4 | 4\n'
            '|}'
        )
        self.assertEqual(table.data(), [['1 !! 1 ! 1', '', '3', '4']])

    def test_single_exclamation_is_not_attribute_data_separator(self):
        table = Table(
            '{|class=wikitable\n'
            '! 1 !! 2 ! 2 !!!! 4 || a5 ! a5 | 5\n'
            '|}'
        )
        self.assertEqual(table.data(), [['1', '2 ! 2', '', '4', '5']])

    def test_newline_cell_attr_closure_cant_be_cell_sep(self):
        table = Table(
            '{|class=wikitable\n'
            '||||| 2 ! 2\n'
            '|}'
        )
        self.assertEqual(table.data(), [['', '', '2 ! 2']])

    def test_attr_delimiter_cant_be_adjacent_to_cell_delimiter(self):
        """Couldn't find a logical explanation for MW's behaviour."""
        table = Table(
            '{|class=wikitable\n'
            '!a| !!b|c\n'
            '|}'
        )
        self.assertEqual(table.data(), [['', 'c']])
        # Remove one space and...
        table = Table(
            '{|class=wikitable\n'
            '!a|!!b|c\n'
            '|}'
        )
        self.assertEqual(table.data(), [['a', 'b|c']])


class Caption(unittest.TestCase):

    """Test the caption and caption_attrs methods."""

    def test_no_caption(self):
        table = Table('{| class="wikitable"\n|a\n|+ ignore\n|}')
        self.assertEqual(table.caption, None)
        self.assertEqual(table.caption_attrs, None)
        table.caption = 'foo'
        self.assertEqual(
            table.string,
            '{| class="wikitable"\n|+foo\n|a\n|+ ignore\n|}'
        )

    def test_replace_caption_attrs(self):
        table = Table('{|class="wikitable"\n|+old|cap\n|}')
        table.caption_attrs = 'new'
        self.assertEqual(table.caption_attrs, 'new')

    def test_set_caption_attrs_before_cap(self):
        table = Table('{| class="wikitable"\n|a\n|+ ignore\n|}')
        table.caption_attrs = 'style=""'
        self.assertEqual(table.caption_attrs, 'style=""')

    def test_no_attrs_but_caption(self):
        text = (
            '{|\n|+Food complements\n|-\n|Orange\n|Apple\n|-'
            '\n|Bread\n|Pie\n|-\n|Butter\n|Ice cream \n|}'
        )
        table = Table(text)
        self.assertEqual(table.caption, 'Food complements')
        self.assertEqual(table.caption_attrs, None)
        table.caption = ' C '
        self.assertEqual(table.string, text.replace('Food complements', ' C '))

    def test_attrs_and_caption(self):
        text = (
            '{| class="wikitable"\n'
            '|+ style="caption-side:bottom; color:#e76700;"|'
            '\'\'Food complements\'\'\n|-\n|Orange\n|Apple\n|-'
            '\n|Bread\n|Pie\n|-\n|Butter\n|Ice cream \n|}'
        )
        table = Table(text)
        self.assertEqual(table.caption, "''Food complements''")
        self.assertEqual(
            table.caption_attrs,
            ' style="caption-side:bottom; color:#e76700;"'
        )


class TableAttrs(unittest.TestCase):

    """Test the table_attrs method of the Table class."""

    def test_multiline_table(self):
        table = Table('{|s\n|a\n|}')
        self.assertEqual(table.table_attrs, 's')
        self.assertEqual(table.attrs, {'s': ''})
        self.assertEqual(table.has_attr('s'), True)
        self.assertEqual(table.has_attr('n'), False)
        self.assertEqual(table.get_attr('s'), '')
        table.table_attrs = 'class="wikitable"'
        self.assertEqual(
            repr(table), "Table('{|class=\"wikitable\"\\n|a\\n|}')"
        )
        self.assertEqual(table.get_attr('class'), 'wikitable')
        table.set_attr('class', 'sortable')
        self.assertEqual(table.attrs, {'class': 'sortable'})
        table.del_attr('class')
        self.assertEqual(table.attrs, {})

    def test_attr_contains_template_newline_invalid_chars(self):
        t = WikiText(
            '  {| class=wikitable |ب style="color: {{text| 1 =\n'
            'red}};"\n'
            '| cell\n'
            '|}\n'
        ).tables[0]
        self.assertEqual(t.get_attr('style'), 'color: {{text| 1 =\nred}};')


class Cells(unittest.TestCase):

    """Test the cells method of the table."""

    def test_cell_extraction(self):
        table = Table(
            '{|class=wikitable\n'
            '|| 1 | 1 || a | 2\n'
            '| 3 ||| 4\n'
            '|| 5\n'
            '! 6 !! a | 7\n'
            '!| 8 || 9\n'
            '|}'
        )
        cells = table.cells()
        self.assertEqual(len(cells), 1)
        self.assertEqual(len(cells[0]), 9)
        cell_string = (
            '\n|| 1 | 1 ',
            '|| a | 2',
            '\n| 3 ',
            '||| 4',
            '\n|| 5',
            '\n! 6 ',
            '!! a | 7',
            '\n!| 8 ',
            '|| 9',
        )
        for r in cells:
            for i, c in enumerate(r):
                self.assertEqual(c.string, cell_string[i])
        # Single cell
        self.assertEqual(table.cells(row=0, column=4).string, cell_string[4])
        # Column only
        self.assertEqual(table.cells(column=4)[0].string, cell_string[4])
        # Row only
        self.assertEqual(table.cells(row=0)[4].string, cell_string[4])

    def test_cell_spans(self):
        table = WikiText(
            '<!-- c -->{|class=wikitable\n| a \n|}'
        ).tables[0]
        self.assertEqual(table.cells(row=0, column=0).value, ' a ')

    def test_changing_cell_should_effect_the_table(self):
        t = Table('{|class=wikitable\n|a=b|c\n|}')
        c = t.cells(0, 0)
        c.value = 'v'
        self.assertEqual(c.value, 'v')
        c.set('a', 'b2')
        self.assertEqual(t.string, '{|class=wikitable\n|a="b2"|v\n|}')
        c.delete('a')
        self.assertEqual(t.string, '{|class=wikitable\n||v\n|}')
        c.set('c', 'd')
        self.assertEqual(t.string, '{|class=wikitable\n| c="d"|v\n|}')

    def test_cell_span_false(self):
        t = Table('{|class=wikitable\n|a=b|c\n|}')
        c = t.cells(span=False)
        self.assertEqual(len(c), 1)


if __name__ == '__main__':
    unittest.main()
