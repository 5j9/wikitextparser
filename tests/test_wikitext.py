from operator import attrgetter

from pytest import warns, mark, raises

from wikitextparser import WikiText, parse, Template, ParserFunction,\
    remove_markup
# noinspection PyProtectedMember
from wikitextparser._wikitext import WS, DeadIndexError, DEAD_INDEX


# basics  of WikiText

def test_len():
    t1, t2 = WikiText('{{t1|{{t2}}}}').templates
    assert len(t2) == 6
    assert len(t1) == 13


def test_repr():
    assert repr(parse('')) == "WikiText('')"


def test_call():
    t1, t2 = WikiText('{{t1|{{t2}}}}').templates
    assert t2(2) == 't'
    assert t2(2, 4) == 't2'
    assert t2(-4, -2) == 't2'
    assert t2(-3) == '2'


def test_setitem():
    s = '{{t1|{{t2}}}}'
    wt = WikiText(s)
    t1, t2 = wt.templates
    t2[2] = 'a'
    assert t2.string == '{{a2}}'
    assert t1.string == '{{t1|{{a2}}}}'
    t2[2] = 'bb'
    assert t2.string == '{{bb2}}'
    assert t1.string == '{{t1|{{bb2}}}}'
    t2[2:5] = 'ccc'
    assert t2.string == '{{ccc}}'
    assert t1.string == '{{t1|{{ccc}}}}'
    t2[-5:-2] = 'd'
    assert wt.string == '{{t1|{{d}}}}'
    t2[-3] = 'e'
    assert wt.string == '{{t1|{{e}}}}'


def test_setitem_errors():
    w = WikiText('a')
    raises(IndexError, w.__setitem__, -2, 'b')
    assert 'a' == w(-9, 9)
    raises(IndexError, w.__setitem__, 1, 'c')
    raises(
        NotImplementedError, w.__setitem__, slice(0, 1, 1), 'd')
    assert 'a' == w(-1, None)
    assert w(-2, None) == 'a'
    raises(IndexError, w.__setitem__, slice(-2, None), 'e')
    assert w(0, -2) == ''
    raises(IndexError, w.__setitem__, slice(0, -2), 'f')
    w[0] = 'gg'
    w[1] = 'hh'
    assert w.string == 'ghh'
    # stop and start in range but stop is before start
    assert w(1, 0) == ''
    raises(IndexError, w.__setitem__, slice(1, 0), 'h')


def test_insert():
    w = WikiText('c')
    w.insert(0, 'a')
    assert w.string == 'ac'
    # Just to show that ``w.insert(i, s)`` is the same as ``w[i:i] = s``:
    v = WikiText('c')
    v[0:0] = 'a'
    assert w.string == v.string
    w.insert(-1, 'b')
    assert w.string == 'abc'
    # Like list.insert, w.insert accepts out of range indexes.
    w.insert(5, 'd')
    assert w.string == 'abcd'
    w.insert(-5, 'z')
    assert w.string == 'zabcd'


def test_overwriting_template_args():
    t = Template('{{t|a|b|c}}')
    c = t.arguments[-1]
    assert '|c' == c.string
    t.string = '{{t|0|a|b|c}}'
    assert '' == c.string
    assert '0' == t.get_arg('1').value
    assert 'c' == t.get_arg('4').value


def test_delitem():
    s = '{{t1|{{t2}}}}'
    wt = WikiText(s)
    t1, t2 = wt.templates
    del t2[3]
    assert wt.string == '{{t1|{{t}}}}'
    del wt[5:10]
    assert t1.string == '{{t1|}}'
    assert t2.string == ''


def test_span():
    assert WikiText('').span == (0, 0)


# __contains__


def test_a_is_actually_in_b():
    b, a = WikiText('{{b|{{a}}}}').templates
    assert a in b
    assert b not in a


def test_a_seems_to_be_in_b_but_in_another_span():
    s = '{{b|{{a}}}}{{a}}'
    b, a1, a2 = WikiText(s).templates
    assert a1 in b
    assert a2 not in b
    assert a2 not in a1
    assert a1 not in a2


def test_a_b_from_different_objects():
    s = '{{b|{{a}}}}'
    b1, a1 = WikiText(s).templates
    b2, a2 = WikiText(s).templates
    assert a1 in b1
    assert a2 in b2
    assert a2 not in b1
    assert a1 not in b2
    assert '{{a}}' in b1
    assert'{{c}}' not in b2


# _shrink_update


def test_stripping_template_name_should_update_its_arg_spans():
    t = Template('{{ t\n |1=2}}')
    a = t.arguments[0]
    t.name = t.name.strip(WS)
    assert '|1=2' == a.string


def test_opcodes_in_spans_should_be_referenced_based_on_self_lststr0():
    template = WikiText('{{a}}{{ b\n|d=}}').templates[1]
    arg = template.arguments[0]
    template.name = template.name.strip(WS)
    assert '|d=' == arg.string


def test_rmstart_s_rmstop_e():
    wt = WikiText('{{t| {{t2|<!--c-->}} }}')
    c = wt.comments[0]
    t = wt.templates[0]
    t[3:14] = ''
    assert c.string == 'c-->'


def test_shrink_more_than_one_subspan():
    wt = WikiText('{{p|[[c1]][[c2]][[c3]]}}')
    wls = wt.wikilinks
    t = wt.templates[0]
    del t[:]
    assert wls[0].string == ''
    assert wls[1].string == ''
    assert wls[2].string == ''


# _close_subspans


def test_spans_are_closed_properly():
    # Real example:
    # ae(
    #     '{{text\n    | 1 = {{#if:\n        \n        | \n    }}\n}}',
    #     WikiText('{{text|1={{#if:|}}\n\n}}').pformat(),
    # )
    wt = WikiText('')
    wt._type_to_spans = {'ParserFunction': [[16, 25, None, None]]}
    # noinspection PyProtectedMember
    wt._close_subspans(16, 27)
    # noinspection PyProtectedMember
    assert not wt._type_to_spans['ParserFunction']


