from wikitextparser import Template, parse, remove_markup


def test_plaintext():
    def ap(s, p):
        assert parse(s).plain_text() == p

    ap('[https://wikimedia.org/ wm]', 'wm')
    ap('{{{a}}}', '')
    ap('<span>a<small>b</small>c</span>', 'abc')
    ap("<ref>''w''</ref>", 'w')  # could be '' as well
    ap('[[file:a.jpg|[[w]]]]', '')
    ap('<span>a</span>b<span>c</span>', 'abc')  # 39
    ap('{{a}}b{{c}}', 'b')  # 39
    ap('t [[a|b]] t', 't b t')
    ap('t [[a]] t', 't a t')
    ap('&Sigma; &#931; &#x3a3; Σ', 'Σ Σ Σ Σ')
    ap('[https://wikimedia.org/]', '')
    ap('<s>text</s>', 'text')
    ap('{{template|argument}}', '')
    ap('{{#if:a|y|n}}', '')
    ap("'''b'''", 'b')
    ap("''i''", 'i')
    ap('{{{1|a}}}', 'a')


def test_plain_text_should_not_mutate():  # 40
    p = parse('[[a]][[b]]')
    a, b = p.wikilinks
    assert a.plain_text() == 'a'
    assert b.plain_text() == 'b'


def test_remove_markup():
    assert remove_markup("''a'' {{b}} c <!----> '''d'''") == 'a  c  d'


def test_do_not_include_end_tag():
    assert parse('<div>[http://a]</div>').plain_text() == ''


def test_nested_bold_or_italic_plain_text():
    assert remove_markup("''[[a|''b'']]") == 'b'
    assert remove_markup("'''[[a|'''b''']]") == 'b'


def test_nested_tag_extensions_plain_text():
    assert (
        parse(
            '<noinclude><pagequality level="4" user="Zabia" /></noinclude>'
        ).plain_text()
        == ''
    )


def test_plain_text_when_the_whole_content_of_bold_is_a_template():
    assert parse("'''{{text|a}}''', ''b''<ref>c</ref>").plain_text() == ', bc'


def test_plain_text_non_root_node():
    assert Template('{{T}}').plain_text() == ''


def test_extract_unparsable_extension_tags_first():  # 90
    assert (
        parse(
            '<noinclude>[[a|<nowiki>[</nowiki>b<nowiki>]</nowiki>]]</noinclude>'
        ).plain_text()
        == '[b]'
    )


def test_self_closing_tag_contents():  # 88
    assert parse('a<ref n=b/>').plain_text() == 'a'


def test_replace_fuctions():
    def t(_):
        return 'T'

    def f(_):
        return 'F'

    assert (
        parse('a {{tt}} b {{tt}} a {{#if:}} b {{#if:}} c').plain_text(
            replace_templates=t,
            replace_parser_functions=f,
        )
        == 'a T b T a F b F c'
    )


def test_nested_template_function_replace():
    def t(_):
        return 'T'

    assert parse('{{tt|{{tt}}}}').plain_text(replace_templates=t) == 'T'


def test_replace_nested_template_functions():
    def t(_):
        return 'T'

    assert (
        parse('{{tt|{{#if:}}}}').plain_text(
            replace_templates=t,
            replace_parser_functions=t,  # tests for
        )
        == 'T'
    )


def test_after_tag_deletion():  # 113
    parsed = parse('<ref>R</ref>')
    tag = parsed.get_tags('ref')[0]
    del tag[:]
    assert parsed.plain_text() == ''


def test_table():
    p = parse(
        'a\n'
        '{|\n'
        '|[[Orange]]\n'
        '|Apple\n'
        '|-\n'
        '|Bread\n'
        '|Pie\n'
        '|-\n'
        '|Butter\n'
        '|Ice cream \n'
        '|}\n'
        'b'
    )
    assert (
        p.plain_text()
        == 'a\n\nOrange\tApple\nBread \tPie\nButter\tIce cream\n\nb'
    )


TABLE_WITH_ROW_AND_COL_SPANS = """{| class="wikitable"
!colspan="6"|Shopping List
|-
|rowspan="2"|Bread & Butter
|Pie
|Buns
|Danish
|colspan="2"|Croissant
|-
|Cheese
|colspan="2"|Ice cream
|Butter
|Yogurt
|}"""


def test_none_in_table_data():
    p = parse(TABLE_WITH_ROW_AND_COL_SPANS)
    assert p.plain_text() == (
        '\nShopping List \tShopping List\tShopping List\tShopping List\tShopping List\tShopping List\nBread & Butter\tPie          \tBuns         \tDanish       \tCroissant    \tCroissant\nBread & Butter\tCheese       \tIce cream    \tIce cream    \tButter       \tYogurt\n'
    )


TABLE_WITH_CAPTION = """{|
|+Food complements
|-
|Orange
|Apple
|-
|Bread
|Pie
|-
|Butter
|Ice cream
|}"""


def test_table_caption():
    assert parse(TABLE_WITH_CAPTION).plain_text() == (
        '\nFood complements\n\nOrange\tApple\nBread \tPie\nButter\tIce cream\n'
    )


def test_table_with_no_data():  # 120
    text = """{|{{t1|a=v}}{{t2|a2=v2]]}}\n|}"""
    assert parse(text).plain_text() == ''


TABLE_IN_IMAGE = """
1234567890123456789012345678901234567890123456789012345
[[Image:Huffman coding example.svg|thumb|
{|class="wikitable"
! Symbol !! Code
|-
|a1 || 0
|-
|}
]]
"""


def test_table_in_image():  # 122
    parsed = parse(TABLE_IN_IMAGE)
    assert parsed.wikilinks[0].plain_text() == ''


def test_file_links():
    # https://www.mediawiki.org/wiki/Help:Linking_to_files
    assert parse('[[:File:Example.jpg]]').plain_text() == ':File:Example.jpg'
    assert parse('[[:File:n.jpg|Sunflowers]]').plain_text() == 'Sunflowers'
    # just having : and . in title does not mean it is a file. Real example:
    assert (
        parse('[[Survivor: Brains vs. Brawn vs. Beauty]]').plain_text()
        == 'Survivor: Brains vs. Brawn vs. Beauty'
    )
    assert parse('[[#f|t]]').plain_text() == 't'  # 123
    # Fails for the following cases:
    # assert parse('[[Media:Example.jpg]]').plain_text() == 'Media:Example.jpg'
    # assert parse('[[Media:n.jpg|Sunflowers]]').plain_text() == 'Sunflowers'


def test_image_name_with_multiple_dots():  # 129
    assert (
        parse(
            'a\n[[File:Julia set (C = 0.285, 0.01).jpg|caption]]\nb'
        ).plain_text()
        == 'a\n\nb'
    )


def test_tag_containing_comment_with_no_end():  # 126
    parsed = parse(
        """
        [[a|b]]
        <gallery>
        <!-- 
        </gallery>
        """
    )
    del parsed.wikilinks[0][:]
    assert parsed.plain_text().strip() == ''


def test_on_list_with_replace_template_function():  # 130
    assert (
        parse('\n#:{{a}}')
        .get_lists()[0]
        .plain_text(replace_templates=lambda t: t.name)
        == '#:a'
    )


def test_external_starting_with_comment():
    text = "''[https://<!---->x.com/ x]''"
    parsed = parse(text)
    assert parsed.plain_text() == 'x'
