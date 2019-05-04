"""Test the ExternalLink class."""


from unittest import TestCase, main

from wikitextparser import ExternalLink


class TestExternalLink(TestCase):
    """Test capturing of external links."""

    def test_repr(self):
        el = ExternalLink('HTTP://mediawiki.org')
        self.assertEqual(repr(el), "ExternalLink('HTTP://mediawiki.org')")

    def test_numberedmailto_change_none_to_empty(self):
        ae = self.assertEqual
        s = (
            '[mailto:'
            'info@example.org?Subject=URL%20Encoded%20Subject&body='
            'Body%20Textinfo]')
        el = ExternalLink(s)
        ae(s[1:-1], el.url)
        self.assertIsNone(el.text)
        ae(True, el.in_brackets)
        el.text = ''
        ae(el.string, s[:-1] + ' ]')

    def test_bare_link(self):
        ae = self.assertEqual
        el = ExternalLink('HTTP://mediawiki.org')
        ae('HTTP://mediawiki.org', el.url)
        self.assertIsNone(el.text)
        ae(False, el.in_brackets)

    def test_inbracket_with_text(self):
        ae = self.assertEqual
        el = ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
        ae('ftp://mediawiki.org', el.url)
        ae('mediawiki ftp', el.text)
        ae(True, el.in_brackets)

    def test_text_setter(self):
        ae = self.assertEqual
        el = ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
        el.text = 'a'
        ae('[ftp://mediawiki.org a]', el.string)

        del el.text
        el.text = 'b'
        ae('[ftp://mediawiki.org b]', el.string)

        el = ExternalLink('ftp://mediawiki.org')
        el.text = 'c'
        ae('[ftp://mediawiki.org c]', el.string)

    def test_text_delter(self):
        ae = self.assertEqual
        el = ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
        del el.text
        ae('[ftp://mediawiki.org]', el.string)

        del el.text
        ae('[ftp://mediawiki.org]', el.string)

        el = ExternalLink('ftp://mediawiki.org')
        del el.text
        ae('ftp://mediawiki.org', el.string)

    def test_url_setter(self):
        ae = self.assertEqual
        el = ExternalLink('[ftp://mediawiki.org mw]')
        el.url = 'https://www.mediawiki.org/'
        ae('[https://www.mediawiki.org/ mw]', el.string)

        el = ExternalLink('ftp://mediawiki.org')
        el.url = 'https://www.mediawiki.org/'
        ae('https://www.mediawiki.org/', el.string)

        el = ExternalLink('[ftp://mediawiki.org]')
        el.url = 'https://www.mediawiki.org/'
        ae('[https://www.mediawiki.org/]', el.string)

    def test_ending_with_less_than_sign(self):
        ae = self.assertEqual
        el = ExternalLink('[https://www.google.<com]')
        ae(el.url, 'https://www.google.')
        ae(el.text, '<com')


if __name__ == '__main__':
    main()
