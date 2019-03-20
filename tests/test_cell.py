"""Test the Argument class."""


import unittest

from wikitextparser import parse
# noinspection PyProtectedMember
from wikitextparser._table import Table, Cell


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
        self.assertTrue(c.has_attr('n'))
        self.assertEqual(c.get_attr('n'), 'v')

    def test_set_overwrite(self):
        c = Cell('\n! n=v | 00', True)
        # Set a new value for an existing attribute
        c.set_attr('n', 'w')
        # Set a new attribute
        c.set_attr('n2', 'v2')
        self.assertEqual(c.string, '\n! n="w" n2="v2" | 00')

    def test_newline_cell_no_attr_span_set(self):
        c = Cell('\n! 00', True)
        c.set_attr('n', 'v')
        self.assertEqual(c.string, '\n! n="v" | 00')
        c = Cell('\n! 00', True)
        c.set_attr('n', '')
        self.assertEqual(c.string, '\n! n | 00')

    def test_inline_cell_no_attr_span_set(self):
        c = Cell('!! 00', True)
        c.set_attr('n', 'v')
        self.assertEqual(c.string, '!! n="v" | 00')
        c = Cell('!! 00', True)
        c.set_attr('n', '')
        self.assertEqual(c.string, '!! n | 00')

    def test_space_or_quote_at_set_boundary(self):
        c = Cell('!!n=v|', True)
        c.set_attr('m', 'w')
        self.assertEqual(c.string, '!!n=v m="w"|')
        c = Cell('!! n=v |', True)
        c.set_attr('m', 'w')
        self.assertEqual(c.string, '!! n=v m="w" |')

    def test_delete(self):
        c = Cell('!!n=v|', True)
        c.del_attr('n')
        self.assertEqual(c.string, '!!|')
        c = Cell('!!n=v1 m=w n="v2"|', True)
        c.del_attr('n')
        self.assertEqual(c.string, '!!m=w |')
        # Test removing a non-existing attribute
        c.del_attr('n')

    def test_update_match_from_shadow(self):
        t = Table('{|class=wikitable\n|{{text|s}}\n|}')
        c = t.cells(0, 0)
        self.assertEqual(c.value, '{{text|s}}')
        t = c.templates[0]
        t.arguments[0].value = 't'
        self.assertEqual(c.value, '{{text|t}}')

    def test_cached_attrs_expiry(self):
        """_cached_attrs should expire when _match_cache is updated."""
        c = Cell('\n!v', True)
        # Fill _match_cache and _attrs_match_cache
        self.assertEqual(c.attrs, {})
        # Invalidate both caches
        c.insert(2, 'a|')
        # Update _match_cache
        self.assertEqual(c.value, 'v')
        # _attrs_match_cache should not be valid
        self.assertEqual(c.attrs, {'a': ''})

    def test_cell_attrs_using_table_match(self):
        c = parse('text\n{|\n!a=b| c\n|}').tables[0].cells(0, 0)
        self.assertEqual(c.attrs, {'a': 'b'})


if __name__ == '__main__':
    unittest.main()
