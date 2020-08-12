from typing import Dict, List

from pytest import mark

from wikitextparser import WikiText, parse
# noinspection PyProtectedMember
from wikitextparser._spans import PF_TL_FINDITER, parse_to_spans


def bytearray_parse_to_spans(bytes_: bytes) -> Dict[str, List[List[int]]]:
    return {
        k: [i[:2] for i in v]
        for k, v in parse_to_spans(bytearray(bytes_)).items()}


bpts = bytearray_parse_to_spans


# noinspection PyProtectedMember
def test_template_name_cannot_be_empty():
    assert WikiText('{{_}}')._type_to_spans['Template'] == []
    assert WikiText('{{_|text}}')._type_to_spans['Template'] == []
    assert len(WikiText('{{text| {{_}} }}')._type_to_spans['Template']) == 1
    assert len(WikiText('{{ {{_|text}} | a }}')._type_to_spans['Template']) \
        == 0
    assert len(WikiText('{{a{{_|text}} | a }}')._type_to_spans['Template']) \
        == 0


# noinspection PyProtectedMember
def test_template_in_template():
    assert bpts(b'{{cite|{{t1}}|{{t2}}}}')['Template'] == \
        [[0, 22], [7, 13], [14, 20]]


# noinspection PyProtectedMember
def test_textmixed_multitemplate():
    assert bpts(
        b'text1{{cite|{{t1}}|{{t2}}}}'
        b'text2{{cite|{{t3}}|{{t4}}}}text3'
    )['Template'] == [
        [5, 27], [12, 18], [19, 25], [32, 54], [39, 45], [46, 52]]


# noinspection PyProtectedMember
def test_multiline_mutitemplate():
    assert bpts(b'{{cite\n    |{{t1}}\n    |{{t2}}}}')['Template'] ==\
        [[0, 32], [12, 18], [24, 30]]


# noinspection PyProtectedMember
def test_lacks_ending_braces():
    assert [[7, 13], [14, 20]] == bpts(b'{{cite|{{t1}}|{{t2}}')['Template']


# noinspection PyProtectedMember
def test_lacks_starting_braces():
    assert [[5, 11], [12, 18]] == bpts(b'cite|{{t1}}|{{t2}}}}')['Template']


# noinspection PyProtectedMember
def test_no_template_for_braces_around_wikilink():
    assert not WikiText('{{[[a]]}}')._type_to_spans['Template']


# noinspection PyProtectedMember
def test_template_inside_parameter():
    d = bpts(b'{{{1|{{colorbox|yellow|text1}}}}}')
    assert [[5, 30]], d['Template']
    assert [[0, 33]], d['Parameter']


# noinspection PyProtectedMember
def test_parameter_inside_template():
    d = bpts(b'{{colorbox|yellow|{{{1|defualt_text}}}}}')
    assert [[0, 40]] == d['Template']
    assert [[18, 38]] == d['Parameter']


# noinspection PyProtectedMember
def test_template_name_cannot_contain_newline():
    assert [] == WikiText(
        '{{\nColor\nbox\n|mytext}}')._type_to_spans['Template']


# noinspection PyProtectedMember
def test_unicode_template():
    (a, b, _, _), = WikiText('{{\nرنگ\n|متن}}')._type_to_spans['Template']
    assert a == 0
    assert b == 13


# noinspection PyProtectedMember
def test_invoking_a_named_ref_is_not_a_ref_start():
    """See [[mw:Extension:Cite#Multiple_uses_of_the_same_footnote]].

    [[mw:Help:Extension:Cite]] may be helpful, too.

    """
    (a, b, _, _), = WikiText(
        '{{text|1=v<ref name=n/>}}\ntext.<ref name=n>r</ref>'
    )._type_to_spans['Template']
    assert a == 0
    assert b == 25


# noinspection PyProtectedMember
def test_invalid_refs_that_should_not_produce_any_template():
    assert [] == WikiText(
        'f {{text|<ref \n > g}} <ref  name=n />\n</ref  >\n'
    )._type_to_spans['Template']


# noinspection PyProtectedMember
def test_unicode_parser_function():
    (a, b, _, _), = WikiText('{{#اگر:|فلان}}')._type_to_spans['ParserFunction']
    assert a == 0
    assert b == 14


