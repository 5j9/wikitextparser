from pytest import raises, warns

from wikitextparser import Template, WikiText, parse

# noinspection PyProtectedMember
from wikitextparser._wikitext import DEAD_INDEX, WS, DeadIndexError

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
    raises(NotImplementedError, w.__setitem__, slice(0, 1, 1), 'd')
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
    del wt[5:10]  # {{t}}
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
    assert '{{c}}' not in b2


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
    assert 2 == len(WikiText('{{text |  [[ A | {{text|b}} ]] }}').templates)


def test_wikilink_in_template():
    # todo: merge with test_spans?
    s = '{{text |[[A|}}]]}}'
    ts = str(WikiText(s).templates[0])
    assert s == ts
    assert s == str(WikiText('<ref>{{text |[[A|}}]]}}</ref>').templates[0])


def test_wikilink_containing_closing_braces_in_template():
    s = '{{text|[[  A   |\n|}}[]<>]]\n}}'
    assert s == str(WikiText(s).templates[0])


def test_ignore_comments():
    s1 = '{{text |<!-- }} -->}}'
    assert s1 == str(WikiText(s1).templates[0])


def test_ignore_nowiki():
    assert '{{text |<nowiki>}} A </nowiki> }}' == str(
        WikiText('{{text |<nowiki>}} A </nowiki> }} B').templates[0]
    )


def test_template_inside_extension_tags():
    s = '<includeonly>{{t}}</includeonly>'
    assert '{{t}}' == str(WikiText(s).templates[0])


def test_dont_parse_source_tag():
    assert 0 == len(WikiText('<source>{{t}}</source>').templates)


# WikiText.parser_functions


def test_comment_in_parserfunction_name():
    assert 1 == len(WikiText('{{<!--c\n}}-->#if:|a}}').parser_functions)


# WikiText.wikilinks


def test_wikilink_inside_parser_function():
    assert (
        '[[u:{{{3}}}|{{{3}}}]]'
        == WikiText('{{ #if: {{{3|}}} | [[u:{{{3}}}|{{{3}}}]] }}')
        .wikilinks[0]
        .string
    )


def test_template_in_wikilink():
    s = '[[A|{{text|text}}]]'
    assert s == str(WikiText(s).wikilinks[0])


def test_wikilink_target_may_contain_newline():
    s = '[[A | faf a\n\nfads]]'
    assert s == str(WikiText(s).wikilinks[0])


# WikiText.comments


def test_getting_comment():
    assert (
        '\n\nc\n{{A}}\n'
        == WikiText('1 <!--\n\nc\n{{A}}\n-->2').comments[0].contents
    )


# WikiText.nesting_level


def test_a_in_b():
    s = '{{b|{{a}}}}'
    b, a = WikiText(s).templates
    assert 1 == b.nesting_level
    assert 2 == a.nesting_level


def test_insert_parse():
    """Test that insert parses the inserted part."""
    wt = WikiText('')
    wt.insert(0, '{{t}}')
    assert len(wt.templates) == 1


def test_unicode_attr_values():
    wikitext = (
        'متن۱<ref name="نام۱" group="گ">یاد۱</ref>\n\n'
        'متن۲<ref name="نام۲" group="گ">یاد۲</ref>\n\n'
        '<references group="گ"/>'
    )
    parsed = parse(wikitext)
    ref1, ref2 = parsed.get_tags('ref')
    assert ref1.string == '<ref name="نام۱" group="گ">یاد۱</ref>'
    assert ref2.string == '<ref name="نام۲" group="گ">یاد۲</ref>'


def test_extension_tags():
    a, b = parse('<ref/><ref/>')._extension_tags
    assert a._extension_tags == []


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


def test_wikitext_string_set():  # 66
    parsed = parse('[[a]]')
    wikilink = parsed.wikilinks[0]
    wikilink.insert(0, 'b')
    assert wikilink.string == 'b[[a]]'
    assert parsed.string == 'b[[a]]'
