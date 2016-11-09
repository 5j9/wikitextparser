"""Test the Argument class."""


import unittest

import wikitextparser as wtp
from wikitextparser.table import Cell


class TableCell(unittest.TestCase):

    """Test the Cell class."""

    def test_basics(self):
        c = Cell('\n| a ')
        self.assertEqual(' a ', c.value)
        self.assertEqual(repr(c), 'Cell(\'\\n| a \')')
        self.assertEqual(c.attrs, {})
        # Use _cached_attrs
        self.assertEqual(c.attrs, {})
        c = Cell('\n! scope="col" | 00', True)
        self.assertTrue(c.has('scope'))
        self.assertEqual(c.get('scope'), 'col')
        # Inline _header cell
        c = Cell('|| 01 ', True)
        self.assertEqual(c.value, ' 01 ')
        # Inline non-_header cell
        c = Cell('|| 01 ')
        self.assertEqual(c.value, ' 01 ')
        # Set a new value
        c.value = '\na\na'
        self.assertEqual(c.value, '\na\na')

if __name__ == '__main__':
    unittest.main()