def test_rm_start_not_equal_to_self_start():
    wt = WikiText('t{{a}}')
    wt._type_to_spans = {'Templates': [[1, 6]]}
    # noinspection PyProtectedMember
    wt._close_subspans(5, 6)
    # noinspection PyProtectedMember
    assert wt._type_to_spans == {'Templates': [[1, 6]]}


# _expand_span_update


def test_extending_template_name_should_not_effect_arg_string():
    t = Template('{{t|1=2}}')
    a = t.arguments[0]
    t.name = 't\n    '
    assert '|1=2' == a.string


def test_overwriting_or_extending_selfspan_will_cause_data_loss():
    wt = WikiText('{{t|{{#if:a|b|c}}}}')
    a = wt.templates[0].arguments[0]
    pf = wt.parser_functions[0]
    a.value += ''
    assert '|{{#if:a|b|c}}' == a.string
    # Note that the old parser function is overwritten
    assert '' == pf.string
    pf = a.parser_functions[0]
    a.value = 'a'
    assert '' == pf.string


# WikiText.templates


def test_template_inside_wikilink():
    assert 2 == len(WikiText(
        "{{text |  [[ A | {{text|b}} ]] }}").templates)


def test_wikilink_in_template():
    # todo: merge with test_spans?
    s = "{{text |[[A|}}]]}}"
    ts = str(WikiText(s).templates[0])
    assert s == ts
    assert s == str(WikiText('<ref>{{text |[[A|}}]]}}</ref>').templates[0])


def test_wikilink_containing_closing_braces_in_template():
    s = '{{text|[[  A   |\n|}}[]<>]]\n}}'
    assert s == str(WikiText(s).templates[0])


def test_ignore_comments():
    s1 = "{{text |<!-- }} -->}}"
    assert s1 == str(WikiText(s1).templates[0])


def test_ignore_nowiki():
    assert "{{text |<nowiki>}} A </nowiki> }}" == str(WikiText(
        "{{text |<nowiki>}} A </nowiki> }} B").templates[0])


def test_template_inside_extension_tags():
    s = "<includeonly>{{t}}</includeonly>"
    assert '{{t}}' == str(WikiText(s).templates[0])


def test_dont_parse_source_tag():
    s = "<source>{{t}}</source>"
    assert 0 == len(WikiText(s).templates)


# WikiText.parser_functions


def test_comment_in_parserfunction_name():
    assert 1 == len(WikiText("{{<!--c\n}}-->#if:|a}}").parser_functions)


# WikiText.wikilinks


def test_wikilink_inside_parser_function():
    assert "[[u:{{{3}}}|{{{3}}}]]" == WikiText(
        "{{ #if: {{{3|}}} | [[u:{{{3}}}|{{{3}}}]] }}").wikilinks[0].string


def test_template_in_wikilink():
    s = '[[A|{{text|text}}]]'
    assert s == str(WikiText(s).wikilinks[0])


def test_wikilink_target_may_contain_newline():
    s = '[[A | faf a\n\nfads]]'
    assert s == str(WikiText(s).wikilinks[0])


# WikiText.commonts


def test_getting_comment():
    assert "\n\ncomment\n{{A}}\n" == WikiText(
        'text1 <!--\n\ncomment\n{{A}}\n-->text2').comments[0].contents


# WikiText.external_links


def test_external_links_in_brackets_in_parser_elements():  # 50
    assert parse('{{t|[http://a b]}}').external_links[0].string \
        == '[http://a b]'
    assert parse('<ref>[http://a b]</ref>').external_links[0].string \
        == '[http://a b]'
    assert parse('<ref>[http://a{{b}}]</ref>').external_links[0].string \
        == '[http://a{{b}}]'
    assert parse('{{a|{{b|[http://c{{d}}]}}}}').external_links[0].string \
        == '[http://c{{d}}]'


def test_with_nowiki():
    assert parse('[http://a.b <nowiki>[c]</nowiki>]').external_links[0].text \
           == '<nowiki>[c]</nowiki>'


def test_ipv6_brackets():
    # See:
    # https://en.wikipedia.org/wiki/IPv6_address#Literal_IPv6_addresses_in_network_resource_identifiers
    assert parse(
        'https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/'
    ).external_links[0].url == \
        'https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/'
    el = parse(
        '[https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/ t]'
    ).external_links[0]
    assert el.url == 'https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/'
    assert el.text == 't'
    s = '[//[fe80::1ff:fe23:4567:890a]:443/ t]'
    assert parse(s).external_links[0].string == s


def test_in_template():
    # with brackets
    els = parse('{{text|http://example.com?foo=bar}}').external_links
    assert len(els) == 1
    assert els[0].url == 'http://example.com?foo=bar'
    # without brackets
    els = parse('{{text|[http://example.com?foo=bar]}}').external_links
    assert len(els) == 1
    assert els[0].url == 'http://example.com?foo=bar'


def test_starting_boundary():
    assert not parse('turn:a').external_links


def test_external_links_inside_template():
    t = Template('{{t0|urn:0{{t1|urn:1}}}}')
    # Warning: both urn's are treated ast one.
    # But on a live site this depends on the template outcome.
    assert t.external_links[0].string == 'urn:0'


def test_bare_link():
    s = 'text1 HTTP://mediawiki.org text2'
    wt = WikiText(s)
    assert 'HTTP://mediawiki.org' == str(wt.external_links[0])


def test_with_lable():
    s = 'text1 [http://mediawiki.org MediaWiki] text2'
    el = WikiText(s).external_links[0]
    assert 'http://mediawiki.org' == el.url
    assert 'MediaWiki' == el.text


def test_external_link_match_is_not_in_spans():
    wt = WikiText('t [http://b.b b] t [http://c.c c] t')
    # calculate the links
    links1 = wt.external_links
    wt.insert(0, 't [http://a.a a]')
    links2 = wt.external_links
    assert links1[1].string == '[http://c.c c]'
    assert links2[0].string == '[http://a.a a]'


