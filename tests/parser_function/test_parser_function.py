from pytest import mark, raises

from wikitextparser import ParserFunction, WikiText

# noinspection PyProtectedMember
from wikitextparser._wikitext import WS


def test_parser_function():
    assert (
        repr(ParserFunction('{{#if:a|{{#if:b|c}}}}').parser_functions[0])
        == "ParserFunction('{{#if:b|c}}')"
    )


def test_args_containing_braces():
    assert 4 == len(ParserFunction('{{#pf:\n{|2\n|3\n|}\n}}').arguments)


def test_repr():
    assert (
        repr(ParserFunction('{{#if:a|b}}')) == "ParserFunction('{{#if:a|b}}')"
    )


def test_name_and_args():
    f = ParserFunction('{{ #if: test | true | false }}')
    assert ' #if' == f.name
    args = f.arguments
    assert [': test ', '| true ', '| false '] == [a.string for a in args]
    assert args[0].name == '1'
    assert args[2].name == '3'


def test_set_name():
    pf = ParserFunction('{{   #if: test | true | false }}')
    pf.name = pf.name.strip(WS)
    assert '{{#if: test | true | false }}' == pf.string


def test_normal_name():
    assert '#u ' == ParserFunction('{{ #u :a}}').normal_name()
    assert '#u ' == ParserFunction('{{ #U :a}}').normal_name()
    assert '#a_b' == ParserFunction('{{#a_b:}}').normal_name()
    assert '#t#a' == ParserFunction('{{#t#a:a}}').normal_name()
    assert '#a___b' == ParserFunction('{{#A___B:}}').normal_name()
    assert '#t' == ParserFunction('{{<!---->\n #T<!---->:}}').normal_name()


def test_pipes_inside_params_or_templates():
    pf = ParserFunction('{{ #if: test | {{ text | aaa }} }}')
    assert [] == pf.parameters
    assert 2 == len(pf.arguments)
    pf = ParserFunction('{{ #if: test | {{{ text | aaa }}} }}')
    assert 1 == len(pf.parameters)
    assert 2 == len(pf.arguments)


def test_strip_empty_wikilink():
    pf = ParserFunction('{{ #if: test | [[|Alt]] }}')
    assert 2 == len(pf.arguments)


def test_default_parser_function_without_hash_sign():
    assert 1 == len(WikiText('{{formatnum:text|R}}').parser_functions)


@mark.xfail
def test_parser_function_alias_without_hash_sign():
    """‍`آرایش‌عدد` is an alias for `formatnum` on Persian Wikipedia.

    See: //translatewiki.net/wiki/MediaWiki:Sp-translate-data-MagicWords/fa
    """
    assert 1 == len(WikiText('{{آرایش‌عدد:text|R}}').parser_functions)


def test_argument_with_existing_span():
    """Test when the span is already in type_to_spans."""
    pf = WikiText('{{formatnum:text}}').parser_functions[0]
    assert pf.arguments[0].value == 'text'
    assert pf.arguments[0].value == 'text'
    assert pf.string == '{{formatnum:text}}'


def test_tag_containing_pipe():
    assert len(ParserFunction('{{text|a<s |>b</s>c}}').arguments) == 1


def test_equal_in_if_expression():
    pf = ParserFunction('{{#if: 2==2 | yes | no }}')
    pf.set_arg('1', '3', ignore_equals=True)
    assert pf.string == '{{#if:3| yes | no }}'


def test_has_arg():
    has_arg = ParserFunction('{{#pf:a|b=c}}').has_arg
    assert has_arg('1', ignore_equals=True) is True
    assert has_arg('1', 'a', ignore_equals=True) is True
    assert has_arg('b', ignore_equals=True) is False
    assert has_arg('b', 'c', ignore_equals=True) is False
    assert has_arg('2', ignore_equals=True) is True
    assert has_arg('2', 'b=c', ignore_equals=True) is True
    assert has_arg('c', ignore_equals=True) is False
    assert has_arg('b', 'd', ignore_equals=True) is False


def test_get_arg():
    get_arg = ParserFunction('{{#pf:a|b=c}}').get_arg
    assert ':a' == get_arg('1', ignore_equals=True).string  # type: ignore
    assert get_arg('c', ignore_equals=True) is None


def test_name_contains_a_param_with_default():
    t = ParserFunction('{{#pf {{{p1|d1}}} : {{{p2|d2}}} }}')
    assert '#pf {{{p1|d1}}} ' == t.name
    assert ': {{{p2|d2}}} ' == t.arguments[0].string
    t.name = 'g'
    assert 'g' == t.name


