from pytest import raises

from wikitextparser import Argument, Template, parse


def test_basics():
    a = Argument('| a = b ')
    assert ' a ' == a.name
    assert ' b ' == a.value
    assert not a.positional
    assert repr(a) == "Argument('| a = b ')"


def test_anonymous_parameter():
    a = Argument('| a ')
    assert '1' == a.name
    assert ' a ' == a.value


def test_set_name():
    a = Argument('| a = b ')
    a.name = ' c '
    assert '| c = b ' == a.string


def test_set_name_at_subspan_boundary():
    a = Argument('|{{ a }}={{ b }}')
    a.name = ' c '
    assert '| c ={{ b }}' == a.string
    assert '{{ b }}' == a.value


def test_set_name_for_positional_args():
    a = Argument('| b ')
    a.name = a.name
    assert '|1= b ' == a.string


def test_value_setter():
    a = Argument('| a = b ')
    a.value = ' c '
    assert '| a = c ' == a.string


def test_removing_last_arg_should_not_effect_the_others():
    a, b, c = Template('{{t|1=v|v|1=v}}').arguments
    del c[:]
    assert '|1=v' == a.string
    assert '|v' == b.string


def test_nowikied_arg():
    a = Argument('|<nowiki>1=3</nowiki>')
    assert a.positional is True
    assert '1' == a.name
    assert '<nowiki>1=3</nowiki>' == a.value


def test_value_after_convertion_of_positional_to_keywordk():
    a = Argument("""|{{{a|{{{b}}}}}}""")
    a.name = ' 1 '
    assert '{{{a|{{{b}}}}}}' == a.value


def test_name_of_positionals():
    assert ['1', '2', '3'] == [
        a.name for a in parse('{{t|a|b|c}}').templates[0].arguments
    ]


def test_dont_confuse_subspan_equal_with_keyword_arg_equal():
    p = parse('{{text| {{text|1=first}} | b }}')
    a0, a1 = p.templates[0].arguments
    assert ' {{text|1=first}} ' == a0.value
    assert '1' == a0.name
    assert ' b ' == a1.value
    assert '2' == a1.name


def test_setting_positionality():
    a = Argument('|1=v')
    a.positional = False
    assert '|1=v' == a.string
    a.positional = True
    assert '|v' == a.string
    a.positional = True
    assert '|v' == a.string
    raises(ValueError, setattr, a, 'positional', False)


def test_parser_functions_at_the_end():
    pfs = Argument('| 1 ={{#ifeq:||yes}}').parser_functions
    assert 1 == len(pfs)


def test_section_not_keyword_arg():
    a = Argument('|1=foo\n== section ==\nbar')
    assert (a.name, a.value) == ('1', 'foo\n== section ==\nbar')
    a = Argument('|\n==t==\nx')
    assert (a.name, a.value) == ('1', '\n==t==\nx')
    # Following cases is not treated as a section headings
    a = Argument('|==1==\n')
    assert (a.name, a.value) == ('', '=1==\n')
    # Todo: Prevents forming a template!
    # a = Argument('|\n==1==')
    # assert
    #     (a.name == a.value), ('1', '\n==1==')


def test_argument_name_not_external_link():
    # MediaWiki parses template parameters before external links,
    # so it goes with the named parameter in both cases.
    a = Argument('|[http://example.com?foo=bar]')
    assert (a.name, a.value) == ('[http://example.com?foo', 'bar]')
    a = Argument('|http://example.com?foo=bar')
    assert (a.name, a.value) == ('http://example.com?foo', 'bar')


def test_lists():
    assert Argument('|list=*a\n*b').get_lists()[0].items == ['a', 'b']
    assert Argument('|lst= *a\n*b').get_lists()[0].items == ['a', 'b']
    assert Argument('|*a\n*b').get_lists()[0].items == ['a', 'b']
    # the space at the beginning of a positional argument should not be
    # ignored. (?)
    assert Argument('| *a\n*b').get_lists()[0].items == ['b']


def test_equal_sign_in_val():
    a, c = Template('{{t|a==b|c}}').arguments
    assert a.value == '=b'
    assert c.name == '1'
