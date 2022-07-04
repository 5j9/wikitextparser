from wikitextparser import parse, remove_markup, Template


def test_plaintext():
    def ap(s, p):
        assert parse(s).plain_text() == p
    ap('[https://wikimedia.org/ wm]', 'wm')
    ap("{{{a}}}", '')
    ap("<span>a<small>b</small>c</span>", 'abc')
    ap("<ref>''w''</ref>", 'w')  # could be '' as well
    ap("[[file:a.jpg|[[w]]]]", '')
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
    ap("{{{1|a}}}", 'a')


def test_plain_text_should_not_mutate():  # 40
    p = parse('[[a]][[b]]')
    a, b = p.wikilinks
    assert a.plain_text() == 'a'
    assert b.plain_text() == 'b'


def test_remove_markup():
    assert remove_markup("''a'' {{b}} c <!----> '''d'''") == "a  c  d"


def test_do_not_include_end_tag():
    assert parse('<div>[http://a]</div>').plain_text() == ''


def test_nested_bold_or_italic_plain_text():
    assert remove_markup("''[[a|''b'']]") == 'b'
    assert remove_markup("'''[[a|'''b''']]") == 'b'


def test_nested_tag_extensions_plain_text():
    assert parse(
        '<noinclude><pagequality level="4" user="Zabia" /></noinclude>'
    ).plain_text() == ''


def test_plain_text_when_the_whole_content_of_bold_is_a_template():
    assert parse("'''{{text|a}}''', ''b''<ref>c</ref>").plain_text() == ', bc'


def test_plain_text_non_root_node():
    assert Template('{{T}}').plain_text() == ''


def test_extract_unparsable_extension_tags_first():  # 90
    assert parse(
        "<noinclude>[[a|<nowiki>[</nowiki>b<nowiki>]</nowiki>]]</noinclude>"
    ).plain_text() == '[b]'


def test_self_closing_tag_contents():  # 88
    assert parse('a<ref n=b/>').plain_text() == 'a'


def test_replace_fuctions():
    def t(_):
        return 'T'

    def f(_):
        return 'F'

    assert parse(
        'a {{tt}} b {{tt}} a {{#if:}} b {{#if:}} c'
    ).plain_text(
        replace_templates=t,
        replace_parser_functions=f,
    ) == 'a T b T a F b F c'


def test_nested_template_function_replace():
    def t(_):
        return 'T'
    assert parse('{{tt|{{tt}}}}').plain_text(replace_templates=t) == \
        'T'


def test_replace_nested_template_functions():
    def t(_):
        return 'T'

    assert parse(
        '{{tt|{{#if:}}}}'
    ).plain_text(
        replace_templates=t,
        replace_parser_functions=False,
    ) == 'T'
