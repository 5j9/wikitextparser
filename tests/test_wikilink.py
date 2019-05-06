"""Test the wikilink.py module."""


from unittest import main, TestCase

from wikitextparser import WikiLink


class TestWikiLink(TestCase):

    """Test WikiLink functionalities."""

    def test_repr(self):
        self.assertEqual("WikiLink('[[a]]')", repr(WikiLink('[[a]]')))

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

    def test_title_and_fragment_getters(self):
        ae = self.assertEqual

        wl = WikiLink('[[a<!--#1-->#<!--#2-->f|x]]')
        ae(wl.title, 'a<!--#1-->')
        ae(wl.fragment, '<!--#2-->f')

        wl = WikiLink('[[a<!--#1-->#<!--#2-->f]]')
        ae(wl.title, 'a<!--#1-->')
        ae(wl.fragment, '<!--#2-->f')

        wl = WikiLink('[[{{#if:||t}}#{{#if:||f}}|x]]')
        ae(wl.title, '{{#if:||t}}')
        ae(wl.fragment, '{{#if:||f}}')

        wl = WikiLink('[[{{#if:||t}}#{{#if:||f}}]]')
        ae(wl.title, '{{#if:||t}}')
        ae(wl.fragment, '{{#if:||f}}')

        wl = WikiLink('[[t|x]]')
        ae(wl.title, 't')
        ae(wl.fragment, None)

        wl = WikiLink('[[t]]')
        ae(wl.title, 't')
        ae(wl.fragment, None)

        wl = WikiLink('[[t|#]]')
        ae(wl.title, 't')
        ae(wl.fragment, None)

        wl = WikiLink('[[t#|x]]')
        ae(wl.title, 't')
        ae(wl.fragment, '')

        wl = WikiLink('[[t#]]')
        ae(wl.title, 't')
        ae(wl.fragment, '')

    def test_title_and_fragment_setters(self):
        ae = self.assertEqual

        # no frag, no pipe
        wl = WikiLink('[[a]]')
        wl.title = 'b'
        ae(wl.string, '[[b]]')
        wl.fragment = 'c'
        ae(wl.string, '[[b#c]]')

        # frag, no pipe
        wl.fragment = 'c'
        ae(wl.string, '[[b#c]]')
        wl.title = 'a'
        ae(wl.string, '[[a#c]]')

        # frag, pipe
        wl.text = ''  # [[d#c|]]
        wl.fragment = 'e'
        ae(wl.string, '[[a#e|]]')
        wl.title = 'b'
        ae(wl.string, '[[b#e|]]')

        # no frag, pipe
        del wl.fragment
        wl.fragment = 'e'
        ae(wl.string, '[[b#e|]]')
        del wl.fragment
        wl.title = 'a'
        ae(wl.string, '[[a|]]')

        # no frag after pipe
        wl = WikiLink('[[a|#]]')
        wl.title = 'b'
        ae(wl.string, '[[b|#]]')
        wl.fragment = 'f'
        ae(wl.string, '[[b#f|#]]')

    def test_title_and_fragment_deleters(self):
        ae = self.assertEqual

        # no pipe, no frag
        wl = WikiLink('[[a]]')
        del wl.fragment
        ae(wl.string, '[[a]]')
        del wl.title
        ae(wl.string, '[[]]')

        # no pipe, frag
        wl = WikiLink('[[a#]]')
        del wl.fragment
        ae(wl.string, '[[a]]')
        wl.fragment = 'f'
        del wl.title
        ae(wl.string, '[[f]]')

        # pipe, no frag
        wl = WikiLink('[[a|]]')
        del wl.fragment
        ae(wl.string, '[[a|]]')
        del wl.title
        ae(wl.string, '[[|]]')

        # pipe, frag
        wl = WikiLink('[[a#|]]')
        del wl.fragment
        ae(wl.string, '[[a|]]')
        wl.fragment = 'f'
        del wl.title
        ae(wl.string, '[[f|]]')

        # pipe, no frag, special case
        wl = WikiLink('[[a|#]]')
        del wl.fragment
        del wl.title
        ae(wl.string, '[[|#]]')


if __name__ == '__main__':
    main()
