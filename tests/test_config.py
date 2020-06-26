# noinspection PyProtectedMember
from wikitextparser._config import _pattern, _plant_trie, regex_pattern


# Test the _plant_trie function.
def test__plant_trie_empty():
    assert _plant_trie(['']) == {'': None}


def test_alternatives():
    assert _plant_trie(['a', 'b']) == {'a': {'': None}, 'b': {'': None}}


def test_string():
    assert _plant_trie(['ab']) == {'a': {'b': {'': None}}}


def test_a_and_optional_b():
    assert _plant_trie(['ab', 'a']) == {'a': {'b': {'': None}, '': None}}


# Test the _pattern function.
def test_pattern_empty():  # ['']
    assert _pattern({'': None}) == ''


def test_ab():  # ['ab']
    assert _pattern({'a': {'b': {'': None}}}) == 'ab'


def test_a_or_b():
    # ['a', 'b']
    assert _pattern({'a': {'': None}, 'b': {'': None}}) == '[ba]'


def test_optional_b():
    # ['ab', 'a']
    assert _pattern({'a': {'b': {'': None}, '': None}}) == 'ab?+'


def test_optional_bc():
    # ['abc', 'a']
    assert _pattern({'a': {'b': {'': None}, '': None}}) == 'ab?+'


def test_abc_or_dbc():
    assert _pattern(_plant_trie(['abc', 'dbc'])) == '[da]bc'


def test_null_or_ab():
    assert _pattern({'': None, 'a': {'b': {'': None}}}) == '(?:ab)?+'


def test_a_or_abc():
    assert _pattern(_plant_trie(['a', 'abc'])) == 'a(?:bc)?+'


def test_a_or_abc_or_null():
    assert _pattern(_plant_trie(['', 'a', 'bc'])) == '(?>bc|a)?+'


def test_regex_pattern():
    assert regex_pattern(['a', 'bc']) == b'(?>bc|a)'
