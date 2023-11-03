from wikitextparser import Bold, Italic, parse


def test_get_bolds():
    def ab(s: str, o: str, r: bool = True):
        assert parse(s).get_bolds(r)[0].string == o

    def anb(s: str):
        assert not parse(s).get_bolds(True)

    ab("A''''''''''B", "'''B")
    ab("''''''a''''''", "'''a''''")  # '<i><b>a'</b></i>
    ab("a'''<!--b-->'''BI", "'''BI")
    ab("'''b'''", "'''b'''")
    anb("''i1'''s")
    anb("<!--'''b'''-->")
    ab(
        "a<!---->'<!---->'<!---->'<!---->" "b<!---->'<!---->'<!---->'<!---->d",
        "'<!---->'<!---->'<!---->b<!---->'<!---->'<!---->'",
    )
    ab("'''b{{a|'''}}", "'''b{{a|'''}}")  # ?
    ab("a'''b{{text|c|d}}e'''f", "'''b{{text|c|d}}e'''")
    ab("{{text|'''b'''}}", "'''b'''")
    ab("{{text|'''b}}", "'''b")  # ?
    ab("[[a|'''b]] c", "'''b")
    ab("{{{PARAM|'''b}}} c", "'''b")  # ?
    assert (
        repr(parse("'''b\na'''c").get_bolds())
        == """[Bold("'''b"), Bold("'''c")]"""
    )
    ab("'''<S>b</S>'''", "'''<S>b</S>'''")
    ab("'''b<S>r'''c</S>", "'''b<S>r'''")
    ab("'''''b'''i", "'''b'''")
    assert (
        repr(parse("'''b<ref>r'''c</ref>a").get_bolds())
        == """[Bold("'''b<ref>r'''c</ref>a"), Bold("'''c")]"""
    )
    assert (
        repr(parse("'''b<ref>r'''c</ref>a").get_bolds(False))
        == """[Bold("'''b<ref>r'''c</ref>a")]"""
    )
    ab("'''b{{{p|'''}}}", "'''b{{{p|'''}}}")  # ?
    ab("<nowiki>'''a</nowiki>'''b", "'''a")
    anb("' ' ' a ' ' '")
    ab("x''' '''y", "''' '''")
    ab("x''''''y", "'''y")
    ab("{{text|{{text|'''b'''}}}}", "'''b'''")


def test_get_italics():
    def ai(s: str, o: str, r: bool = True):
        italics = parse(s).get_italics(r)
        assert len(italics) == 1
        assert italics[0].string == o

    ai("''i'''", "''i'''")
    ai("a''' '' b '' '''c", "'' b ''")
    ai("'''''i'''''", "'''''i'''''")
    ai("a'' ''' ib ''' ''c", "'' ''' ib ''' ''")
    ai("''i''", "''i''")
    ai(
        'A<!---->'
        "'<!---->'<!---->'<!---->'<!---->'"
        '<!---->i<!---->'
        "'<!---->'<!---->'<!---->'<!---->'"
        '<!---->B',
        "'<!---->'<!---->'<!---->'<!---->'"
        '<!---->i<!---->'
        "'<!---->'<!---->'<!---->'<!---->'",
    )
    ai("''' ''i'''", "''i'''")


def test_bold_italic_index_change():
    p = parse("'''b1''' ''i1'' '''b2'''")
    b1, b2 = p.get_bolds(recursive=False)
    i1 = p.get_italics(recursive=False)[0]
    b1.text = '1'
    assert p.string == "'''1''' ''i1'' '''b2'''"
    assert i1.string == "''i1''"
    assert b2.text == 'b2'


def test_do_not_return_duplicate_bolds_italics():  # 42
    assert len(parse("{{a|{{b|'''c'''}}}}").get_bolds()) == 1
    assert len(parse("[[file:a.jpg|[[b|''c'']]]]").get_italics()) == 1


def test_multiline_italics():
    a, b = parse("'''a''\n'''b''").get_italics()
    assert a.string == "''a''"
    assert b.string == "''b''"


def test_first_single_letter_word_condition_in_doquotes():
    (b,) = parse("'''a'' b'''c'' '''d''").get_bolds()
    assert b.string == "'''a'' b'''c'' '''"


def test_first_space_condition_in_doquotes_not_used():
    (b,) = parse("'''a'' '''b'' '''c''").get_bolds()
    assert b.string == "'''b'' '''"


def test_first_space_condition_in_balanced_quotes_shadow():
    (b,) = parse("a '''b'' '''c'' '''d''").get_bolds()
    assert b.string == "'''c'' '''"


def test_ignore_head_apostrophes():
    (b,) = parse("''''''''a").get_italics()
    assert b.string == "'''''a"


def test_bold_ends_4_apostrophes():
    (b,) = parse("''a'''b''''").get_bolds()
    assert b.text == "b'"


def test_single_bold_italic():
    (i,) = parse("'''''a").get_italics()
    assert i.text == "'''a"


def test_bolds_italics_span_data_reuse():
    p = parse("'''b''' ''i''")
    b0, i0 = p.get_bolds_and_italics()
    b1, i1 = p.get_bolds_and_italics()
    assert i0._span_data is i1._span_data
    assert b0._span_data is b1._span_data


def test_bold_italics_order():
    i, b = parse("''i'' '''b'''").get_bolds_and_italics(recursive=False)
    assert type(i) is Italic
    assert type(b) is Bold


def test_wikilinks_in_extension_tags_should_not_create_duplicates():  # 57
    assert (
        len(parse("<ref>\n[[a|''b'']]\n</ref>").get_bolds_and_italics()) == 1
    )


def test_italic_end_token():
    assert parse("''i''").get_italics(False)[0].end_token is True