def test_numbered_link():
    s = 'text1 [http://mediawiki.org] text2'
    wt = WikiText(s)
    assert '[http://mediawiki.org]' == str(wt.external_links[0])


def test_protocol_relative():
    s = 'text1 [//en.wikipedia.org wikipedia] text2'
    wt = WikiText(s)
    assert '[//en.wikipedia.org wikipedia]' == str(wt.external_links[0])


def test_destroy():
    s = 'text1 [//en.wikipedia.org wikipedia] text2'
    wt = WikiText(s)
    del wt.external_links[0].string
    assert 'text1  text2' == str(wt)


def test_wikilink2externallink_fallback():
    p = parse('[[http://example.com foo bar]]')
    assert '[http://example.com foo bar]' == p.external_links[0].string
    assert 0 == len(p.wikilinks)


def test_template_in_link():
    # Note: In reality all assertions depend on the template outcome.
    assert parse('http://example.com{{dead link}}').external_links[0].url == \
        'http://example.com'
    assert parse('http://example.com/foo{{!}}bar').external_links[0].url == \
        'http://example.com/foo'
    assert parse('[http://example.com{{foo}}text]').external_links[0].url == \
        'http://example.com'
    assert parse('[http://example.com{{foo bar}} t]').external_links[0].url ==\
        'http://example.com'


def test_comment_in_external_link():
    # This probably can be fixed, but who uses comments within urls?
    el = parse(
        '[http://example.com/foo<!-- comment -->bar]').external_links[0]
    assert el.text is None
    assert el.url == 'http://example.com/foo<!-- comment -->bar'
    assert parse('[http://example<!-- c -->.com t]').external_links[0].url == \
        'http://example<!-- c -->.com'


def test_no_bare_external_link_within_wiki_links():
    """A wikilink's target may not be an external link."""
    p = parse('[[ https://w|b]]')
    assert 'https://w|b' == p.external_links[0].string
    assert 0 == len(p.wikilinks)


def test_external_link_containing_wikilink():
    s = '[http://a.b [[c]] d]'
    assert parse(s).external_links[0].string == s


def test_bare_external_link_must_have_scheme():
    """Bare external links must have scheme."""
    assert len(parse('//mediawiki.org').external_links) == 0


def test_external_link_with_template():
    """External links may contain templates."""
    assert len(parse('http://example.com/{{text|foo}}').external_links) == 1


def test_external_link_containing_extension_tags():
    s = '[https://www.google.<includeonly>com </includeonly>a]'
    el = parse(s).external_links[0]
    assert str(el) == s
    # Warning: This depends on context and/or requires evaluation.
    assert el.url != 'https://www.google.a'
    s = '[https://www.google.<noinclude>com </noinclude>a]'
    el = parse(s).external_links[0]
    assert str(el) == s
    # Warning: This depends on context and/or requires evaluation.
    assert el.url != 'https://www.google.com'


def test_parser_function_in_external_link():
    assert parse(
        '[urn:u {{<!--c-->#if:a|a}}]'
    ).external_links[0].parser_functions[0].string == '{{<!--c-->#if:a|a}}'
    # Note: Depends on the parser function outcome.
    assert len(parse('[urn:{{#if:a|a|}} t]').external_links) == 0


def test_equal_span_ids():
    p = parse('lead\n== 1 ==\nhttp://wikipedia.org/')
    # noinspection PyProtectedMember
    assert id(p.external_links[0]._span_data) == \
        id(p.sections[1].external_links[0]._span_data)


# WikiText.tables


def test_table_extraction():
    s = '{|class=wikitable\n|a \n|}'
    p = parse(s)
    assert s == p.tables[0].string


def test_table_start_after_space():
    s = '   {|class=wikitable\n|a \n|}'
    p = parse(s)
    assert s.strip(WS) == p.tables[0].string


def test_ignore_comments_before_extracting_tables():
    s = '{|class=wikitable\n|a \n<!-- \n|} \n-->\n|b\n|}'
    p = parse(s)
    assert s == p.tables[0].string


def test_two_tables():
    s = 'text1\n {|\n|a \n|}\ntext2\n{|\n|b\n|}\ntext3\n'
    p = parse(s)
    tables = p.tables
    assert 2 == len(tables)
    assert '{|\n|a \n|}' == tables[0].string
    assert '{|\n|b\n|}' == tables[1].string


def test_nested_tables():
    s = 'text1\n{|class=wikitable\n|a\n|\n' \
            '{|class=wikitable\n|b\n|}\n|}\ntext2'
    p = parse(s)
    assert 1 == len(p.get_tables())  # non-recursive
    tables = p.tables  # recursive
    assert 2 == len(tables)
    table0 = tables[0]
    assert s[6:-6] == table0.string
    assert 0 == table0.nesting_level
    table1 = tables[1]
    assert '{|class=wikitable\n|b\n|}' == table1.string
    assert 1 == table1.nesting_level


def test_tables_in_different_sections():
    s = '{|\n| a\n|}\n\n= s =\n{|\n| b\n|}\n'
    p = parse(s).sections[1]
    assert '{|\n| b\n|}' == p.tables[0].string


def test_match_index_is_none():
    wt = parse('{|\n| b\n|}\n')
    assert len(wt.tables) == 1
    wt.insert(0, '{|\n| a\n|}\n')
    tables = wt.tables
    assert tables[0].string == '{|\n| a\n|}'
    assert tables[1].string == '{|\n| b\n|}'


def test_tables_may_be_indented():
    s = ' ::{|class=wikitable\n|a\n|}'
    wt = parse(s)
    assert wt.tables[0].string == '{|class=wikitable\n|a\n|}'


def test_comments_before_table_start():
    s = ' <!-- c -->::{|class=wikitable\n|a\n|}'
    wt = parse(s)
    assert wt.tables[0].string == '{|class=wikitable\n|a\n|}'


