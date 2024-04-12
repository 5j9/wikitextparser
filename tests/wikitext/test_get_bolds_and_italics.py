from wikitextparser import Bold, Italic, parse


def assert_bold(
    input_string: str, expected_bold_string: str, recursive: bool = True
):
    assert (
        parse(input_string).get_bolds(recursive)[0].string
        == expected_bold_string
    )


def assert_no_bold(input_string: str):
    assert not parse(input_string).get_bolds(True)


def test_one_extra_on_each_side():
    assert_bold("''''''a''''''", "'''a''''")  # '<i><b>a'</b></i>


def test_two_tree_letter():
    assert_no_bold("''i1'''s")


def test_italic_bold_letter_bold():
    assert_bold("'''''b'''i", "'''b'''")


def test_get_bolds():
    assert_bold("A''''''''''B", "'''B")
    assert_bold("a'''<!--b-->'''BI", "'''BI")
    assert_bold("'''b'''", "'''b'''")
    assert_no_bold("<!--'''b'''-->")
    assert_bold("'''b{{a|'''}}", "'''b{{a|'''}}")  # ?
    assert_bold("a'''b{{text|c|d}}e'''f", "'''b{{text|c|d}}e'''")
    assert_bold("{{text|'''b'''}}", "'''b'''")
    assert_bold("{{text|'''b}}", "'''b")  # ?
    assert_bold("'''<S>b</S>'''", "'''<S>b</S>'''")
    assert_bold("'''b<S>r'''c</S>", "'''b<S>r'''")
    assert (
        repr(parse("'''b<ref>r'''c</ref>a").get_bolds())
        == """[Bold("'''b<ref>r'''c</ref>a"), Bold("'''c")]"""
    )
    assert (
        repr(parse("'''b<ref>r'''c</ref>a").get_bolds(False))
        == """[Bold("'''b<ref>r'''c</ref>a")]"""
    )
    assert_bold("'''b{{{p|'''}}}", "'''b{{{p|'''}}}")  # ?
    assert_bold("<nowiki>'''a</nowiki>'''b", "'''a")
    assert_no_bold("' ' ' a ' ' '")
    assert_bold("x''' '''y", "''' '''")
    assert_bold("x''''''y", "'''y")
    assert_bold("{{text|{{text|'''b'''}}}}", "'''b'''")


def test_hald_bolds_with_newline_in_between():
    assert (
        repr(parse("'''b\na'''c").get_bolds())
        == """[Bold("'''b"), Bold("'''c")]"""
    )


def test_half_bold_in_param():
    assert_bold("{{{PARAM|'''b}}} c", "'''b")  # ?


def test_half_bold_in_wikilink():
    assert_bold("[[a|'''b]] c", "'''b")


def test_comment_before_and_after_bold():
    assert_bold(
        "a<!---->'<!---->'<!---->'<!---->" "b<!---->'<!---->'<!---->'<!---->d",
        "'<!---->'<!---->'<!---->b<!---->'<!---->'<!---->'",
    )


def ai(s: str, o: str, r: bool = True):
    italics = parse(s).get_italics(r)
    assert len(italics) == 1
    assert italics[0].string == o


def test_bold_italic_with_comments_in_between_every_apos():
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


def test_get_italics():
    ai("''i'''", "''i'''")
    ai("a''' '' b '' '''c", "'' b ''")
    ai("a'' ''' ib ''' ''c", "'' ''' ib ''' ''")
    ai("''i''", "''i''")
    ai("''' ''i'''", "''i'''")


def test_get_italics_2():
    ai("'''''i'''''", "'''''i'''''")


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


def test_four_apostrophe_to_three_to_two():
    assert [repr(i) for i in parse("''''a''b").get_bolds_and_italics()] == [
        "Italic(\"''a''\")"
    ]
