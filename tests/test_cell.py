from wikitextparser import parse

# noinspection PyProtectedMember
from wikitextparser._table import Cell, Table


def test_value():
    c = Cell('\n| a ')
    assert ' a ' == c.value
    assert repr(c) == "Cell('\\n| a ')"
    assert c.attrs == {}
    # Use _cached_attrs
    assert c.attrs == {}
    # Inline _header cell
    c = Cell('|| 01 ', True)
    assert c.value == ' 01 '
    # Inline non-_header cell
    c = Cell('|| 01 ', False)
    assert c.value == ' 01 '
    # Set a new value
    c.value = '\na\na'
    assert c.value == '\na\na'


def test_has_get():
    c = Cell('\n! n="v" | 00', True)
    assert c.has_attr('n')
    assert c.get_attr('n') == 'v'


def test_set_overwrite():
    c = Cell('\n! n=v | 00', True)
    # Set a new value for an existing attribute
    c.set_attr('n', 'w')
    # Set a new attribute
    c.set_attr('n2', 'v2')
    assert c.string == '\n! n="w" n2="v2" | 00'


def test_newline_cell_no_attr_span_set():
    c = Cell('\n! 00', True)
    c.set_attr('n', 'v')
    assert c.string == '\n! n="v" | 00'
    c = Cell('\n! 00', True)
    c.set_attr('n', '')
    assert c.string == '\n! n | 00'


def test_inline_cell_no_attr_span_set():
    c = Cell('!! 00', True)
    c.set_attr('n', 'v')
    assert c.string == '!! n="v" | 00'
    c = Cell('!! 00', True)
    c.set_attr('n', '')
    assert c.string == '!! n | 00'


def test_space_or_quote_at_set_boundary():
    c = Cell('!!n=v|', True)
    c.set_attr('m', 'w')
    assert c.string == '!!n=v m="w"|'
    c = Cell('!! n=v |', True)
    c.set_attr('m', 'w')
    assert c.string == '!! n=v m="w" |'


def test_delete():
    c = Cell('!!n=v|', True)
    c.del_attr('n')
    assert c.string == '!!|'
    c = Cell('!!n=v1 m=w n="v2"|', True)
    c.del_attr('n')
    assert c.string == '!! m=w|'
    # Test removing a non-existing attribute
    c.del_attr('n')


def test_update_match_from_shadow():
    t = Table('{|class=wikitable\n|{{text|s}}\n|}')
    c = t.cells(0, 0)
    assert c is not None
    assert c.value == '{{text|s}}'
    t = c.templates[0]
    t.arguments[0].value = 't'
    assert c.value == '{{text|t}}'


def test_cached_attrs_expiry():
    """_cached_attrs should expire when _match_cache is updated."""
    c = Cell('\n!v', True)
    # Fill _match_cache and _attrs_match_cache
    assert c.attrs == {}
    # Invalidate both caches
    c.insert(2, 'a|')
    # Update _match_cache
    assert c.value == 'v'
    # _attrs_match_cache should not be valid
    assert c.attrs == {'a': ''}


def test_cell_attrs_using_table_match():
    c = parse('text\n{|\n!a=b| c\n|}').tables[0].cells(0, 0)
    assert c is not None
    assert c.attrs == {'a': 'b'}
