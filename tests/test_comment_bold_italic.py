from wikitextparser import Comment, Bold, Italic


def test_comment():
    c = Comment('<!-- c -->')
    assert repr(c) == "Comment('<!-- c -->')"
    assert c.comments == []


def test_bold():
    assert Bold("'''b'''").text == 'b'
    assert Bold("'<!---->''b'''").text == 'b'
    assert Bold("'''b").text == 'b'


def test_italic():
    assert Italic("''i").text == 'i'
    assert Italic("'''''i'''''").text == "'''i'''"
    assert Italic("''i<!---->'<!---->'").text == "i<!---->"
    assert Italic("''i'''").text == "i'"
    # searching "''' ''i'''" for italics gives "''i'''", but it has not end
    assert Italic("''i'''", end_token=False).text == "i'''"


def test_sub_bolds():
    b = Bold("'''A{{{text|'''b'''}}}C'''")
    assert b.get_bolds(recursive=False) == []
    recursive_subbolds = b.get_bolds()
    assert len(recursive_subbolds) == 1  # ?
    assert recursive_subbolds[0]._span_data[:2] == [12, 19]


def test_sub_bolds_italics():
    b = Bold("'''A{{{text|'''b'''}}}C'''")
    assert b.get_bolds_and_italics(recursive=False) == []
    recursive_results = b.get_bolds_and_italics()
    assert len(recursive_results) == 1
    assert recursive_results[0]._span_data[:2] == [12, 19]


def test_sub_italics():
    i = Italic("''A{{{text|''b''}}}C''")
    assert i.get_italics(recursive=False) == []
    recursive_subitalics = i.get_italics()
    assert len(recursive_subitalics) == 1  # ?
    assert recursive_subitalics[0]._span_data[:2] == [11, 16]
