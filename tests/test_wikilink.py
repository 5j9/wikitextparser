"""Test the wikilink.py module."""


from unittest import main, TestCase

from wikitextparser import WikiLink


class TestWikiLink(TestCase):

    """Test WikiLink functionalities."""

    def test_basic(self):
        wl = WikiLink('[[a]]')
        self.assertEqual("WikiLink('[[a]]')", repr(wl))

    def test_wikilink_target_text(self):
        wl = WikiLink('[[A | faf a\n\nfads]]')
        self.assertEqual('A ', wl.target)
        self.assertEqual(' faf a\n\nfads', wl.text)

    def test_set_target(self):
        wl = WikiLink('[[A | B]]')
        wl.target = ' C '
        self.assertEqual('[[ C | B]]', wl.string)
        wl = WikiLink('[[A]]')
        wl.target = ' C '
        self.assertEqual('[[ C ]]', wl.string)

    def test_set_target_to_none(self):
        # If the link is piped:
        wl = WikiLink('[[a|b]]')
        wl.text = None
        self.assertEqual('[[a]]', wl.string)
        # Without a pipe:
        wl = WikiLink('[[a]]')
        wl.text = None
        self.assertEqual('[[a]]', wl.string)

    def test_set_text(self):
        wl = WikiLink('[[A | B]]')
        wl.text = ' C '
        self.assertEqual('[[A | C ]]', wl.string)

    def test_set_text_when_there_is_no_text(self):
        wl = WikiLink('[[ A ]]')
        self.assertEqual(wl.text, None)
        wl.text = ' C '
        self.assertEqual('[[ A | C ]]', wl.string)

    def test_dont_confuse_pipe_in_target_template_with_wl_pipe(self):
        wl = WikiLink('[[ {{text|target}} | text ]]')
        self.assertEqual(' {{text|target}} ', wl.target)
        self.assertEqual(' text ', wl.text)

    def test_tricks(self):
        """Test unsupported wikilink tricks.

        Currently WikiLink.text returns the piped text literally and does not
        expand these tricks (which by the way do not always work as expected).
        """
        # Pipe trick
        # Note that pipe trick does not work in ref or gallery tags (T4700),
        # also not with links that have anchors, or edit summery links; see:
        # https://en.wikipedia.org/wiki/Help:Pipe_trick#Where_it_doesn't_work
        # https://en.wikipedia.org/wiki/Help:Pipe_trick
        self.assertEqual(WikiLink('[[L|]]').text, '')
        # Slash trick
        # https://en.wikipedia.org/wiki/Help:Pipe_trick#Slash_trick
        self.assertEqual(WikiLink('[[/Subpage/]]').text, None)
        # Reverse pipe trick (depends on page title)
        # https://en.wikipedia.org/wiki/Help:Pipe_trick#Reverse_pipe_trick
        self.assertEqual(WikiLink('[[|t]]').text, 't')


if __name__ == '__main__':
    main()