def test_set_arg():
    f = ParserFunction('{{#pf}}')
    f.set_arg('1', 'b', ignore_equals=True)
    assert '{{#pf:b}}' == f.string
    f = ParserFunction('{{#pf:a}}')
    f.set_arg('1', 'b', ignore_equals=True)
    assert '{{#pf:b}}' == f.string
    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg('2', 'c', ignore_equals=True)
    assert '{{#pf:a|c}}' == f.string
    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg('2', 'c', True, ignore_equals=True)
    assert '{{#pf:a|c}}' == f.string
    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg('2', 'c', True, ignore_equals=False)
    assert '{{#pf:a|c}}' == f.string
    f = ParserFunction('{{#pf:a|b=x}}')
    f.set_arg('2', 'c', True, ignore_equals=True)
    assert '{{#pf:a|c}}' == f.string
    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg('4', 'c', ignore_equals=False)
    assert '{{#pf:a|b|4=c}}' == f.string
    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg('xd', 'c', ignore_equals=False)
    assert '{{#pf:a|b|xd=c}}' == f.string


def test_set_arg_ignore_equals_keyword_name():
    f = ParserFunction('{{#f:a|b}}')
    f.set_arg('xd', 'c', ignore_equals=True)
    assert f.string == '{{#f:a|b|xd=c}}'


def test_set_arg_no_ignore_equals_non_existing_positional_name():
    f = ParserFunction('{{#f:a|b}}')
    f.set_arg('4', 'c', ignore_equals=False)
    assert f.string == '{{#f:a|b|4=c}}'


def test_set_arg_ignore_equals_non_existing_positional_name():
    f = ParserFunction('{{#f:a|b}}')
    f.set_arg('4', 'c', ignore_equals=True)
    assert f.string == '{{#f:a|b|4=c}}'


def test_converting_positional_to_named_with_set_arg():
    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg('2', 'c', positional=False, ignore_equals=False)
    assert '{{#pf:a|2=c}}' == f.string

    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg('2', 'c', ignore_equals=False)
    assert '{{#pf:a|c}}' == f.string

    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg('2', 'c', positional=True, ignore_equals=False)
    assert '{{#pf:a|c}}' == f.string


def test_set_arg_preserve_spacing_ignore_equals():
    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg('3', 'c', preserve_spacing=True, ignore_equals=True)
    assert '{{#pf:a|b|c}}' == f.string


def test_set_arg_preserve_spacing_no_ignore_equals_no_positional():
    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg('3', 'c', preserve_spacing=True, ignore_equals=False)
    assert '{{#pf:a|b|c}}' == f.string


def test_set_arg_preserve_spacing_no_ignore_equals_positional():
    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg(
        '3', 'c', preserve_spacing=True, ignore_equals=False, positional=True
    )
    assert '{{#pf:a|b|c}}' == f.string


def test_set_arg_preserve_spacing_no_ignore_equals_false_positional():
    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg(
        '3', 'c', preserve_spacing=True, ignore_equals=False, positional=False
    )
    assert '{{#pf:a|b|3=c}}' == f.string


def test_del_arg():
    t = ParserFunction('{{#pf:a}}')
    t.del_arg('1', ignore_equals=True)
    assert '{{#pf}}' == t.string
    t = ParserFunction('{{#pf:a|b}}')
    t.del_arg('2', ignore_equals=True)
    assert '{{#pf:a}}' == t.string


def test_lists():
    l1, l2 = ParserFunction('{{#pf:*a\n*b|*c\n*d}}').get_lists()
    assert l1.items == ['a', 'b']
    assert l2.items == ['c', 'd']
    assert ParserFunction('{{#pf:;https://a.b :d}}').get_lists('[;:]')[
        0
    ].items == [
        'https://a.b ',
        'd',
    ]


def test_ignore_equals_rejects_invalid_indices():
    t = ParserFunction('{{#pf:a|b}}')

    assert t.get_arg('0', ignore_equals=True) is None
    assert t.get_arg('-1', ignore_equals=True) is None
    assert t.get_arg('3', ignore_equals=True) is None

    assert not t.has_arg('0', ignore_equals=True)
    assert not t.has_arg('-1', ignore_equals=True)


def test_removing_first_positional_arg():
    f = ParserFunction('{{#f:a=a|b=b|c=c}}')
    f.del_arg('1', ignore_equals=True)
    assert f.string == '{{#f:b=b|c=c}}'


def test_removing_first_keyword_arg():
    f = ParserFunction('{{#f:a=a|b=b|c=c}}')
    f.del_arg('a', ignore_equals=False)
    assert f.string == '{{#f:b=b|c=c}}'


def test_get_the_just_set():
    f = ParserFunction('{{#f:a|b}}')
    f.set_arg('xd', 'c', ignore_equals=True)  # you named it 'xd'
    assert f.string == '{{#f:a|b|xd=c}}'
    # but it's not findable by that name
    assert f.get_arg('xd', ignore_equals=True) is None
    arg = f.get_arg('xd', ignore_equals=False)
    assert arg is not None and arg.string == '|xd=c'
    arg = f.get_arg('3', ignore_equals=True)
    assert arg is not None
    assert arg.string == '|xd=c'


