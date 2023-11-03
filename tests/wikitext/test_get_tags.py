from wikitextparser import WikiText, parse


def test_assume_that_templates_do_not_exist():
    # this is actually an invalid <s> tag on English Wikipedia, i.e the
    # result of {{para}} makes it invalid.
    assert len(parse('<s {{para|a}}></s>').get_tags('s')) == 1


def test_defferent_nested_tags():
    parsed = parse('<s><b>strikethrough-bold</b></s>')
    b = parsed.get_tags('b')[0].string
    assert b == '<b>strikethrough-bold</b>'
    s = parsed.get_tags('s')[0].string
    assert s == '<s><b>strikethrough-bold</b></s>'
    s2, b2 = parsed.get_tags()
    assert b2.string == b
    assert s2.string == s


def test_same_nested_tags():
    parsed = parse('<b><b>bold</b></b>')
    tags_by_name = parsed.get_tags('b')
    assert tags_by_name[0].string == '<b><b>bold</b></b>'
    assert tags_by_name[1].string == '<b>bold</b>'
    all_tags = parsed.get_tags()
    assert all_tags[0].string == tags_by_name[0].string
    assert all_tags[1].string == tags_by_name[1].string


def test_tag_extension_by_name():
    assert (
        parse('<gallery>pictures</gallery>').get_tags('gallery')[0].contents
        == 'pictures'
    )
    assert (
        parse('<gallery\t>pictures</gallery>').get_tags('gallery')[0].contents
        == 'pictures'
    )


def test_self_closing():
    # extension tag
    assert parse('<references />').get_tags()[0].string == '<references />'
    # HTML tag
    assert parse('<s / >').get_tags()[0].string == '<s / >'


def test_start_only():
    """Some elements' end tag may be omitted in certain conditions.

    An li element’s end tag may be omitted if the li element is immediately
    followed by another li element or if there is no more content in the
    parent element.

    See: https://www.w3.org/TR/html51/syntax.html#optional-tags
    """
    parsed = parse('<li>')
    tags = parsed.get_tags()
    assert tags[0].string == '<li>'


def test_inner_tag():
    parsed = parse('<br><s><b>sb</b></s>')
    s = parsed.get_tags('s')[0]
    assert s.string == '<s><b>sb</b></s>'
    assert s.get_tags()[0].string == '<b>sb</b>'


def test_extension_tags_are_not_lost_in_shadows():
    parsed = parse('text<ref name="c">citation</ref>\n' '<references/>')
    ref, references = parsed.get_tags()
    ref.set_attr('name', 'z')
    assert ref.string == '<ref name="z">citation</ref>'
    assert references.string == '<references/>'


def test_same_tags_end():
    # noinspection PyProtectedMember
    assert WikiText('<s></s><s></s>').get_tags()[0]._span_data[:2] == [0, 7]


def test_pre():  # 46
    assert len(parse('<pre></pre>').get_tags()) == 1


def test_section_tag_apparently_containing_another_section_tag_start():  # 58
    assert (
        parse('<section begin=<section begin=t2 />')
        .get_tags('section')[0]
        .contents
        == ''
    )


def test_tags_in_wikilinks():
    (b,) = parse('[[a|a <b>c]] d</b>').get_tags('b')
    assert b.string == '<b>c]] d</b>'
