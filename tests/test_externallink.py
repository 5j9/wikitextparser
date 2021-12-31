from wikitextparser import ExternalLink


def test_externallinks():
    assert ExternalLink('http://example.org').external_links == []


def test_repr():
    assert repr(ExternalLink('HTTP://mediawiki.org')) == \
        "ExternalLink('HTTP://mediawiki.org')"


def test_numberedmailto_change_none_to_empty():
    s = (
        '[mailto:'
        'info@example.org?Subject=URL%20Encoded%20Subject&body='
        'Body%20Textinfo]')
    el = ExternalLink(s)
    assert s[1:-1] == el.url
    assert el.text is None
    assert el.in_brackets
    el.text = ''
    assert el.string == s[:-1] + ' ]'


def test_bare_link():
    el = ExternalLink('HTTP://mediawiki.org')
    assert 'HTTP://mediawiki.org' == el.url
    assert el.text is None
    assert not el.in_brackets


def test_inbracket_with_text():
    el = ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
    assert 'ftp://mediawiki.org' == el.url
    assert 'mediawiki ftp' == el.text
    assert el.in_brackets is True


def test_text_setter():
    el = ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
    el.text = 'a'
    assert '[ftp://mediawiki.org a]' == el.string

    del el.text
    el.text = 'b'
    assert '[ftp://mediawiki.org b]' == el.string

    el = ExternalLink('ftp://mediawiki.org')
    el.text = 'c'
    assert '[ftp://mediawiki.org c]' == el.string


def test_text_delter():
    el = ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
    del el.text
    assert '[ftp://mediawiki.org]' == el.string

    del el.text
    assert '[ftp://mediawiki.org]' == el.string

    el = ExternalLink('ftp://mediawiki.org')
    del el.text
    assert 'ftp://mediawiki.org' == el.string


def test_url_setter():
    el = ExternalLink('[ftp://mediawiki.org mw]')
    el.url = 'https://www.mediawiki.org/'
    assert '[https://www.mediawiki.org/ mw]' == el.string

    el = ExternalLink('ftp://mediawiki.org')
    el.url = 'https://www.mediawiki.org/'
    assert 'https://www.mediawiki.org/' == el.string

    el = ExternalLink('[ftp://mediawiki.org]')
    el.url = 'https://www.mediawiki.org/'
    assert '[https://www.mediawiki.org/]' == el.string


def test_ending_with_less_than_sign():
    el = ExternalLink('[https://www.google.<com]')
    assert el.url == 'https://www.google.'
    assert el.text == '<com'


def test_external_link_case():  # 99
    assert ExternalLink('[Https://a b]').text == 'b'
