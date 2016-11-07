"""Test the Argument class."""


import unittest

import wikitextparser as wtp
from wikitextparser.table import Cell


class TableCell(unittest.TestCase):

    """Test the Cell class."""

    @unittest.expectedFailure
    def test_basic(self):
        c = Cell('\n| a ')
        self.assertEqual(' a ', c.value)
        self.assertEqual(repr(c), '\n| a ')


if __name__ == '__main__':
    unittest.main()