def test_comments_between_indentation():
    s = ':<!-- c -->:{|class=wikitable\n|a\n|}'
    wt = parse(s)
    assert wt.tables[0].string == '{|class=wikitable\n|a\n|}'


def test_comments_between_indentation_after_them():
    assert parse(
        ':<!-- c -->: <!-- c -->{|class=wikitable\n|a\n|}'
    ).tables[0].string == '{|class=wikitable\n|a\n|}'


def test_indentation_cannot_be_inside_nowiki():
    """A very unusual case. It would be OK to have false positives here.

        Also false positive for tables are pretty much harmless here.

        The same thing may happen for tables which start right after a
        templates, parser functions, wiki links, comments, or
        other extension tags.

        """
    assert len(parse(
        '<nowiki>:</nowiki>{|class=wikitable\n|a\n|}').tables) == 0


def test_template_before_or_after_table():
    # This tests self._shadow function.
    s = '{{t|1}}\n{|class=wikitable\n|a\n|}\n{{t|1}}'
    p = parse(s)
    assert [['a']] == p.tables[0].data()


def test_nested_tables_sorted():
    s = (
        '{| style="border: 1px solid black;"\n'
        '| style="border: 1px solid black;" | 0\n'
        '| style="border: 1px solid black; text-align:center;" | 1\n'
        '{| style="border: 2px solid black; background: green;" '
        '<!-- The nested table must be on a new line -->\n'
        '| style="border: 2px solid darkgray;" | 1_G00\n'
        '|-\n'
        '| style="border: 2px solid darkgray;" | 1_G10\n'
        '|}\n'
        '| style="border: 1px solid black; vertical-align: bottom;" '
        '| 2\n'
        '| style="border: 1px solid black; width:100px" |\n'
        '{| style="border: 2px solid black; background: yellow"\n'
        '| style="border: 2px solid darkgray;" | 3_Y00\n'
        '|}\n'
        '{| style="border: 2px solid black; background: Orchid"\n'
        '| style="border: 2px solid darkgray;" | 3_O00\n'
        '| style="border: 2px solid darkgray;" | 3_O01\n'
        '|}\n'
        '| style="border: 1px solid black; width: 50px" |\n'
        '{| style="border: 2px solid black; background:blue; float:left"\n'
        '| style="border: 2px solid darkgray;" | 4_B00\n'
        '|}\n'
        '{| style="border: 2px solid black; background:red; float:right"\n'
        '| style="border: 2px solid darkgray;" | 4_R00\n'
        '|}\n'
        '|}')
    p = parse(s)
    assert 1 == len(p.get_tables())  # non-recursive
    tables = p.tables
    assert tables == sorted(tables, key=attrgetter('_span_data'))
    t0 = tables[0]
    assert s == t0.string
    assert t0.data(strip=False) == [[
        ' 0',
        ' 1\n'
        '{| style="border: 2px solid black; background: green;" '
        '<!-- The nested table must be on a new line -->\n'
        '| style="border: 2px solid darkgray;" | 1_G00\n|-\n'
        '| style="border: 2px solid darkgray;" | 1_G10\n'
        '|}',
        ' 2',
        '\n{| style="border: 2px solid black; background: yellow"\n'
        '| style="border: 2px solid darkgray;" | 3_Y00\n|}\n'
        '{| style="border: 2px solid black; background: Orchid"\n'
        '| style="border: 2px solid darkgray;" | 3_O00\n'
        '| style="border: 2px solid darkgray;" | 3_O01\n|}',
        '\n{| style="border: 2px solid black; background:blue; float:left"'
        '\n| style="border: 2px solid darkgray;" | 4_B00\n|}\n'
        '{| style="border: 2px solid black; background:red; float:right"\n'
        '| style="border: 2px solid darkgray;" | 4_R00\n|}'
    ]]
    assert tables[3].data() == [['3_O00', '3_O01']]
    assert 5 == len(tables[0].tables)
    # noinspection PyProtectedMember
    dynamic_spans = p._type_to_spans['Table']
    assert len(dynamic_spans) == 6
    pre_insert_spans = dynamic_spans[:]
    p.insert(0, '{|\na\n|}\n')
    assert len(dynamic_spans) == 6
    assert 2 == len(p.get_tables())  # non-recursive for the second time
    assert len(dynamic_spans) == 7
    for os, ns in zip(dynamic_spans[1:], pre_insert_spans):
        assert os is ns


# WikiText.nesting_level


def test_a_in_b():
    s = '{{b|{{a}}}}'
    b, a = WikiText(s).templates
    assert 1 == b.nesting_level
    assert 2 == a.nesting_level


# WikiText.pformat


def test_template_with_multi_args():
    wt = WikiText('{{a|b=b|c=c|d=d|e=e}}')
    assert '{{a\n    | b = b\n    | c = c\n    | d = d\n    | e = e\n}}' == \
           wt.pformat()


def test_double_space_indent():
    s = "{{a|b=b|c=c|d=d|e=e}}"
    wt = WikiText(s)
    assert '{{a\n  | b = b\n  | c = c\n  | d = d\n  | e = e\n}}' == \
           wt.pformat('  ')


def test_remove_comments():
    assert '{{a\n  | e = e\n}}' == \
           WikiText('{{a|<!--b=b|c=c|d=d|-->e=e}}').pformat('  ', True)


def test_first_arg_of_tag_is_whitespace_sensitive():
    """The second argument of #tag is an exception.

        See the last warning on [[mw:Help:Magic_words#Miscellaneous]]:
        You must write {{#tag:tagname||attribute1=value1|attribute2=value2}}
        to pass an empty content. No space is permitted in the area reserved
        for content between the pipe characters || before attribute1.
        """
    s = '{{#tag:ref||name="n1"}}'
    wt = WikiText(s)
    assert s == wt.pformat()
    s = '{{#tag:foo| }}'
    wt = WikiText(s)
    assert s == wt.pformat()


def test_invoke():
    """#invoke args are also whitespace-sensitive."""
    s = '{{#invoke:module|func|arg}}'
    wt = WikiText(s)
    assert s == wt.pformat()


