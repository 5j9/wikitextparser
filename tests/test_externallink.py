"""Test the ExternalLink class."""


import unittest

from wikitextparser import ExternalLink


class TestExternalLink(unittest.TestCase):
    """Test capturing of external links."""

    def test_repr(self):
        el = ExternalLink('HTTP://mediawiki.org')
        self.assertEqual(repr(el), "ExternalLink('HTTP://mediawiki.org')")

    def test_numberedmailto_change_none_to_empty(self):
        s = (
            '[mailto:'
            'info@example.org?Subject=URL%20Encoded%20Subject&body='
            'Body%20Textinfo]'
        )
        el = ExternalLink(s)
        self.assertEqual(s[1:-1], el.url)
        self.assertIsNone(el.text)
        self.assertEqual(True, el.in_brackets)
        el.text = ''
        self.assertEqual(el.string, s[:-1] + ' ]')

    def test_bare_link(self):
        el = ExternalLink('HTTP://mediawiki.org')
        self.assertEqual('HTTP://mediawiki.org', el.url)
        self.assertIsNone(el.text)
        self.assertEqual(False, el.in_brackets)

    def test_inbracket_with_text(self):
        el = ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
        self.assertEqual('ftp://mediawiki.org', el.url)
        self.assertEqual('mediawiki ftp', el.text)
        self.assertEqual(True, el.in_brackets)

    def test_set_text(self):
        el = ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
        el.text = 'mwftp'
        self.assertEqual('[ftp://mediawiki.org mwftp]', el.string)
        el = ExternalLink('ftp://mediawiki.org')
        el.text = 'mwftp'
        self.assertEqual('[ftp://mediawiki.org mwftp]', el.string)

    def test_set_url(self):
        el = ExternalLink('[ftp://mediawiki.org mw]')
        el.url = 'https://www.mediawiki.org/'
        self.assertEqual('[https://www.mediawiki.org/ mw]', el.string)
        el = ExternalLink('ftp://mediawiki.org')
        el.url = 'https://www.mediawiki.org/'
        self.assertEqual('https://www.mediawiki.org/', el.string)
        el = ExternalLink('[ftp://mediawiki.org]')
        el.url = 'https://www.mediawiki.org/'
        self.assertEqual('[https://www.mediawiki.org/]', el.string)

    def test_ending_with_less_than_sign(self):
        el = ExternalLink('[https://www.google.<com]')
        self.assertEqual(el.url, 'https://www.google.')
        self.assertEqual(el.text, '<com')


if __name__ == '__main__':
    unittest.main()
