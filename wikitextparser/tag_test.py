"""Test the tag module."""


import unittest

import wikitextparser as wtp
from wikitextparser.tag import START_TAG_REGEX, END_TAG_REGEX, TAG_REGEX


class Tag(unittest.TestCase):

    """Test the Tag module."""

    def test_start_tag_regex(self):
        self.assertEqual(
            START_TAG_REGEX.match('<a>').groupdict(),
            {'name': 'a', 'attr': None, 'quote': None,
             'start': '<a>', 'attr_name': None,
             'self_closing': None, 'attr_value': None,}
        )
        self.assertEqual(
            START_TAG_REGEX.match('<a t>').groupdict(),
            {'name': 'a', 'attr': ' t', 'quote': None,
             'start': '<a t>', 'attr_name': 't', 'attr_value': '',
             'self_closing': None}
        )
        self.assertEqual(
            START_TAG_REGEX.match('<input value=yes>').groupdict(),
            {'name': 'input', 'attr': ' value=yes', 'quote': None,
             'start': '<input value=yes>', 'attr_name': 'value',
             'attr_value': 'yes', 'self_closing': None}
        )
        self.assertEqual(
            START_TAG_REGEX.match("<input type='checkbox'>").groupdict(),
            {'name': 'input', 'attr': " type='checkbox'", 'quote': "'",
             'start': "<input type='checkbox'>", 'attr_name': 'type',
             'attr_value': 'checkbox', 'self_closing': None}
        )
        # This is not standard HTML5, but could be useful to have.
        # self.assertEqual(
        #     START_TAG_REGEX.match('<s style=>').groupdict(),
        #     {'name': 's', 'attr': 'style=', 'quote': None,
        #      'start': '<s style=>', 'attr_name': 'style', 'attr_value': ''
        #      'self_closing': None}
        # )
        self.assertEqual(
            START_TAG_REGEX.match("<t a1=v1 a2=v2>").capturesdict(),
            {'attr_name': ['a1', 'a2'], 'start': ['<t a1=v1 a2=v2>'],
             'attr': [' a1=v1', ' a2=v2'], 'quote': [],
             'attr_value': ['v1', 'v2'], 'self_closing': [], 'name': ['t']}
        )

    def test_end_tag_regex(self):
        self.assertEqual(
            END_TAG_REGEX.match('</p>').groupdict(),
            {'name': 'p', 'end': '</p>'}
        )

    @unittest.expectedFailure
    def test_tag_content_cannot_contain_another_start(self):
        """Checking for such situations is not currently required."""
        self.assertEqual(
            TAG_REGEX.search('<a><a>c</a></a>').group(),
            '<a>c</a>'
        )

    def test_tag_name(self):
        t = wtp.Tag('<t>c</t>')
        self.assertEqual(t.name, 't')
        t.name = 'a'
        self.assertEqual(t.string, '<a>c</a>')
        t = wtp.Tag('<t/>')
        self.assertEqual(t.name, 't')
        t.name = 'n'
        self.assertEqual(t.string, '<n/>')

    def test_tag_contents(self):
        t = wtp.Tag('<t>\nc\n</t>')
        self.assertEqual(t.contents, '\nc\n')
        t.contents = 'n'
        self.assertEqual(t.string, '<t>n</t>')
        t = wtp.Tag('<t></t>')
        self.assertEqual(t.contents, '')
        t.contents = 'n'
        self.assertEqual(t.string, '<t>n</t>')
        t = wtp.Tag('<t/>')
        self.assertEqual(t.contents, None)
        t.contents = 'n'
        self.assertEqual(t.string, '<t>n</t>')

    def test_get_attr_value(self):
        t = wtp.Tag('<t n1=v1 n2=v2 n1=v3>c</t>')
        self.assertEqual(t['n1'], 'v3')
        self.assertEqual(t['n2'], 'v2')

    def test_set_attr_value(self):
        t = wtp.Tag('<t n1=v1 n2=v2 n1=v3>c</t>')
        t['n1'] = 'v4'
        t['n2'] = 'v5'
        self.assertEqual(t.string, '<t n1=v1 n2=v5 n1=v4>c</t>')
        t['id'] = '1'
        self.assertEqual(t.string, '<t n1=v1 n2=v5 n1=v4 id="1">c</t>')

    def test_attr_deletion(self):
        t = wtp.Tag('<t n1=v1 n2=v2 n1=v3>c</t>')
        del t['n1']
        self.assertEqual(t.string, '<t n2=v2>c</t>')
