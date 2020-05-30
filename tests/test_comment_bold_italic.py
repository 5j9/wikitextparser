from pytest import main

from wikitextparser import Comment, Bold, Italic


def test_comment():
    c = Comment('<!-- c -->')
    assert repr(c) == "Comment('<!-- c -->')"
    assert c.comments == []


def test_bold():
    assert Bold("'''b'''").text == 'b'
    assert Bold("'<!---->''b'''").text == 'b'


def test_italic():
    assert Italic("'''''i'''''").text == "'''i'''"
    assert Italic("''i<!---->'<!---->'").text == "i<!---->"


if __name__ == '__main__':
    main()
