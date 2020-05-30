from pytest import main

from wikitextparser import WikiLink


def test_wikilinks():
    assert repr(WikiLink('[[File:example.jpg|frame|[[caption]]]]').wikilinks) == "[WikiLink('[[caption]]')]"


def test_repr():
    assert "WikiLink('[[a]]')" == repr(WikiLink('[[a]]'))


def test_wikilink_target_text():
    wl = WikiLink('[[A | c c\n\ncc]]')
    assert 'A ' == wl.target
    assert ' c c\n\ncc' == wl.text


def test_set_target():
    wl = WikiLink('[[A | B]]')
    wl.target = ' C '
    assert '[[ C | B]]' == wl.string
    del wl.target
    assert '[[ B]]' == wl.string
    del wl.target
    assert '[[]]' == wl.string
    wl = WikiLink('[[A]]')
    wl.target = ' C '
    assert '[[ C ]]' == wl.string


def test_text_settter():
    wl = WikiLink('[[A | B]]')
    wl.text = ' C '
    assert '[[A | C ]]' == wl.string
    del wl.text
    assert '[[A ]]' == wl.string
    del wl.text
    assert '[[A ]]' == wl.string


def test_test_deleter():
    wl = WikiLink('[[t|x]]')
    del wl.text
    assert wl.string == '[[t]]'
    del wl.text
    assert wl.string == '[[t]]'


def test_set_text_when_there_is_no_text():
    wl = WikiLink('[[ A ]]')
    assert wl.text is None
    wl.text = ' C '
    assert '[[ A | C ]]' == wl.string


def test_dont_confuse_pipe_in_target_template_with_wl_pipe():
    wl = WikiLink('[[ {{text|target}} | text ]]')
    assert ' {{text|target}} ' == wl.target
    assert ' text ' == wl.text


def test_tricks():
    """Test unsupported wikilink tricks.

        Currently WikiLink.text returns the piped text literally and does not
        expand these tricks (which by the way do not always work as expected).
        """
    # Pipe trick
    # Note that pipe trick does not work in ref or gallery tags (T4700),
    # also not with links that have anchors, or edit summery links; see:
    # https://en.wikipedia.org/wiki/Help:Pipe_trick#Where_it_doesn't_work
    # https://en.wikipedia.org/wiki/Help:Pipe_trick
    assert WikiLink('[[L|]]').text == ''
    # Slash trick
    # https://en.wikipedia.org/wiki/Help:Pipe_trick#Slash_trick
    assert WikiLink('[[/Subpage/]]').text is None
    # Reverse pipe trick (depends on page title)
    # https://en.wikipedia.org/wiki/Help:Pipe_trick#Reverse_pipe_trick
    assert WikiLink('[[|t]]').text == 't'


def test_title_and_fragment_getters():
    wl = WikiLink('[[a<!--1-->#<!--2-->f|x]]')
    assert wl.title == 'a<!--1-->'
    assert wl.fragment == '<!--2-->f'

    wl = WikiLink('[[a<!--1-->#<!--2-->f]]')
    assert wl.title == 'a<!--1-->'
    assert wl.fragment == '<!--2-->f'

    wl = WikiLink('[[{{#if:||t}}#{{#if:||f}}|x]]')
    assert wl.title == '{{#if:||t}}'
    assert wl.fragment == '{{#if:||f}}'

    wl = WikiLink('[[{{#if:||t}}#{{#if:||f}}]]')
    assert wl.title == '{{#if:||t}}'
    assert wl.fragment == '{{#if:||f}}'

    wl = WikiLink('[<!--1-->[t|x]<!--2-->]')
    assert wl.title == 't'
    assert wl.fragment is None
    assert wl.comments[1].string == '<!--2-->'

    wl = WikiLink('[[t]]')
    assert wl.title == 't'
    assert wl.fragment is None

    wl = WikiLink('[[t|#]]')
    assert wl.title == 't'
    assert wl.fragment is None

    wl = WikiLink('[[t#|x]]')
    assert wl.title == 't'
    assert wl.fragment == ''

    wl = WikiLink('[[t#]]')
    assert wl.title == 't'
    assert wl.fragment == ''


def test_title_and_fragment_setters():
    # no frag, no pipe
    wl = WikiLink('[[a]]')
    wl.title = 'b'
    assert wl.string == '[[b]]'
    wl.fragment = 'c'
    assert wl.string == '[[b#c]]'

    # frag, no pipe
    wl.fragment = 'c'
    assert wl.string == '[[b#c]]'
    wl.title = 'a'
    assert wl.string == '[[a#c]]'

    # frag, pipe
    wl.text = ''  # [[d#c|]]
    wl.fragment = 'e'
    assert wl.string == '[[a#e|]]'
    wl.title = 'b'
    assert wl.string == '[[b#e|]]'

    # no frag, pipe
    del wl.fragment
    wl.fragment = 'e'
    assert wl.string == '[[b#e|]]'
    del wl.fragment
    wl.title = 'a'
    assert wl.string == '[[a|]]'

    # no frag after pipe
    wl = WikiLink('[[a|#]]')
    wl.title = 'b'
    assert wl.string == '[[b|#]]'
    wl.fragment = 'f'
    assert wl.string == '[[b#f|#]]'


def test_title_and_fragment_deleters():
    # no pipe, no frag
    wl = WikiLink('[[a]]')
    del wl.fragment
    assert wl.string == '[[a]]'
    del wl.title
    assert wl.string == '[[]]'

    # no pipe, frag
    wl = WikiLink('[[a#]]')
    del wl.fragment
    assert wl.string == '[[a]]'
    wl.fragment = 'f'
    del wl.title
    assert wl.string == '[[f]]'

    # pipe, no frag
    wl = WikiLink('[[a|]]')
    del wl.fragment
    assert wl.string == '[[a|]]'
    del wl.title
    assert wl.string == '[[|]]'

    # pipe, frag
    wl = WikiLink('[[a#|]]')
    del wl.fragment
    assert wl.string == '[[a|]]'
    wl.fragment = 'f'
    del wl.title
    assert wl.string == '[[f|]]'

    # pipe, no frag, special case
    wl = WikiLink('[[a|#]]')
    del wl.fragment
    del wl.title
    assert wl.string == '[[|#]]'


if __name__ == '__main__':
    main()
