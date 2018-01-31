"""Test the _config.py module."""

from unittest import main, TestCase

# noinspection PyProtectedMember
from wikitextparser._config import _pattern, _plant_trie, regex_pattern


class TestPlantTrie(TestCase):

    """Test the _plant_trie function."""

    def test_empty(self):
        self.assertEqual(_plant_trie(['']), {'': None})

    def test_alternatives(self):
        self.assertEqual(_plant_trie(
            ['a', 'b']), {'a': {'': None}, 'b': {'': None}})

    def test_string(self):
        self.assertEqual(_plant_trie(['ab']), {'a': {'b': {'': None}}})

    def test_a_and_optional_b(self):
        self.assertEqual(_plant_trie(
            ['ab', 'a']), {'a': {'b': {'': None}, '': None}})


class TestPattern(TestCase):

    """Test the _pattern function."""

    def test_empty(self):  # ['']
        self.assertEqual(_pattern({'': None}), '')

    def test_ab(self):  # ['ab']
        self.assertEqual(_pattern({'a': {'b': {'': None}}}), 'ab')

    def test_a_or_b(self):
        self.assertEqual(_pattern(  # ['a', 'b']
            {'a': {'': None}, 'b': {'': None}}), '[ba]')

    def test_optional_b(self):
        self.assertEqual(_pattern(  # ['ab', 'a']
            {'a': {'b': {'': None}, '': None}}), 'ab?+')

    def test_optional_bc(self):
        self.assertEqual(_pattern(  # ['abc', 'a']
            {'a': {'b': {'': None}, '': None}}), 'ab?+')

    def test_abc_or_dbc(self):
        self.assertEqual(
            _pattern(_plant_trie(['abc', 'dbc'])), '[da]bc',
        )

    def test_null_or_ab(self):
        self.assertEqual(
            _pattern({'': None, 'a': {'b': {'': None}}}), '(?:ab)?+',
        )

    def test_a_or_abc(self):
        self.assertEqual(
            _pattern(_plant_trie(['a', 'abc'])), 'a(?:bc)?+',
        )

    def test_a_or_abc_or_null(self):
        self.assertEqual(
            _pattern(_plant_trie(['', 'a', 'bc'])), '(?>bc|a)?+',
        )


class RegexPattern(TestCase):

    def test_regex_pattern(self):
        self.assertEqual(regex_pattern(['a', 'bc']), '(?>bc|a)')


if __name__ == '__main__':
    main()
