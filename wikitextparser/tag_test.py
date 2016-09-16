import unittest

import wikitextparser as wtp


class Tag(unittest.TestCase):

    """Test the Tag class."""

    @unittest.expectedFailure
    def test_basic(self):
        t = wtp.Tag('<ref>text</ref>')
        self.assertEqual(t.name, 'ref')
