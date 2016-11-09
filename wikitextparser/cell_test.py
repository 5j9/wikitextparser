"""Test the Argument class."""


import unittest

from wikitextparser.table import Cell


class TableCell(unittest.TestCase):

    """Test the Cell class."""

    def test_value(self):
        c = Cell('\n| a ')
        self.assertEqual(' a ', c.value)
        self.assertEqual(repr(c), 'Cell(\'\\n| a \')')
        self.assertEqual(c.attrs, {})
        # Use _cached_attrs
        self.assertEqual(c.attrs, {})
        # Inline _header cell
        c = Cell('|| 01 ', True)
        self.assertEqual(c.value, ' 01 ')
        # Inline non-_header cell
        c = Cell('|| 01 ', False)
        self.assertEqual(c.value, ' 01 ')
        # Set a new value
        c.value = '\na\na'
        self.assertEqual(c.value, '\na\na')

    def test_has_get(self):
        c = Cell('\n! n="v" | 00', True)
        self.assertTrue(c.has('n'))
        self.assertEqual(c.get('n'), 'v')

    def test_set_overwrite(self):
        c = Cell('\n! n=v | 00', True)
        # Set a new value for an existing attribute
        c.set('n', 'w')
        # Set a new attribute
        c.set('n2', 'v2')
        self.assertEqual(c.string, '\n! n="w" n2="v2" | 00')

    def test_newline_cell_no_attr_span_set(self):
        c = Cell('\n! 00', True)
        c.set('n', 'v')
        self.assertEqual(c.string, '\n! n="v" | 00')
        c = Cell('\n! 00', True)
        c.set('n', '')
        self.assertEqual(c.string, '\n! n | 00')

    def test_inline_cell_no_attr_span_set(self):
        c = Cell('!! 00', True)
        c.set('n', 'v')
        self.assertEqual(c.string, '!! n="v" | 00')
        c = Cell('!! 00', True)
        c.set('n', '')
        self.assertEqual(c.string, '!! n | 00')

    def test_space_or_quote_at_set_boundary(self):
        c = Cell('!!n=v|', True)
        c.set('m', 'w')
        self.assertEqual(c.string, '!!n=v m="w"|')
        c = Cell('!! n=v |', True)
        c.set('m', 'w')
        self.assertEqual(c.string, '!! n=v m="w" |')


if __name__ == '__main__':
    unittest.main()