def test_on_parserfunction():
    s = "{{#if:c|abcde = f| g=h}}"
    wt = parse(s)
    assert (
        '{{#if:\n'
        '    c\n'
        '    | abcde = f\n'
        '    | g=h\n'
        '}}') == wt.pformat()


def test_parserfunction_with_no_pos_arg():
    s = "{{#switch:case|a|b}}"
    wt = parse(s)
    assert (
        '{{#switch:\n'
        '    case\n'
        '    | a\n'
        '    | b\n'
        '}}') == wt.pformat()


def test_convert_positional_to_keyword_if_possible():
    assert '{{t\n    | 1 = a\n    | 2 = b\n    | 3 = c\n}}' ==\
           parse('{{t|a|b|c}}').pformat()


def test_inconvertible_positionals():
    """Otherwise the second positional arg will also be passed as 1.

        Because of T24555 we can't use "<nowiki/>" to preserve the
        whitespace of positional arguments. On the other hand we can't just
        convert the initial arguments to keyword and keep the rest as
        positional, because that would produce duplicate args as stated above.

        What we *can* do is to either convert all the arguments to keyword
        args if possible, or we should only convert the longest part of
        the tail of arguments that is convertible.

        Use <!--comments--> to align positional arguments where necessary.

        """
    assert (
        '{{t\n'
        '    |a<!--\n'
        ' -->| b <!--\n'
        '-->}}') == parse('{{t|a| b }}').pformat()
    assert (
        '{{t\n'
        '    | a <!--\n'
        ' -->| 2 = b\n'
        '    | 3 = c\n'
        '}}') == parse('{{t| a |b|c}}').pformat()


def test_commented_repformat():
    s = '{{t\n    | a <!--\n -->| 2 = b\n    | 3 = c\n}}'
    assert s == parse(s).pformat()


def test_dont_treat_parser_function_arguments_as_kwargs():
    """The `=` is usually just a part of parameter value.

        Another example: {{fullurl:Category:Top level|action=edit}}.
        """
    assert (
        '{{#if:\n'
        '    true\n'
        '    | <span style="color:Blue;">text</span>\n'
        '}}') == parse(
            '{{#if:true|<span style="color:Blue;">text</span>}}'
        ).pformat()


def test_ignore_zwnj_for_alignment():
    assert (
        '{{ا\n    | نیم\u200cفاصله       = ۱\n    |'
        ' بدون نیم فاصله = ۲\n}}'
    ) == parse('{{ا|نیم‌فاصله=۱|بدون نیم فاصله=۲}}').pformat()


def test_equal_sign_alignment():
    assert (
        '{{t\n'
        '    | long_argument_name = 1\n'
        '    | 2                  = 2\n'
        '}}') == parse('{{t|long_argument_name=1|2=2}}').pformat()


def test_arabic_ligature_lam_with_alef():
    """'ل' + 'ا' creates a ligature with one character width.

        Some terminal emulators do not support this but it's defined in
        Courier New font which is the main (almost only) font used for
        monospaced Persian texts on Windows. Also tested on Arabic Wikipedia.
        """
    assert '{{ا\n    | الف = ۱\n    | لا   = ۲\n}}' == \
           parse('{{ا|الف=۱|لا=۲}}').pformat()


def test_pf_inside_t():
    wt = parse('{{t|a= {{#if:I|I}} }}')
    assert (
        '{{t\n'
        '    | a = {{#if:\n'
        '        I\n'
        '        | I\n'
        '    }}\n'
        '}}') == wt.pformat()


def test_nested_pf_inside_tl():
    wt = parse('{{t1|{{t2}}{{#pf:a}}}}')
    assert (
        '{{t1\n'
        '    | 1 = {{t2}}{{#pf:\n'
        '        a\n'
        '    }}\n'
        '}}') == wt.pformat()


def test_html_tag_equal():
    wt = parse('{{#iferror:<t a="">|yes|no}}')
    assert (
        '{{#iferror:\n'
        '    <t a="">\n'
        '    | yes\n'
        '    | no\n'
        '}}') == wt.pformat()


def test_pformat_tl_directly():
    assert (
        '{{t\n'
        '    | 1 = a\n'
        '}}') == Template('{{t|a}}').pformat()


def test_pformat_pf_directly():
    assert (
        '{{#iferror:\n'
        '    <t a="">\n'
        '    | yes\n'
        '    | no\n'
        '}}') == ParserFunction('{{#iferror:<t a="">|yes|no}}').pformat()


def test_function_inside_template():
    p = parse('{{t|{{#ifeq:||yes}}|a2}}')
    assert (
        '{{t\n'
        '    | 1 = {{#ifeq:\n'
        '        \n'
        '        | \n'
        '        | yes\n'
        '    }}\n'
        '    | 2 = a2\n'
        '}}') == p.pformat()


def test_parser_template_parser():
    p = parse('{{#f:c|e|{{t|a={{#g:b|c}}}}}}')
    assert (
        '{{#f:\n'
        '    c\n'
        '    | e\n'
        '    | {{t\n'
        '        | a = {{#g:\n'
        '            b\n'
        '            | c\n'
        '        }}\n'
        '    }}\n'
        '}}') == p.pformat()


def test_pfromat_first_arg_of_functions():
    assert (
        '{{#time:\n'
        '    {{#if:\n'
        '        1\n'
        '        | y\n'
        '        | \n'
        '    }}\n'
        '}}') == parse('{{#time:{{#if:1|y|}}}}').pformat()


def test_pformat_pf_whitespace():
    assert (
        '{{#if:\n'
        '    a\n'
        '}}') == parse('{{#if: a}}').pformat()
    assert (
        '{{#if:\n'
        '    a\n'
        '}}') == parse('{{#if:a }}').pformat()
    assert (
        '{{#if:\n'
        '    a\n'
        '}}') == parse('{{#if: a }}').pformat()
    assert (
        '{{#if:\n'
        '    a= b\n'
        '}}') == parse('{{#if: a= b }}').pformat()
    assert (
        '{{#if:\n'
        '    a = b\n'
        '}}') == parse('{{#if:a = b }}').pformat()


