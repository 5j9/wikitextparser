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

    def test_set_target_to_none(self):
        # If the link is piped:
        wl = wtp.WikiLink('[[a|b]]')
        wl.text = None
        self.assertEqual('[[a]]', wl.string)
        # Without a pipe:
        wl = wtp.WikiLink('[[a]]')
        wl.text = None
        self.assertEqual('[[a]]', wl.string)

    def test_set_text(self):
        wl = wtp.WikiLink('[[A | B]]')
        wl.text = ' C '
        self.assertEqual('[[A | C ]]', wl.string)

    def test_set_text_when_there_is_no_text(self):
        wl = wtp.WikiLink('[[ A ]]')
        wl.text = ' C '
        self.assertEqual('[[ A | C ]]', wl.string)

    def test_dont_confuse_pipe_in_target_template_with_wl_pipe(self):
        wl = wtp.WikiLink('[[ {{text|target}} | text ]]')
        self.assertEqual(' {{text|target}} ', wl.target)
        self.assertEqual(' text ', wl.text)


if __name__ == '__main__':
    unittest.main()
