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

import wikitextparser as wtp


class GetData(unittest.TestCase):

    """Test the GetData method of the table class."""

    def test_each_row_on_a_newline(self):
        table = wtp.Table(
            '{|\n|Orange\n|Apple\n|-\n|Bread\n|Pie\n|-'
            '\n|Butter\n|Ice cream \n|}'
        )
        self.assertEqual(
            table.getdata(),
            [['Orange', 'Apple'], ['Bread', 'Pie'], ['Butter', 'Ice cream']],
        )

    def test_with_optional_rowseprator_on_first_row(self):
        table = wtp.Table(
            '{| class=wikitable | g\n'
            ' |- 132131 |||\n'
            '  | a | b\n'
            ' |-\n'
            '  | c\n'
            '|}'
        )
        self.assertEqual(
            table.getdata(),
            [['b'], ['c']],
        )

    def test_all_rows_are_on_a_single_line(self):
        table = wtp.Table(
            '{|\n'
            '|a||b||c\n'
            '|-\n'
            '|d||e||f\n'
            '|-\n'
            '|g||h||i\n'
            '|}'
        )
        self.assertEqual(
            table.getdata(),
            [['a', 'b', 'c'], ['d', 'e', 'f'], ['g', 'h', 'i']],
        )

    def test_extra_spaces_have_no_effect(self):
        table = wtp.Table(
            '{|\n|  Orange    ||   Apple   ||   more\n|-\n'
            '|   Bread    ||   Pie     ||   more\n|-\n'
            '|   Butter   || Ice cream ||  and more\n|}'
        )
        self.assertEqual(
            table.getdata(),
            [
                ['Orange', 'Apple', 'more'],
                ['Bread', 'Pie', 'more'],
                ['Butter', 'Ice cream', 'and more']],
        )

    def test_longer_text_and_only_rstrip(self):
        table = wtp.Table(
            '{|\n|multi\nline\ntext. \n\n2nd paragraph. \n|'
            '\n* ulli1\n* ulli2\n* ulli3\n|}'
        )
        self.assertEqual(
            table.getdata(),
            [
                [
                    'multi\nline\ntext. \n\n2nd paragraph.',
                    '\n* ulli1\n* ulli2\n* ulli3'
                ]
            ]
        )

    def test_doublepipe_multiline(self):
        table = wtp.Table(
            '{|\n|| multi\nline\n||\n 1\n|}'
        )
        self.assertEqual(table.getdata(), [['multi\nline', '\n 1']])

    def test_with_headers(self):
        table = wtp.Table(
            '{|\n! style="text-align:left;"| Item\n! Amount\n! Cost\n|-\n'
            '|Orange\n|10\n|7.00\n|-\n|Bread\n|4\n|3.00\n|-\n'
            '|Butter\n|1\n|5.00\n|-\n!Total\n|\n|15.00\n|}'
        )
        self.assertEqual(
            table.getdata(), [
                ['Item', 'Amount', 'Cost'],
                ['Orange', '10', '7.00'],
                ['Bread', '4', '3.00'],
                ['Butter', '1', '5.00'],
                ['Total', '', '15.00'],
            ]
        )

    def test_with_caption(self):
        table = wtp.Table(
            '{|\n|+Food complements\n|-\n|Orange\n|Apple\n|-\n'
            '|Bread\n|Pie\n|-\n|Butter\n|Ice cream \n|}'
        )
        self.assertEqual(
            table.getdata(),
            [['Orange', 'Apple'], ['Bread', 'Pie'], ['Butter', 'Ice cream']],
        )

    def test_with_caption_attrs(self):
        table = wtp.Table(
            '{|class=wikitable\n'
            '|+ sal | no\n'
            '|a \n'
            '|}'
        )
        self.assertEqual(table.getdata(), [['a']])

    def test_second_caption_is_ignored(self):
        table = wtp.Table(
            '{|\n'
            '  |+ c1\n'
            '  |+ c2\n'
            '|-\n'
            '|1\n'
            '|2\n'
            '|}')
        self.assertEqual(table.getdata(), [['1', '2']])

    def test_unneeded_newline_after_table_start(self):
        table = wtp.Table('{|\n\n|-\n|c1\n|c2\n|}')
        self.assertEqual(table.getdata(), [['c1', 'c2']])

    def test_text_after_tablestart_is_not_actually_inside_the_table(self):
        table = wtp.Table(
            '{|\n'
            '  text\n'
            '|-\n'
            '|c1\n'
            '|c2\n'
            '|}'
        )
        self.assertEqual(table.getdata(), [['c1', 'c2']])

    def test_empty_table(self):
        table = wtp.Table('{|class=wikitable\n|}')
        self.assertEqual(table.getdata(), [])

    def test_empty_cell(self):
        table = wtp.Table('{|class=wikitable\n||a || || c\n|}')
        self.assertEqual(table.getdata(), [['a', '', 'c']])

    def test_pipe_as_text(self):
        table = wtp.Table('{|class=wikitable\n||a | || c\n|}')
        self.assertEqual(table.getdata(), [['a |', 'c']])

    def test_meaningless_rowsep(self):
        table = wtp.Table('{|class=wikitable\n||a || || c\n|-\n|}')
        self.assertEqual(table.getdata(), [['a', '', 'c']])

    def test_template_inside_table(self):
        table = wtp.Table('{|class=wikitable\n|-\n|{{text|a}}\n|}')
        self.assertEqual(table.getdata(), [['{{text|a}}']])

    def test_only_pipes_can_seprate_attributes(self):
        """According to the note at mw:Help:Tables#Table_headers."""
        table = wtp.Table(
            '{|class=wikitable\n! style="text-align:left;"! '
            'Item\n! Amount\n! Cost\n|}'
        )
        self.assertEqual(table.getdata(), [
            ['style="text-align:left;"! Item', 'Amount', 'Cost']
        ])
        table = wtp.Table(
            '{|class=wikitable\n! style="text-align:left;"| '
            'Item\n! Amount\n! Cost\n|}'
        )
        self.assertEqual(table.getdata(), [
            ['Item', 'Amount', 'Cost']
        ])

    def test_double_exclamation_marks_are_valid_on_header_rows(self):
        table = wtp.Table('{|class=wikitable\n!a!!b!!c\n|}')
        self.assertEqual(table.getdata(), [['a', 'b', 'c']])

    def test_double_exclamation_marks_are_valid_only_on_header_rows(self):
        # Actually I'm not sure about this in general.
        table = wtp.Table('{|class=wikitable\n|a!!b!!c\n|}')
        self.assertEqual(table.getdata(), [['a!!b!!c']])

    def test_caption_in_row_is_treated_as_pipe_and_plut(self):
        table = wtp.Table('{|class=wikitable\n|a|+b||c\n|}')
        self.assertEqual(table.getdata(), [['+b', 'c']])

    def test_odd_case1(self):
        table = wtp.Table(
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
        self.assertEqual(table.getdata(span=False), [
            ['h1', '+ h2'],
            ['+ h4'],
            ['!+ h6'],
            ['c1', 'c2']
        ])

    def test_colspan_and_rowspan_and_span_false(self):
        table = wtp.Table(
            '{| class="wikitable"\n!colspan= 6 |11\n|-\n'
            '|rowspan="2"|21\n|22\n|23\n|24\n|colspan="2"|25\n|-\n'
            '|31\n|colspan="2"|32\n|33\n|34\n|}'
        )
        self.assertEqual(table.getdata(span=False), [
            ['11'],
            ['21', '22', '23', '24', '25'],
            ['31', '32', '33', '34'],
        ])

    def test_colspan_and_rowspan_and_span_true(self):
        table = wtp.Table(
            '{| class="wikitable"\n!colspan= 6 |11\n|-\n'
            '|rowspan="2"|21\n|22\n|23\n|24\n  |colspan="2"|25\n|-\n'
            '|31\n|colspan="2"|32\n|33\n|34\n|}'
        )
        self.assertEqual(table.getdata(span=True), [
            ['11', '11', '11', '11', '11', '11'],
            ['21', '22', '23', '24', '25', '25'],
            ['21', '31', '32', '32', '33', '34'],
        ])

    def test_inline_colspan_and_rowspan(self):
        table = wtp.Table(
            '{| class=wikitable\n'
            ' !a !! b !!  c !! rowspan = 2 | d \n'
            ' |- \n'
            ' | e || colspan = "2"| f\n'
            '|}'
        )
        self.assertEqual(table.getdata(span=True), [
            ['a', 'b', 'c', 'd'],
            ['e', 'f', 'f', 'd']
        ])

    def test_growing_downward_growing_cells(self):
        table = wtp.Table(
            '{|class=wikitable\n'
            '| a || rowspan=0 | b\n'
            '|-\n'
            '| c\n'
            '|}'
        )
        self.assertEqual(table.getdata(span=True), [
            ['a', 'b'],
            ['c', 'b'],
        ])

    def test_colspan_0(self):
        table = wtp.Table(
            '{|class=wikitable\n'
            '| colspan=0 | a || b\n'
            '|-\n'
            '| c || d\n'
            '|}'
        )
        self.assertEqual(table.getdata(span=True), [
            ['a', 'b'],
            ['c', 'd'],
        ])

    def test_ending_row_group(self):
        table = wtp.Table(
            '{|class=wikitable\n'
            '| rowspan = 3 | a || b\n'
            '|-\n'
            '| c\n'
            '|}'
        )
        self.assertEqual(table.getdata(span=True), [
            ['a', 'b'],
            ['a', 'c'],
            ['a', None],
        ])

    def test_ending_row_group_and_rowspan_0(self):
        table = wtp.Table(
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


class GetRowData(unittest.TestCase):

    """Test the getrdata method of the Table class."""

    def test_second_of_three(self):
        table = wtp.Table('{|\n|a||b||c\n|-\n|d||e||f\n|-\n|g||h||i\n|}')
        self.assertEqual(table.getrdata(1), ['d', 'e', 'f'])


class GetColData(unittest.TestCase):

    """Test the getcdata method of the Table class."""

    def test_second_of_three(self):
        table = wtp.Table('{|\n|a||b||c\n|-\n|d||e||f\n|-\n|g||h||i\n|}')
        self.assertEqual(table.getcdata(1), ['b', 'e', 'h'])


class Caption(unittest.TestCase):

    """Test the caption and caption_attrs methods."""

    def test_no_caption(self):
        table = wtp.Table('{| class="wikitable"\n|a\n|+ ignore\n|}')
        self.assertEqual(table.caption, None)
        self.assertEqual(table.caption_attrs, None)
        table.caption = 'foo'
        self.assertEqual(
            table.string,
            '{| class="wikitable"\n|+foo\n|a\n|+ ignore\n|}'
        )

    def test_replace_caption_attrs(self):
        table = wtp.Table('{|class="wikitable"\n|+old|cap\n|}')
        table.caption_attrs = 'new'
        self.assertEqual(table.caption_attrs, 'new')

    def test_set_caption_attrs_before_cap(self):
        table = wtp.Table('{| class="wikitable"\n|a\n|+ ignore\n|}')
        table.caption_attrs = 'style=""'
        self.assertEqual(table.caption_attrs, 'style=""')

    def test_no_attrs_but_caption(self):
        text = (
            '{|\n|+Food complements\n|-\n|Orange\n|Apple\n|-'
            '\n|Bread\n|Pie\n|-\n|Butter\n|Ice cream \n|}'
        )
        table = wtp.Table(text)
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
        table = wtp.Table(text)
        self.assertEqual(table.caption, "''Food complements''")
        self.assertEqual(
            table.caption_attrs,
            ' style="caption-side:bottom; color:#e76700;"'
        )


class TableAttrs(unittest.TestCase):

    """Test the table_attrs method of the Table class."""

    def test_multiline_table(self):
        table = wtp.Table('{|s\n|a\n|}')
        self.assertEqual(table.table_attrs, 's')
        table.table_attrs = 'class="wikitable"'
        self.assertEqual(
            repr(table), "Table('{|class=\"wikitable\"\\n|a\\n|}')"
        )


if __name__ == '__main__':
    unittest.main()