def test_pformat_tl_whitespace():
    assert '{{t}}' == parse('{{ t }}').pformat()
    assert (
        '{{ {{t}} \n'
        '    | a = b\n'
        '}}') == parse('{{ {{t}}|a=b}}').pformat()


def test_zwnj_is_not_whitespace():
    assert (
        '{{#if:\n'
        '    \u200c\n'
        '}}') == parse('{{#if:\u200c}}').pformat()


def test_colon_in_tl_name():
    assert (
        '{{en:text\n'
        '    |text<!--\n'
        '-->}}') == parse('{{en:text|text}}').pformat()
    assert (
        '{{en:text\n'
        '    |1<!--\n'
        ' -->|2<!--\n'
        '-->}}') == parse('{{en:text|1|2}}').pformat()
    assert (
        '{{en:text\n'
        '    |1<!--\n'
        ' -->| 2=v <!--\n'
        '-->}}') == parse('{{en:text|1|2=v}}').pformat()


def test_parser_function_with_an_empty_argument():
    """The result might seem a little odd, but this is a very rare case.

        The code could benefit from a little improvement.

        """
    assert (
        '{{#rel2abs:\n'
        '    \n'
        '}}') == parse('{{ #rel2abs: }}').pformat()


def test_pf_one_kw_arg():
    assert (
        '{{#expr:\n'
        '    2  =   3\n'
        '}}') == parse('{{#expr: 2  =   3}}').pformat()


def test_pformat_inner_template():
    a, b, c = WikiText('{{a|{{b|{{c}}}}}}').templates
    assert (
        '{{b\n'
        '    | 1 = {{c}}\n'
        '}}') == b.pformat()


def test_repformat():
    """Make sure that pformat won't mutate self."""
    s = '{{a|{{b|{{c}}}}}}'
    a, b, c = WikiText(s).templates
    assert '{{a\n    | 1 = {{b\n        | 1 = {{c}}\n    }}\n}}' == a.pformat()
    # Again:
    assert '{{a\n    | 1 = {{b\n        | 1 = {{c}}\n    }}\n}}' == a.pformat()


def test_pformat_keep_separated():
    """Test that `{{ {{t}} }}` is not converted to `{{{{t}}}}`.

        `{{{{t}}}}` will be interpreted as a parameter with {} around it.

        """
    assert '{{ {{t}} }}' == WikiText('{{{{t}} }}').pformat()


def test_last_arg_last_char_is_newline():
    """Do not add comment_indent when it has no effect."""
    assert '{{text\n    |{{#if:\n        \n    }}\n}}' == \
           WikiText('{{text|{{#if:}}\n}}').pformat()
    assert (
        '{{text\n'
        '    |{{text\n'
        '        |{{#if:\n'
        '            \n'
        '        }}\n'
        '<!--\n'
        ' -->}}\n'
        '}}') == WikiText('{{text|{{text|{{#if:}}\n}}\n}}').pformat()
    assert (
        '{{text\n'
        '    |{{text\n'
        '        |{{#if:\n'
        '            \n'
        '        }}\n'
        '    }}\n'
        '}}') == WikiText('{{text|{{text|{{#if:}}\n    }}\n}}').pformat()
    assert '{{text\n    |a\n    |b\n}}' == WikiText(
        '{{text|a\n    |b\n}}').pformat()
    assert '{{text\n    |a\n    | 2 = b\n}}' == WikiText(
        '{{text|a\n    |2=b\n}}').pformat()
    assert (
        '{{en:text\n'
        '    | n=v\n'
        '}}') == parse('{{en:text|n=v\n}}').pformat()


def test_no_error():
    # the errors were actually found in shrink/insert/extend
    assert parse('{{#f1:{{#f2:}}{{t|}}}}').pformat() == (
        '{{#f1:'
        '\n    {{#f2:'
        '\n        '
        '\n    }}{{t'
        '\n        | 1 = '
        '\n    }}'
        '\n}}')
    assert parse('{{{{#t2:{{{p1|}}}}}{{#t3:{{{p2|}}}\n}}}}\n').pformat() == (
        '{{ {{#t2:'
        '\n        {{{p1|}}}'
        '\n    }}{{#t3:'
        '\n        {{{p2|}}}'
        '\n    }} }}'
        '\n')


# WikiText.sections


def test_grab_the_final_newline_for_the_last_section():
    wt = WikiText('== s ==\nc\n')
    assert '== s ==\nc\n' == wt.sections[1].string


def test_blank_lead():
    wt = WikiText('== s ==\nc\n')
    assert '== s ==\nc\n' == wt.sections[1].string


# Todo: Parser should also work with windows line endings.
@mark.xfail
def test_multiline_with_carriage_return():
    s = 'text\r\n= s =\r\n{|\r\n| a \r\n|}\r\ntext'
    p = parse(s)
    assert 'text\r\n' == p.sections[0].string


def test_inserting_into_sections():
    wt = WikiText('== s1 ==\nc\n')
    s1 = wt.sections[1]
    wt.insert(0, 'c\n== s0 ==\nc\n')
    assert '== s1 ==\nc\n' == s1.string
    assert 'c\n== s0 ==\nc\n== s1 ==\nc\n' == wt.string
    s0 = wt.sections[1]
    assert '== s0 ==\nc\n' == s0.string
    assert 'c\n== s0 ==\nc\n== s1 ==\nc\n' == wt.string
    s1.insert(len(wt.string), '=== s2 ===\nc\n')
    assert (
        'c\n'
        '== s0 ==\n'
        'c\n'
        '== s1 ==\n'
        'c\n'
        '=== s2 ===\n'
        'c\n') == wt.string
    s3 = wt.sections[3]
    assert '=== s2 ===\nc\n' == s3.string


def test_insert_parse():
    """Test that insert parses the inserted part."""
    wt = WikiText('')
    wt.insert(0, '{{t}}')
    assert len(wt.templates) == 1