# noinspection PyProtectedMember
def test_unicode_parameters():
    (a, b, _, _), (c, d, _, _) = WikiText(
        '{{{پارا۱|{{{پارا۲|پيشفرض}}}}}}')._type_to_spans['Parameter']
    assert a == 0
    assert b == 30
    assert c == 9
    assert d == 27


# noinspection PyProtectedMember
def test_image_containing_wikilink():
    (a, b, _, _), (c, d, _, _), (e, f, _, _) = parse(
        "[[File:xyz.jpg|thumb|1px|txt1 [[wikilink1]] txt2 "
        "[[Wikilink2]].]]")._type_to_spans['WikiLink']
    assert a == 0
    assert b == 65
    assert c == 30
    assert d == 43
    assert e == 49
    assert f == 62


def test_extracting_sections():
    sections = WikiText(
        '== h2 ==\nt2\n\n=== h3 ===\nt3\n\n== h22 ==\nt22').sections
    assert 4 == len(sections)
    assert 0 == sections[0].level
    assert sections[0].title is None
    assert '' == sections[0].contents
    assert '== h2 ==\nt2\n\n=== h3 ===\nt3\n\n' == str(sections[1])
    assert (
        "[Section('\\n'), Section('== 1 ==\\n'), "
        "Section('== 2 ==\\n=== 2.1 ===\\n==== 2.1.1 ====\\n"
        "===== 2.1.1.1 =====\\n=== 2.2 ===\\n=== 2.3 ===\\n"
        "==== 2.3.1 ====\\n2.3.1\\n'), Section('=== 2.1 ===\\n"
        "==== 2.1.1 ====\\n===== 2.1.1.1 =====\\n'), "
        "Section('==== 2.1.1 ====\\n===== 2.1.1.1 =====\\n'), "
        "Section('===== 2.1.1.1 =====\\n'), Section('=== 2.2 ===\\n'), "
        "Section('=== 2.3 ===\\n==== 2.3.1 ====\\n2.3.1\\n'), "
        "Section('==== 2.3.1 ====\\n2.3.1\\n'), Section('== 3 ==\\n')]") == \
        str(WikiText(
            '\n== 1 ==\n== 2 ==\n=== 2.1 ===\n==== 2.1.1 ===='
            '\n===== 2.1.1.1 =====\n=== 2.2 ===\n=== 2.3 ==='
            '\n==== 2.3.1 ====\n2.3.1\n== 3 ==\n').sections)


def test_section_title_may_contain_template_newline_etc():
    sections = WikiText(
        '=== h3 {{z\n\n|text}}<!-- \nc --><nowiki>\nnw'
        '\n</nowiki> ===\nt3').sections
    assert 2 == len(sections)
    assert ' h3 {{z\n\n|text}}<!-- \nc --><nowiki>\nnw\n</nowiki> ' ==\
        sections[1].title
    assert 't3' == sections[1].contents


def test_keyword_and_positional_args_removal():
    wt = WikiText("text{{t1|kw=a|1=|pa|kw2=a|pa2}}{{t2|a|1|1=}}text")
    t1, t2 = wt.templates
    t1_args = t1.arguments
    t2_args = t2.arguments
    assert '1' == t1_args[2].name
    assert 'kw2' == t1_args[3].name
    assert '2' == t1_args[4].name
    assert '1' == t2_args[0].name
    assert '2' == t2_args[1].name
    assert '1' == t2_args[2].name
    del t1_args[0][:]
    t1_args = t1.arguments
    t2_args = t2.arguments
    assert '1' == t1_args[0].name
    assert 'kw2' == t1_args[2].name
    assert '|pa2' == t1_args[3].string
    assert '1' == t2_args[0].name
    assert '2' == t2_args[1].name
    assert '1' == t2_args[2].name
    del t1_args[1][:]
    t1_args = t1.arguments
    t2_args = t2.arguments
    assert "text{{t1|1=|kw2=a|pa2}}{{t2|a|1|1=}}text" == wt.string
    assert 'pa2' == t1_args[2].value
    assert '1' == t1_args[2].name
    assert 'a' == t2_args[0].value
    assert '1' == t2_args[0].name


