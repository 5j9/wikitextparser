"""Test the functionalities of table.py module."""
'''Todo:
addrow([], -1)
getrow(n)
addcol([], -1)
getcol(n)
rows
caption

shitfrow(n,m)
shiftcol(n,m)

sort?
transpose?
'''


import sys
import unittest

sys.path.insert(0, '..')
from wikitextparser import wikitextparser as wtp


class Rows(unittest.TestCase):

    """Test the rows method of the table class."""

    def test_each_row_on_a_newline(self):
        table = wtp.Table(
            '{|\n|Orange\n|Apple\n|-\n|Bread\n|Pie\n|-'
            '\n|Butter\n|Ice cream \n|}'
        )
        self.assertEqual(
            table.rows,
            [['Orange', 'Apple'], ['Bread', 'Pie'], ['Butter', 'Ice cream']],
        )

    def test_with_optional_rowseprator_on_first_row(self):
        table = wtp.Table(
            '{| class=wikitable | g\n |- 132131 |||\n  | a | b\n |-\n  | c\n|}'
        )
        self.assertEqual(
            table.rows,
            [['b'], ['c']],
        )

    def test_all_rows_are_on_a_single_line(self):
        table = wtp.Table(
            '{|\n|a||b||c\n|-\n|d||e||f\n|-\n|g||h||i\n|}'
        )
        self.assertEqual(
            table.rows,
            [['a', 'b', 'c'], ['d', 'e', 'f'], ['g', 'h', 'i']],
        )

    def test_extra_spaces_have_no_effect(self):
        table = wtp.Table(
            '{|\n|  Orange    ||   Apple   ||   more\n|-\n'
            '|   Bread    ||   Pie     ||   more\n|-\n'
            '|   Butter   || Ice cream ||  and more\n|}'
        )
        self.assertEqual(
            table.rows,
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
            table.rows,
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
        self.assertEqual(table.rows, [['multi\nline', '\n 1']])

    def test_with_headers(self):
        table = wtp.Table(
            '{|\n! style="text-align:left;"| Item\n! Amount\n! Cost\n|-\n'
            '|Orange\n|10\n|7.00\n|-\n|Bread\n|4\n|3.00\n|-\n'
            '|Butter\n|1\n|5.00\n|-\n!Total\n|\n|15.00\n|}'
        )
        self.assertEqual(
            table.rows, [
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
            table.rows,
            [['Orange', 'Apple'], ['Bread', 'Pie'], ['Butter', 'Ice cream']],
        )

    def test_second_caption_is_ignored(self):
        table = wtp.Table('{|\n  |+ c1\n  |+ c2\n|-\n|1\n|2\n|}')
        self.assertEqual(table.rows, [['1', '2']])

    def test_unneeded_newline_after_table_start(self):
        table = wtp.Table('{|\n\n|-\n|c1\n|c2\n|}')
        self.assertEqual(table.rows, [['c1', 'c2']])

    def test_text_after_tablestart_is_not_actually_inside_the_table(self):
        table = wtp.Table('{|\n  text\n|-\n|c1\n|c2\n|}')
        self.assertEqual(table.rows, [['c1', 'c2']])

    def test_empty_table(self):
        table = wtp.Table('{||}')
        self.assertEqual(table.rows, [])

    def test_empty_cell(self):
        table = wtp.Table('{|class=wikitable\n||a || || c\n|}')
        self.assertEqual(table.rows, [['a', '', 'c']])

    def test_pipe_as_text(self):
        table = wtp.Table('{|class=wikitable\n||a | || c\n|}')
        self.assertEqual(table.rows, [['a |', 'c']])

    def test_meaningless_rowsep(self):
        table = wtp.Table('{|class=wikitable\n||a || || c\n|-\n|}')
        self.assertEqual(table.rows, [['a', '', 'c']])

    def test_template_inside_table(self):
        table = wtp.Table('{|class=wikitable\n|-\n|{{text|a}}\n|}')
        self.assertEqual(table.rows, [['{{text|a}}']])

    def test_only_pipes_can_seprate_attributes(self):
        """According to the note at mw:Help:Tables#Table_headers."""
        table = wtp.Table(
            '{|class=wikitable\n! style="text-align:left;"! '
            'Item\n! Amount\n! Cost\n|}'
        )
        self.assertEqual(table.rows, [
            ['style="text-align:left;"! Item', 'Amount', 'Cost']
        ])
        table = wtp.Table(
            '{|class=wikitable\n! style="text-align:left;"| '
            'Item\n! Amount\n! Cost\n|}'
        )
        self.assertEqual(table.rows, [
            ['Item', 'Amount', 'Cost']
        ])

    def test_double_exclamation_marks_are_valid_on_header_rows(self):
        table = wtp.Table('{|class=wikitable\n!a!!b!!c\n|}')
        self.assertEqual(table.rows, [['a', 'b', 'c']])

    def test_double_exclamation_marks_are_valid_only_on_header_rows(self):
        # Actually I'm not sure about this in general.
        table = wtp.Table('{|class=wikitable\n|a!!b!!c\n|}')
        self.assertEqual(table.rows, [['a!!b!!c']])
        

    def test_caption_in_row_is_treated_as_pipe_and_plut(self):
        table = wtp.Table('{|class=wikitable\n|a|+b||c\n|}')
        self.assertEqual(table.rows, [['+b', 'c']])
        
    def test_odd_case1(self):
        table = wtp.Table(
            '{|class=wikitable\n  [[a]]\n |+ cp1\ncp1\n! h1 '
            '||+ h2\n|-\n! h3 !|+ h4\n|-\n! h5 |!+ h6\n'
            '|-\n|c1\n|+hod [[that]]\n\ntext\n|c2\n|}'
        )
        self.assertEqual(table.rows, [
            ['h1', '+ h2'],
            ['+ h4'],
            ['!+ h6'],
            ['c1', 'c2']
        ])

  
if __name__ == '__main__':
    unittest.main()