def test_subsection():
    a = parse('0\n== a ==\n1\n=== b ===\n2\n==== c ====\n3\n').sections[1]
    assert '== a ==\n1\n=== b ===\n2\n==== c ====\n3\n' == a.string
    a_sections = a.sections
    assert '' == a_sections[0].string
    assert '== a ==\n1\n=== b ===\n2\n==== c ====\n3\n' == a_sections[1].string
    b = a_sections[2]
    assert '=== b ===\n2\n==== c ====\n3\n' == b.string
    # Sections use the same span object
    # noinspection PyProtectedMember
    assert b.sections[1]._span_data is b._span_data
    assert '==== c ====\n3\n' == b.sections[2].string


def test_tabs_in_heading():
    """Test that insert parses the inserted part."""
    t = '=\tt\t=\t'
    assert str(parse(t).sections[1]) == t


def test_deleting_a_section_wont_corrupt_others():
    z, a, b, c = parse('=a=\na\n==b==\nb\n==c==\nc').sections
    del b.string
    assert c.string == '==c==\nc'


def test_section_templates():
    """section.templates returns templates only from that section."""
    templates = parse('{{t1}}\n==section==\n{{t2}}').sections[1].templates
    assert len(templates) == 1
    assert templates[0].string == '{{t2}}'


def test_by_heading_pattern():
    wt = parse(
        'lead\n'
        '= h1 =\n'
        '== h2 ==\n'
        't2\n'
        '=== h3 ===\n'
        '3\n'
        '= h =\n'
        'end'
    )
    lead, h1, h2, h3, h = wt.get_sections(include_subsections=False)
    assert lead.string == 'lead\n'
    assert h1.string == '= h1 =\n'
    assert h2.string == '== h2 ==\nt2\n'
    assert h3.string == '=== h3 ===\n3\n'
    assert h.string == '= h =\nend'
    # return the same span when returning same section
    lead_, h1_, h2_, h3_, h_ = wt.get_sections(include_subsections=False)
    # noinspection PyProtectedMember
    assert lead._span_data is lead_._span_data
    # noinspection PyProtectedMember
    assert h._span_data is h_._span_data
    # do not create repeated spans
    # noinspection PyProtectedMember
    assert len(wt._type_to_spans['Section']) == 5
    h1, h = wt.get_sections(include_subsections=False, level=1)
    assert h1.string == '= h1 =\n'
    assert h.string == '= h =\nend'


def test_get_lists_with_no_pattern():
    wikitext = '*a\n;c:d\n#b'
    parsed = parse(wikitext)
    with warns(DeprecationWarning):
        # noinspection PyDeprecation
        lists = parsed.lists()
    assert len(lists) == 3
    assert lists[1].items == ['c', 'd']


def test_multiline_tags():
    i1, i2, i3 = parse(
        '#1<br\n/>{{note}}\n#2<s\n>s</s\n>\n#3').get_lists()[0].items
    assert i1 == '1<br\n/>{{note}}'
    assert i2 == '2<s\n>s</s\n>'
    assert i3 == '3'
    # an invalid tag name containing newlines will break the list
    assert len(parse('#1<br/\n>\n#2<abc\n>\n#3').get_lists()[0].items) == 2


def test_get_lists_deprecation():
    with warns(DeprecationWarning):
        # noinspection PyTypeChecker
        list_ = ParserFunction('{{#if:|*a\n*b}}').get_lists(None)[0]
    with warns(DeprecationWarning):
        # noinspection PyTypeChecker
        list_.get_lists(None)
    with warns(DeprecationWarning):
        # noinspection PyTypeChecker
        list_.sublists(pattern=None)


def test_assume_that_templates_do_not_exist():
    # this is actually an invalid <s> tag on English Wikipedia, i.e the
    # result of {{para}} makes it invalid.
    assert len(parse('<s {{para|a}}></s>').get_tags('s')) == 1


def test_unicode_attr_values():
    wikitext = (
        'متن۱<ref name="نام۱" group="گ">یاد۱</ref>\n\n'
        'متن۲<ref name="نام۲" group="گ">یاد۲</ref>\n\n'
        '<references group="گ"/>')
    parsed = parse(wikitext)
    with warns(DeprecationWarning):
        # noinspection PyDeprecation
        ref1, ref2 = parsed.tags('ref')
    assert ref1.string == '<ref name="نام۱" group="گ">یاد۱</ref>'
    assert ref2.string == '<ref name="نام۲" group="گ">یاد۲</ref>'


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
    parsed = parse(
        'text<ref name="c">citation</ref>\n'
        '<references/>')
    ref, references = parsed.get_tags()
    ref.set_attr('name', 'z')
    assert ref.string == '<ref name="z">citation</ref>'
    assert references.string == '<references/>'


def test_same_tags_end():
    # noinspection PyProtectedMember
    assert WikiText('<s></s><s></s>').get_tags()[0]._span_data[:2] == [0, 7]


def test_pre():  # 46
    assert len(parse('<pre></pre>').get_tags()) == 1


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
        "a<!---->'<!---->'<!---->'<!---->"
        "b<!---->'<!---->'<!---->'<!---->d",
        "'<!---->'<!---->'<!---->b<!---->'<!---->'<!---->'")
    ab("'''b{{a|'''}}", "'''b{{a|'''}}")  # ?
    ab("a'''b{{text|c|d}}e'''f", "'''b{{text|c|d}}e'''")
    ab("{{text|'''b'''}}", "'''b'''")
    ab("{{text|'''b}}", "'''b")  # ?
    ab("[[a|'''b]] c", "'''b")
    ab("{{{PARAM|'''b}}} c", "'''b")  # ?
    assert repr(parse("'''b\na'''c").get_bolds()) ==\
        """[Bold("'''b"), Bold("'''c")]"""
    ab("'''<S>b</S>'''", "'''<S>b</S>'''")
    ab("'''b<S>r'''c</S>", "'''b<S>r'''")
    ab("'''''b'''i", "'''b'''")
    assert repr(parse("'''b<ref>r'''c</ref>a").get_bolds()) == \
        """[Bold("'''b<ref>r'''c</ref>a"), Bold("'''c")]"""
    assert repr(parse("'''b<ref>r'''c</ref>a").get_bolds(False)) ==\
        """[Bold("'''b<ref>r'''c</ref>a")]"""
    ab("'''b{{{p|'''}}}", "'''b{{{p|'''}}}")  # ?
    ab("<nowiki>'''a</nowiki>'''b", "'''b")
    anb("' ' ' a ' ' '")
    ab("x''' '''y", "''' '''")
    ab("x''''''y", "'''y")
    ab("{{text|{{text|'''b'''}}}}", "'''b'''")