def test_parser_function_regex():
    finditer = PF_TL_FINDITER
    parser_functions = (
        # Technical metadata variables
        b'{{PROTECTIONLEVEL:action}}',
        b'{{DISPLAYTITLE:title}}',
        b'{{DEFAULTCATEGORYSORT:sortkey}}',
        b'{{DEFAULTSORT:sortkey}}',
        b'{{DEFAULTSORTKEY:sortkey}}',
        b'{{PROTECTIONEXPIRY:action}}',
        # Statistic variables
        b'{{NUMBEROFPAGES:R}}',
        b'{{NUMBEROFARTICLES:R}}',
        b'{{NUMBEROFFILES:R}}',
        b'{{NUMBEROFEDITS:R}}',
        b'{{NUMBEROFVIEWS:R}}',
        b'{{NUMBEROFUSERS:R}}',
        b'{{NUMBEROFADMINS:R}}',
        b'{{PAGESINCATEGORY:categoryname}}',
        b'{{PAGESINCAT:categoryname}}',
        b'{{PAGESINCATEGORY:categoryname|all}}',
        b'{{NUMBERINGROUP:groupname}}',
        b'{{NUMINGROUP:groupname}}',
        b'{{PAGESINNS:index}}',
        b'{{PAGESINNAMESPACE:index}}',
        # Page name variables
        b'{{FULLPAGENAME:page}}',
        b'{{PAGENAME:page}}',
        b'{{BASEPAGENAME:page}}',
        b'{{SUBPAGENAME:page}}',
        b'{{SUBJECTPAGENAME:page}}',
        b'{{ARTICLEPAGENAME:page}}',
        b'{{TALKPAGENAME:page}}',
        b'{{ROOTPAGENAME:page}}',
        # URL encoded page name variables
        b'{{FULLPAGENAMEE:page}}',
        b'{{PAGENAMEE:page}}',
        b'{{BASEPAGENAMEE:page}}',
        b'{{SUBPAGENAMEE:page}}',
        b'{{SUBJECTPAGENAMEE:page}}',
        b'{{ARTICLEPAGENAMEE:page}}',
        b'{{TALKPAGENAMEE:page}}',
        b'{{ROOTPAGENAMEE:page}}',
        # Namespace variables
        b'{{NAMESPACE:page}}',
        b'{{NAMESPACENUMBER:page}}',
        b'{{SUBJECTSPACE:page}}',
        b'{{ARTICLESPACE:page}}',
        b'{{TALKSPACE:page}}',
        # Encoded namespace variables
        b'{{NAMESPACEE:page}}',
        b'{{SUBJECTSPACEE:page}}',
        b'{{ARTICLESPACEE:page}}',
        b'{{TALKSPACEE:page}}',
        # Technical metadata parser functions
        b'{{PAGEID: page name }}',
        b'{{PAGESIZE: page name }}',
        b'{{PROTECTIONLEVEL:action | page name}}',
        b'{{CASCADINGSOURCES:page name}}',
        b'{{REVISIONID: page name }}',
        b'{{REVISIONDAY: page name }}',
        b'{{REVISIONDAY2: page name }}',
        b'{{REVISIONMONTH: page name }}',
        b'{{REVISIONMONTH1: page name }}',
        b'{{REVISIONYEAR: page name }}',
        b'{{REVISIONTIMESTAMP: page name }}',
        b'{{REVISIONUSER: page name }}',
        # URL data parser functions
        b'{{localurl:page name}}',
        b'{{fullurl:page name}}',
        b'{{canonicalurl:page name}}',
        b'{{filepath:file name}}',
        b'{{urlencode:string}}',
        b'{{anchorencode:string}}',
        # Namespace parser functions
        b'{{ns:-2}}',
        b'{{nse:}}',
        # Formatting parser functions
        b'{{formatnum:unformatted number}}',
        b'{{lc:string}}',
        b'{{lcfirst:string}}',
        b'{{uc:string}}',
        b'{{ucfirst:string}}',
        b'{{padleft:xyz|stringlength}}',
        b'{{padright:xyz|stringlength}}',
        # Localization parser functions
        b'{{plural:2|is|are}}',
        b'{{grammar:N|noun}}',
        b'{{gender:username|text for every gender}}',
        b'{{int:message name}}',
        # Miscellaneous
        b'{{#language:language code}}',
        b'{{msg:xyz}}',
        b'{{msgnw:xyz}}',
        b'{{raw:xyz}}',
        b'{{safesubst:xyz}}',
        b'{{subst:xyz}}')
    for pf in parser_functions:
        assert next(finditer(pf))[0] == pf


