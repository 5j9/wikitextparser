"""Test the functionalities of table.py module."""

import sys
import unittest

sys.path.insert(0, '..')
from wikitextparser import wikitextparser as wtp


class WikiLink(unittest.TestCase):

    """Test WikiLink functionalities."""

    def test_wikilink_target_text(self):
        wl = wtp.WikiLink('[[A | faf a\n\nfads]]')
        self.assertEqual('A ', wl.target)
        self.assertEqual(' faf a\n\nfads', wl.text)

    def test_set_target(self):
        wl = wtp.WikiLink('[[A | B]]')
        wl.target = ' C '
        self.assertEqual('[[ C | B]]', wl.string)
        wl = wtp.WikiLink('[[A]]')
        wl.target = ' C '
        self.assertEqual('[[ C ]]', wl.string)

    def test_set_text(self):
        wl = wtp.WikiLink('[[A | B]]')
        wl.text = ' C '
        self.assertEqual('[[A | C ]]', wl.string)
        

if __name__ == '__main__':
    unittest.main()