def test_extension_tags():
    a, b = parse('<ref/><ref/>')._extension_tags
    assert a._extension_tags == []


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
        "A<!---->"
        "'<!---->'<!---->'<!---->'<!---->'"
        "<!---->i<!---->"
        "'<!---->'<!---->'<!---->'<!---->'"
        "<!---->B",
        "'<!---->'<!---->'<!---->'<!---->'"
        "<!---->i<!---->"
        "'<!---->'<!---->'<!---->'<!---->'")
    ai("''' ''i'''", "''i'''")


def test_bold_italic_index_change():
    p = parse("'''b1''' ''i1'' '''b2'''")
    b1, b2 = p.get_bolds(recursive=False)
    i1 = p.get_italics(recursive=False)[0]
    b1.text = '1'
    assert p.string == "'''1''' ''i1'' '''b2'''"
    assert i1.string == "''i1''"
    assert b2.text == "b2"


def test_ancestors_and_parent():
    parsed = parse('{{a|{{#if:{{b{{c<!---->}}}}}}}}')
    assert parsed.parent() is None
    assert parsed.ancestors() == []
    c = parsed.comments[0]
    c_parent = c.parent()
    assert c_parent.string == '{{c<!---->}}'
    assert c_parent.parent().string == '{{b{{c<!---->}}}}'
    assert len(c.ancestors()) == 4
    assert len(c.ancestors(type_='Template')) == 3
    assert len(c.ancestors(type_='ParserFunction')) == 1
    t = Template('{{a}}')
    assert t.ancestors() == []
    assert t.parent() is None


def test_not_every_sooner_starting_span_is_a_parent():
    a, b = parse('[[a]][[b]]').wikilinks
    assert b.ancestors() == []


def test_italic_end_token():
    assert parse("''i''").get_italics(False)[0].end_token is True


def test_plaintext():
    def ap(s, p):
        assert parse(s).plain_text() == p
    ap("<span>a<small>b</small>c</span>", 'abc')
    ap("<ref>''w''</ref>", 'w')  # could be '' as well
    ap("[[file:a.jpg|[[w]]]]", '')
    ap('<span>a</span>b<span>c</span>', 'abc')  # 39
    ap('{{a}}b{{c}}', 'b')  # 39
    ap('t [[a|b]] t', 't b t')
    ap('t [[a]] t', 't a t')
    ap('&Sigma; &#931; &#x3a3; Σ', 'Σ Σ Σ Σ')
    ap('[https://wikimedia.org/ wm]', 'wm')
    ap('[https://wikimedia.org/]', '')
    ap('<s>text</s>', 'text')
    ap('{{template|argument}}', '')
    ap('{{#if:a|y|n}}', '')
    ap("'''b'''", 'b')
    ap("''i''", 'i')
    ap("{{{a}}}", '')
    ap("{{{1|a}}}", 'a')


def test_plain_text_should_not_mutate():  # 40
    p = parse('[[a]][[b]]')
    a, b = p.wikilinks
    assert a.plain_text() == 'a'
    assert b.plain_text() == 'b'


def test_remove_markup():
    assert remove_markup("''a'' {{b}} c <!----> '''d'''") == "a  c  d"


def test_do_not_return_duplicate_bolds_italics():  # 42
    assert len(parse("{{a|{{b|'''c'''}}}}").get_bolds()) == 1
    assert len(parse("[[file:a.jpg|[[b|''c'']]]]").get_italics()) == 1


def test_do_not_include_end_tag():
    assert parse('<div>[http://a]</div>').plain_text() == ''


def test_mutating_invalid_link():
    p = parse('a [[file:1.jpg|[[w]]]]')
    w0, w1 = p.wikilinks
    w0.string = '[[]]'
    with raises(DeadIndexError):
        w1.string = 'd'
    assert p.string == 'a [[]]'
    assert w0.string == '[[]]'
    assert w1.string == ''


def test_dead_index():
    assert repr(DEAD_INDEX) == 'DeadIndex()'


def test_nested_bold_or_italic_plain_text():
    assert remove_markup("''[[a|''b'']]") == 'b'
    assert remove_markup("'''[[a|'''b''']]") == 'b'


def test_multiline_italics():
    a, b = parse("'''a''\n'''b''").get_italics()
    assert a.string == "''a''"
    assert b.string == "''b''"


def test_first_single_letter_word_condition_in_doquotes():
    b, = parse("'''a'' b'''c'' '''d''").get_bolds()
    assert b.string == "'''a'' b'''c'' '''"


def test_first_space_condition_in_doquotes_not_used():
    b, = parse("'''a'' '''b'' '''c''").get_bolds()
    assert b.string == "'''b'' '''"


def test_first_space_condition_in_balanced_quotes_shadow():
    b, = parse("a '''b'' '''c'' '''d''").get_bolds()
    assert b.string == "'''c'' '''"


def test_ignore_head_apostrophes():
    b, = parse("''''''''a").get_italics()
    assert b.string == "'''''a"


def test_bold_ends_4_apostrophes():
    b, = parse("''a'''b''''").get_bolds()
    assert b.text == "b'"


def test_single_bold_italic():
    i, = parse("'''''a").get_italics()
    assert i.text == "'''a"