# noinspection PyProtectedMember
def test_wikilinks_inside_exttags():
    (s, e, _, _), = WikiText('<ref>[[w]]</ref>')._type_to_spans['WikiLink']
    assert s == 5
    assert e == 10


def test_single_brace_in_tl():
    (s, e), = bpts(b'{{text|i}n}}')['Template']
    assert s == 0
    assert e == 12


def test_single_brace_after_first_tl_removal():
    (s0, e0), (s1, e1) = bpts(b'{{text|{{text|}}} }}')['Template']
    assert s0 == 0
    assert e0 == 20
    assert s1 == 7
    assert e1 == 16


def test_parse_inner_contents_of_wikilink_inside_ref():
    (s, e), = bpts(b'<ref>[[{{z|link}}]]</ref>')['Template']
    assert s == 7
    assert e == 17


def test_params_are_extracted_before_parser_functions():
    (s, e), = bpts(b'{{{#expr:1+1|3}}}')['Parameter']
    assert s == 0
    assert e == 17


def test_single_brace_after_pf_remove():
    assert {
        'Parameter': [], 'ParserFunction': [[4, 17]],
        'Template': [], 'WikiLink': [], 'Comment': [],
        'ExtensionTag': []} == bpts(b'{{{ {{#if:v|y|n}}} }}')


def test_nested_wikilinks_in_ref():
    assert {
        'Parameter': [], 'ParserFunction': [], 'Template': [],
        'WikiLink': [[5, 40], [30, 38]], 'Comment': [],
        'ExtensionTag': [[0, 46]]
    } == bpts(b'<ref>[[File:Example.jpg|thumb|[[Link]]]]</ref>')


@mark.xfail
def test_invalid_nested_wikilinks():
    assert {
        'Parameter': [], 'ParserFunction': [], 'Template': [],
        'WikiLink': [[10, 15]], 'Comment': [], 'ExtTag': [[0, 24]]
    } == bpts(b'<ref>[[L| [[S]] ]]</ref>')


@mark.xfail
def test_invalid_nested_wikilinks_in_ref():
    assert {
        'Parameter': [], 'ParserFunction': [], 'Template': [],
        'WikiLink': [[0, 13]], 'Comment': [], 'ExtTag': []
    } == bpts(b'[[L| [[S]] ]]')


def test_nested_parser_functions_containing_param():
    assert {
        'Comment': [], 'ExtensionTag': [], 'Parameter': [[18, 25]],
        'ParserFunction': [[0, 31], [9, 28]], 'Template': [],
        'WikiLink': []} == bpts(b'{{#if: | {{#expr: {{{p}}} }} }}')


def test_eliminate_invalid_templates_after_extracting_params():
    assert {
        'Comment': [], 'ExtensionTag': [], 'Parameter': [[0, 9]],
        'ParserFunction': [], 'Template': [], 'WikiLink': []
    } == bpts(b'{{{_|2}}}')


def test_invalid_table_in_template():
    assert {
        'Comment': [], 'ExtensionTag': [], 'Parameter': [],
        'ParserFunction': [], 'Template': [[0, 17]], 'WikiLink': []
    } == bpts(b'{{t|\n{|a\n|b\n|}\n}}')


def test_nested_template_with_unmatched_leading_brace():
    assert [0, 21] == bpts(b'{{text|{{{text|a}} }}')['Template'][0]


def test_wikilink_with_extra_brackets():
    assert [0 == 7], bpts(b'[[a|b]]]')['WikiLink'][0]
    assert [0 == 9], bpts(b'[[a|[b]]]')['WikiLink'][0]
    assert not bpts(b'[[[a|b]]')['WikiLink']
    assert not bpts(b'[[[a]|b]]')['WikiLink']


def test_templates_before_tags():
    # assuming that templates do not exist
    # could be the other way around
    assert bpts(b'{{z|<s }}>a</s>c}}')['Template'][0] == [0, 9]
    assert bpts(b'{{z|<s>}}</s>}}')['Template'][0] == [0, 9]
    assert bpts(b'{{z<s }}>}}</s }}>}}')['Template'] == []
    assert bpts(b'<s {{z|a}}></s>')['Template'][0] == [3, 10]


