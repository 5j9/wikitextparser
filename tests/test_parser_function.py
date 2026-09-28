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
    t = ParserFunction('{{#pf}}')
    t.set_arg('1', 'b', ignore_equals=True)
    assert '{{#pf:b}}' == t.string
    t = ParserFunction('{{#pf:a}}')
    t.set_arg('1', 'b', ignore_equals=True)
    assert '{{#pf:b}}' == t.string
    t = ParserFunction('{{#pf:a|b}}')
    t.set_arg('2', 'c', ignore_equals=True)
    assert '{{#pf:a|c}}' == t.string
    t = ParserFunction('{{#pf:a|b}}')
    t.set_arg('2', 'c', True, ignore_equals=True)
    assert '{{#pf:a|c}}' == t.string
    t = ParserFunction('{{#pf:a|b}}')
    t.set_arg('2', 'c', True, ignore_equals=False)
    assert '{{#pf:a|c}}' == t.string
    t = ParserFunction('{{#pf:a|b=x}}')
    t.set_arg('2', 'c', True, ignore_equals=True)
    assert '{{#pf:a|c}}' == t.string
    with raises(ValueError):
        t = ParserFunction('{{#pf:a|b}}')
        t.set_arg('4', 'c', ignore_equals=True)
    with raises(ValueError):
        t = ParserFunction('{{#pf:a|b}}')
        t.set_arg('xd', 'c', ignore_equals=True)
    t = ParserFunction('{{#pf:a|b}}')
    t.set_arg('4', 'c', ignore_equals=False)
    assert '{{#pf:a|b|4=c}}' == t.string
    t = ParserFunction('{{#pf:a|b}}')
    t.set_arg('xd', 'c', ignore_equals=False)
    assert '{{#pf:a|b|xd=c}}' == t.string
    t = ParserFunction('{{#pf:a|b}}')
    with raises(ValueError):
        t.set_arg('2', 'c', False, ignore_equals=False)
        assert '{{#pf:a|b|2=c}}' == t.string
    t = ParserFunction('{{#pf:a|b}}')
    with raises(ValueError):
        t.set_arg('3', 'c', None, None, None, True, ignore_equals=True)
        assert '{{#pf:a|b|c}}' == t.string


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


def test_get_last_positional_index():
    t = ParserFunction('{{#pf:a|b|c=d}}')
    assert t.get_last_positional_index(ignore_equals=False) == 2
    assert t.get_last_positional_index(ignore_equals=True) == 3


def test_ignore_equals_rejects_invalid_positional_indices():
    t = ParserFunction('{{#pf:a|b}}')

    assert t.get_arg('0', ignore_equals=True) is None
    assert t.get_arg('-1', ignore_equals=True) is None
    assert t.get_arg('3', ignore_equals=True) is None

    assert not t.has_arg('0', ignore_equals=True)
    assert not t.has_arg('-1', ignore_equals=True)
