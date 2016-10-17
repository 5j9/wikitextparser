"""Test the ExternalLink class."""


import unittest

import wikitextparser as wtp


class ExternalLink(unittest.TestCase):
    """Test capturing of external links."""

    def test_repr(self):
        el = wtp.ExternalLink('HTTP://mediawiki.org')
        self.assertEqual(repr(el), "ExternalLink('HTTP://mediawiki.org')")

    def test_numberedmailto(self):
        s = (
            '[mailto:'
            'info@example.org?Subject=URL%20Encoded%20Subject&body='
            'Body%20Textinfo]'
        )
        el = wtp.ExternalLink(s)
        self.assertEqual(s[1:-1], el.url)
        self.assertEqual('', el.text)
        self.assertEqual(True, el.in_brackets)

    def test_bare_link(self):
        el = wtp.ExternalLink('HTTP://mediawiki.org')
        self.assertEqual('HTTP://mediawiki.org', el.url)
        self.assertEqual('HTTP://mediawiki.org', el.text)
        self.assertEqual(False, el.in_brackets)

    def test_inbracket_with_text(self):
        el = wtp.ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
        self.assertEqual('ftp://mediawiki.org', el.url)
        self.assertEqual('mediawiki ftp', el.text)
        self.assertEqual(True, el.in_brackets)

    def test_set_text(self):
        el = wtp.ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
        el.text = 'mwftp'
        self.assertEqual('[ftp://mediawiki.org mwftp]', el.string)
        el = wtp.ExternalLink('ftp://mediawiki.org')
        el.text = 'mwftp'
        self.assertEqual('[ftp://mediawiki.org mwftp]', el.string)

    def test_set_url(self):
        el = wtp.ExternalLink('[ftp://mediawiki.org mw]')
        el.url = 'https://www.mediawiki.org/'
        self.assertEqual('[https://www.mediawiki.org/ mw]', el.string)
        el = wtp.ExternalLink('ftp://mediawiki.org')
        el.url = 'https://www.mediawiki.org/'
        self.assertEqual('https://www.mediawiki.org/', el.string)
        el = wtp.ExternalLink('[ftp://mediawiki.org]')
        el.url = 'https://www.mediawiki.org/'
        self.assertEqual('[https://www.mediawiki.org/]', el.string)


if __name__ == '__main__':
    unittest.main()
