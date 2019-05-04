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
        del wl.target
        self.assertEqual('[[ B]]', wl.string)
        del wl.target
        self.assertEqual('[[]]', wl.string)
        wl = WikiLink('[[A]]')
        wl.target = ' C '
        self.assertEqual('[[ C ]]', wl.string)

    def test_text_settter(self):
        ae = self.assertEqual
        wl = WikiLink('[[A | B]]')
        wl.text = ' C '
        ae('[[A | C ]]', wl.string)
        with self.assertWarns(DeprecationWarning):
            wl.text = None
        ae('[[A ]]', wl.string)
        with self.assertWarns(DeprecationWarning):
            wl.text = None
        ae('[[A ]]', wl.string)

    def test_test_deleter(self):
        ae = self.assertEqual
        wl = WikiLink('[[t|x]]')
        del wl.text
        ae(wl.string, '[[t]]')
        del wl.text
        ae(wl.string, '[[t]]')

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

    def test_fragment_getter(self):
        ae = self.assertEqual
        ae(WikiLink('[[a<!--#1-->#<!--#2-->f|x]]').fragment, '<!--#2-->f')
        ae(WikiLink('[[a<!--#1-->#<!--#2-->f]]').fragment, '<!--#2-->f')
        ae(WikiLink('[[{{#if:||t}}#{{#if:||s}}|x]]').fragment, '{{#if:||s}}')
        ae(WikiLink('[[{{#if:||t}}#{{#if:||s}}]]').fragment, '{{#if:||s}}')
        ae(WikiLink('[[t|x]]').fragment, None)
        ae(WikiLink('[[t]]').fragment, None)
        ae(WikiLink('[[t|#]]').fragment, None)
        ae(WikiLink('[[t#|x]]').fragment, '')
        ae(WikiLink('[[t#]]').fragment, '')

    def test_fragment_setter(self):
        ae = self.assertEqual
        # no frag, no pipe
        wl = WikiLink('[[a]]')
        wl.fragment = 'b'
        ae(wl.string, '[[a#b]]')

        # frag, no pipe
        wl.fragment = 'c'
        ae(wl.string, '[[a#c]]')

        # frag, pipe
        wl.text = ''  # [[a#c|]]
        wl.fragment = 'd'
        ae(wl.string, '[[a#d|]]')

        # no frag, pipe
        del wl.fragment
        wl.fragment = 'e'
        ae(wl.string, '[[a#e|]]')

        # no frag after pipe
        wl = WikiLink('[[a|#]]')
        wl.fragment = 'f'
        ae(wl.string, '[[a#f|#]]')

    def test_fragment_deleter(self):
        ae = self.assertEqual
        wl = WikiLink('[[a]]')
        del wl.fragment
        ae(wl.string, '[[a]]')

        wl = WikiLink('[[a#]]')
        del wl.fragment
        ae(wl.string, '[[a]]')

        wl = WikiLink('[[a|]]')
        del wl.fragment
        ae(wl.string, '[[a|]]')

        wl = WikiLink('[[a#|]]')
        del wl.fragment
        ae(wl.string, '[[a|]]')

        wl = WikiLink('[[a|#]]')
        del wl.fragment
        ae(wl.string, '[[a|#]]')


if __name__ == '__main__':
    main()