def test_wikilinks_priority():
    assert bpts(  # wikilinks are valid inside templates, params, pfs, or tags
        b'<s>{{text|{{ #if: {{{3|}}} || {{{1|[[a|a]]}}} }}}}</s>'
    )['WikiLink'][0] == [35, 42]
    # but the tag must be valid
    assert bpts(b'[[target|t<z ]]|>e</z x|]]>t]]')['WikiLink'][0] == [0, 15]

    # tags before wikilinks (tags are allowed in the text part)
    assert bpts(b'[[target|<s>t]]</s>')['WikiLink'][0] == [0, 15]
    # the end of a wikilink cannot be inside a tag (start and end tags
    # are tokenized before wikilinks)
    assert bpts(b'[[a|b<s ]]|>c</s d|]]>e]]')['WikiLink'][0] == [0, 25]

    # wikilinks before templates
    assert bpts(b'[[w|{{z]]}}')['WikiLink'][0] == [0, 9]
    # Non-existing templates are not valid inside wikilinks. Ignore them.
    # todo: an option to not ignore templates?
    assert bpts(b'[[a|{{z}}]]')['WikiLink'][0] == [0, 11]

    # params are *processed* before wikilinks
    # todo: an option to not ignore params?
    assert bpts(b'[[a{{{1}}}]]')['WikiLink'][0] == [0, 12]
    assert bpts(b'[[a|{{{1}}}]]')['WikiLink'][0] == [0, 13]
    # it's hard to tell if the wikilink should span till 13 or 10
    assert bpts(b'[[a{{{1|]]}}}]]')['WikiLink'][0] == [0, 15]  # ?
    # todo: interesting linktrail case
    # the end of span could be at 11, depends on the value of {{{1}}}
    assert bpts(b'[[a|{{{1|]]}}}]]')['WikiLink'][0] == [0, 16]  # ?

    # pfs are *processed* before wikilinks
    # todo: an option to not ignore pfs?
    # the outer one is not a wikilink actually
    assert bpts(b'[[a[[a{{#if:||}}]]]]')['WikiLink'][1] == [3, 18]


def test_comments_in_between_tokens():
    def aw(w: bytes, r: bytes):
        s, e = bpts(w)['WikiLink'][0]
        assert w[s:e] == r

    def afw(w: bytes):
        assert not bpts(w)['WikiLink']

    # test every \0 used in the old WIKILINK_FINDITER
    aw(b'[<!---->[[[w]]', b'[[w]]')  # first \0
    afw(b'[[<!---->[[[w]]')  # second \0
    afw(b'[[[<!---->[[w]]')  # third \0
    aw(b'[<!---->[w]]', b'[<!---->[w]]')  # fourth \0
    afw(b'[[<!---->https://en.wikipedia.org/ w]]')  # fifth \0
    aw(b'[[w]<!---->]', b'[[w]<!---->]')  # sixth \0
    aw(b'[[w|[<!---->[w]]', b'[<!---->[w]]')  # seventh \0
    aw(b'[[a|[b]<!---->] c]]', b'[[a|[b]<!---->]')  # 8th 11th 12th \0
    aw(b'[[a|[b]<!---->]]', b'[[a|[b]<!---->]]')  # ninth \0
    aw(b'[[a|[b]]<!---->]', b'[[a|[b]]<!---->]')  # tenth \0


@mark.xfail
def test_t253476():
    assert not bpts(b'[[A (D)|]<!---->]')['WikiLink']


@mark.xfail
def test_t253476_2():
    assert not bpts(b'[<!---->[A (D)|]]')['WikiLink']


def test_wikilinks_and_params_cannot_overlap():
    # wikilink prevents param
    d = bpts(b'{{{P|[[a|b}}}]]')
    assert d['WikiLink'] == [[5, 15]]
    assert not d['Parameter']
    # param prevents wikilink
    d = bpts(b'[[a|{{{P|]]b}}}')
    assert d['Parameter'] == [[4, 15]]
    assert not d['WikiLink']
    # -> whichever comes last is processes first


def test_param_containing_curly_brace():
    assert bpts(b'{{{p|{}}}')['Parameter'] == [[0, 9]]
    assert bpts(b'{{{p|}d}}}')['Parameter'] == [[0, 10]]


def test_comment_in_template_name():
    assert bpts(b'{{t\n<!---->|p}}')['Template'] == [[0, 15]]
    assert bpts(b'{{<!---->\nt|p}}')['Template'] == [[0, 15]]
    assert not bpts(b'{{_<!---->}}')['Template']
