import unittest

from wikitextparser.tag import START_TAG_REGEX, END_TAG_REGEX


class Tag(unittest.TestCase):

    """Test the Tag module."""

    def test_start_tag_regex(self):
        self.assertEqual(
            START_TAG_REGEX.match('<a>').groupdict(),
            {'name': 'a', 'attr': None, 'quote': None,
             'start': '<a>', 'attr_name': None, 'empty_attr': None,
             'self_closing': None, 'uq_attr_val': None, 'q_attr_val': None}
        )
        self.assertEqual(
            START_TAG_REGEX.match('<a t>').groupdict(),
            {'name': 'a', 'attr': 't', 'quote': None,
             'start': '<a t>', 'attr_name': 't', 'empty_attr': '',
             'self_closing': None, 'uq_attr_val': None, 'q_attr_val': None}
        )
        self.assertEqual(
            START_TAG_REGEX.match('<input value=yes>').groupdict(),
            {'name': 'input', 'attr': 'value=yes', 'quote': None,
             'start': '<input value=yes>', 'attr_name': 'value',
             'empty_attr': None, 'self_closing': None, 'uq_attr_val': 'yes',
             'q_attr_val': None}
        )
        self.assertEqual(
            START_TAG_REGEX.match("<input type='checkbox'>").groupdict(),
            {'name': 'input', 'attr': "type='checkbox'", 'quote': "'",
             'start': "<input type='checkbox'>", 'attr_name': 'type',
             'empty_attr': None, 'self_closing': None, 'uq_attr_val': None,
             'q_attr_val': 'checkbox'}
        )
        self.assertEqual(
            START_TAG_REGEX.match('<s style=>').groupdict(),
            {'name': 's', 'attr': 'style=', 'quote': None,
             'start': '<s style=>', 'attr_name': 'style',
             'empty_attr': None, 'self_closing': None, 'uq_attr_val': '',
             'q_attr_val': None}
        )

    def test_end_tag_regex(self):
        self.assertEqual(
            END_TAG_REGEX.match('</p>').groupdict(),
            {'name': 'p', 'end': '</p>'}
        )

    @unittest.expectedFailure
    def test_basic(self):
        t = wtp.Tag('<ref>text</ref>')
        self.assertEqual(t.name, 'ref')