def test_set_arg_ignore_equals_numeric_keyword_add_is_not_positionally_findable():
    f = ParserFunction('{{#pf:a|b}}')
    f.set_arg('4', 'c', ignore_equals=True)  # keyword add
    assert f.string == '{{#pf:a|b|4=c}}'
    assert f.get_arg('4', ignore_equals=True) is None  # index 4 doesn't exist
    arg = f.get_arg('4', ignore_equals=False)
    assert arg is not None and arg.string == '|4=c'
    # positional=True is strict and raises for a non-next index
    with raises(ValueError):
        ParserFunction('{{#pf:a|b}}').set_arg(
            '4', 'c', ignore_equals=True, positional=True
        )


def test_set_arg_preserve_spacing_single_arg_pf():
    f = ParserFunction('{{#f:a}}')
    f.set_arg('2', 'x', preserve_spacing=True, ignore_equals=True)
    assert f.string == '{{#f:a|x}}'


def test_del_arg_ignore_equals_numeric_boundary_names():
    # get_arg/has_arg use to_index (int-based); del_arg must agree.
    for name in ('01', '+1', '\uff11'):  # '01', '+1', fullwidth '１'
        f = ParserFunction('{{#pf:a|b|c}}')
        assert f.get_arg(name, ignore_equals=True) is None
        assert f.has_arg(name, ignore_equals=True) is False
        f.del_arg(name, ignore_equals=True)
        assert f.string == '{{#pf:a|b|c}}', name

    # out-of-range / invalid indices: get_arg is None, del_arg is a no-op
    for name in ('0', '-1', '4'):
        f = ParserFunction('{{#pf:a|b|c}}')
        assert f.get_arg(name, ignore_equals=True) is None
        f.del_arg(name, ignore_equals=True)
        assert f.string == '{{#pf:a|b|c}}', name


def test_ignore_equals_canonical_indices_only():
    # Only canonical decimal strings ('1', '2', ...) address positional
    # arguments. Forms that Python's int() would accept but MediaWiki treats
    # as literal names ('01', '+1', fullwidth '１') must
    # NOT be treated as indices by get/has/del/set. The only exception is
    # whitespace-padded name. Since a name is always stripped in MW, i.e.
    # positional args have no WS and keyword args are stripped, we can ignore
    # WS for lookup.
    bad_aliases = ('01', '+1', '\uff11', '1_0', '1.0')
    for name in bad_aliases:
        f = ParserFunction('{{#pf:a|b|c}}')
        assert f.get_arg(name, ignore_equals=True) is None, name
        assert f.has_arg(name, ignore_equals=True) is False, name
        f.del_arg(name, ignore_equals=True)
        assert f.string == '{{#pf:a|b|c}}', name
    for name in (' 1 ', '1 ', ' 1'):
        f = ParserFunction('{{#pf:a|b|c}}')
        a = f.get_arg(name, ignore_equals=True)
        assert a is not None and a.value == 'a'
        assert f.has_arg(name, ignore_equals=True) is True, name
        f.del_arg(name, ignore_equals=True)
        assert f.string == '{{#pf:b|c}}', name
    # Invalid / out-of-range indices behave the same way.
    for name in ('0', '-1', '4', '', 'v'):
        f = ParserFunction('{{#pf:a|b|c}}')
        assert f.get_arg(name, ignore_equals=True) is None, name
        f.del_arg(name, ignore_equals=True)
        assert f.string == '{{#pf:a|b|c}}', name

    # Canonical indices do address positional args, consistently across
    # get/has/del.
    for name, arg in (('1', ':a'), ('2', '|b'), ('3', '|c')):
        f = ParserFunction('{{#pf:a|b|c}}')
        a = f.get_arg(name, ignore_equals=True)
        assert a is not None and a.string == arg, name
        assert f.has_arg(name, ignore_equals=True) is True, name
        f2 = ParserFunction('{{#pf:a|b|c}}')
        f2.del_arg(name, ignore_equals=True)
        remaining = ParserFunction(f2.string).arguments
        assert arg not in [a.string for a in remaining], name


def test_del_arg_ignore_equals_promotes_separator_with_whitespace_and_nested():
    # Deleting the first PF arg promotes the next separator to ':', even
    # when the second arg has surrounding whitespace, a comment, or a
    # nested template, and even when the deleted arg is long.
    cases = {
        '{{#f:a |b=c}}': '{{#f:b=c}}',
        '{{#f:a <!--x-->|b=c}}': '{{#f:b=c}}',
        '{{#f:a|{{u|v}}=c}}': '{{#f:{{u|v}}=c}}',
        '{{#f:a| b = c }}': '{{#f: b = c }}',
        '{{#f:aaaaaaaaaa|b=c}}': '{{#f:b=c}}',
        '{{#f:a|b|c|d}}': '{{#f:b|c|d}}',
    }
    for src, expected in cases.items():
        f = ParserFunction(src)
        f.del_arg('1', ignore_equals=True)
        assert f.string == expected, src


def test_del_arg_no_ignore_equals_promotes_second_arg():
    f = ParserFunction('{{#f:a=1|b=2}}')
    f.del_arg('a', ignore_equals=False)
    assert f.string == '{{#f:b=2}}'
