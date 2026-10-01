from pytest import mark, raises

from wikitextparser import Template


def test_templates():
    assert repr(Template('{{a|b={{c}}}}').templates) == "[Template('{{c}}')]"


def test_args_containing_braces():
    assert 4 == len(Template('{{t|\n{|2\n|3\n|}\n}}').arguments)


def test_named_parameters():
    s = '{{یادکرد کتاب|عنوان = ش{{--}}ش|سال=۱۳۴۵}}'
    assert s == str(Template(s))


def test_ordered_parameters():
    s = '{{example|{{foo}}|bar|2}}'
    assert s == str(Template(s))


def test_ordered_and_named_parameters():
    s = '{{example|para1={{foo}}|bar=3|2}}'
    assert s == str(Template(s))


def test_no_parameters():
    assert "Template('{{template}}')" == repr(Template('{{template}}'))


def test_contains_newlines():
    s = '{{template\n|s=2}}'
    assert s == str(Template(s))


def test_name():
    assert (
        ' wrapper '
        == Template(
            '{{ wrapper | p1 | {{ cite | sp1 | dateformat = ymd}} }}'
        ).name
    )


def test_dont_remove_nonkeyword_argument():
    assert '{{t|a|a}}' == str(Template('{{t|a|a}}'))


def test_set_name():
    t = Template('{{t|a|a}}')
    t.name = ' u '
    assert '{{ u |a|a}}' == t.string


def test_normal_name():
    normal_name = Template('{{ u |a}}').normal_name
    assert 'u' == normal_name()
    assert 'U' == normal_name(capitalize=True)
    assert 'u' == Template('{{ template: u |a}}').normal_name()
    assert 'u' == Template('{{ الگو:u |a}}').normal_name(['الگو'])
    assert 'a b' == Template('{{a_b}}').normal_name()
    assert 't' == Template('{{t#a|a}}').normal_name()
    t = Template('{{ : fa : Template : t  # A }}')
    assert 't' == t.normal_name(code='fa')
    assert 't' == Template('{{ : t |a}}').normal_name()
    assert 'A B' == Template('{{A___B}}').normal_name()
    assert 'T' == Template('{{_<!---->\n _T_ \n<!---->_}}').normal_name()


def test_keyword_and_positional_args():
    assert '1' == Template('{{t|kw=a|1=|pa|kw2=a|pa2}}').arguments[2].name


def test_rm_first_of_dup_args():
    # Remove first of duplicates, keep last
    t = Template('{{template|year=9999|year=2000}}')
    t.rm_first_of_dup_args()
    assert '{{template|year=2000}}' == str(t)
    # Don't remove duplicate positional args in different positions
    s = """{{cite|{{t1}}|{{t1}}}}"""
    t = Template(s)
    t.rm_first_of_dup_args()
    assert s == str(t)
    # Don't remove duplicate subargs
    s1 = '{{i| c = {{g}} |p={{t|h={{g}}}} |q={{t|h={{g}}}}}}'
    t = Template(s1)
    t.rm_first_of_dup_args()
    assert s1 == str(t)
    # test_dont_touch_empty_strings
    t = Template('{{template|url=||work=|accessdate=}}')
    t.rm_first_of_dup_args()
    assert '{{template|url=||work=|accessdate=}}' == str(t)
    # Positional args
    t = Template('{{t|1=v|v}}')
    t.rm_first_of_dup_args()
    assert '{{t|v}}' == str(t)
    # Triple duplicates:
    t = Template('{{t|1=v|v|1=v}}')
    t.rm_first_of_dup_args()
    assert '{{t|1=v}}' == str(t)


def test_has_arg():
    has_arg = Template('{{t|a|b=c}}').has_arg
    assert has_arg('1') is True
    assert has_arg('1', 'a') is True
    assert has_arg('b') is True
    assert has_arg('b', 'c') is True
    assert has_arg('2') is False
    assert has_arg('1', 'b') is False
    assert has_arg('c') is False
    assert has_arg('b', 'd') is False


def test_get_arg():
    get_arg = Template('{{t|a|b=c}}').get_arg
    assert '|a' == get_arg('1').string  # type: ignore
    assert get_arg('c') is None


def test_name_contains_a_param_with_default():
    t = Template('{{t {{{p1|d1}}} | {{{p2|d2}}} }}')
    assert 't {{{p1|d1}}} ' == t.name
    assert '| {{{p2|d2}}} ' == t.arguments[0].string
    t.name = 'g'
    assert 'g' == t.name


def test_overwriting_on_a_string_subspancontaining_string():
    t = Template('{{t {{{p1|d1}}} | {{{p2|d2}}} }}')
    t.name += 's'
    assert 't {{{p1|d1}}} s' == t.name


def test_overwriting_on_a_string_causes_loss_of_spans():
    t = Template('{{t {{{p1|d1}}} | {{{p2|d2}}} }}')
    p = t.parameters[0]
    t.name += 's'
    assert '' == p.string


def test_no_param_template_name():
    assert 'صعود' == Template('{{صعود}}').name


def test_lists():
    l1, l2 = Template('{{t|2=*a\n*b|*c\n*d}}').get_lists()
    assert l1.items == ['a', 'b']
    assert l2.items == ['c', 'd']
    assert Template('{{t|;https://a.b :d}}').get_lists('[;:]')[0].items == [
        'https://a.b ',
        'd',
    ]


# Template.set_arg


def test_set_arg():
    # Template with no args, keyword
    t = Template('{{t}}')
    t.set_arg('a', 'b')
    assert '{{t|a=b}}' == t.string
    # Template with no args, auto positional
    t = Template('{{t}}')
    t.set_arg('1', 'b')
    assert '{{t|1=b}}' == t.string
    # Arg already exist, positional
    t = Template('{{t|a}}')
    t.set_arg('1', 'b', preserve_spacing=False)
    assert '{{t|b}}' == t.string
    # Append new keyword when there is more than one arg
    t = Template('{{t|a}}')
    t.set_arg('z', 'z', preserve_spacing=True)
    assert '{{t|a|z=z}}' == t.string
    # Preserve spacing
    t = Template('{{t\n  | p1   = v1\n  | p22  = v2\n}}')
    t.set_arg('z', 'z', preserve_spacing=True)
    assert '{{t\n  | p1   = v1\n  | p22  = v2\n  | z    = z\n}}' == t.string
    t = Template('{{t|a|b|c}}')
    t.set_arg('3', 'z', positional=False)
    assert t.string == '{{t|a|b|3=z}}'


def test_set_arg_force_keyword():
    t = Template('{{t}}')
    t.set_arg('1', 'b', positional=False)
    assert '{{t|1=b}}' == t.string


@mark.parametrize('newline', ['\n', '\r', '\r\n'])
def test_preserve_spacing_with_only_one_arg(newline):
    t = Template(f'{{{{t{newline}  |  afadfaf =   value {newline}}}')
    t.set_arg('z', 'z', preserve_spacing=True)

    assert (
        '{{t'
        f'{newline}  |  afadfaf =   value'
        f'{newline}  |  z       =   z'
        f'{newline}}}' == t.string
    )


def test_multiline_arg():
    t = Template('{{text|\na=\nb\nc\n}}')
    t.set_arg('d', 'e', preserve_spacing=True)
    assert '{{text|\na=\nb\nc|\nd=\ne\n}}' == t.string
    t = Template('{{text\n\n | a = b\n\n}}')
    t.set_arg('c', 'd', preserve_spacing=True)
    assert '{{text\n\n | a = b\n\n | c = d\n\n}}' == t.string


def test_existing_dont_preserve_space():
    t = Template('{{t\n  |  a =   v \n}}')
    t.set_arg('a', 'w', preserve_spacing=False)
    assert '{{t\n  |a=w}}' == t.string

    t = Template('{{t\n  |  a =   v \n}}')
    t.set_arg('a', 'w', preserve_spacing=True)
    assert '{{t\n  |  a =   w \n}}' == t.string


def test_new_dont_preserve_space():
    t = Template('{{t\n  |  a =   v \n}}')
    t.set_arg('b', 'w', preserve_spacing=False)
    assert '{{t\n  |  a =   v \n|b=w}}' == t.string


def test_before():
    t = Template('{{t|a|b|c=c|d}}')
    t.set_arg('e', 'e', before='c')
    assert '{{t|a|b|e=e|c=c|d}}' == t.string


def test_after():
    t = Template('{{t|a|b|c=c|d}}')
    t.set_arg('e', 'e', after='c')
    assert '{{t|a|b|c=c|e=e|d}}' == t.string


def test_multi_set_positional_args():
    t = Template('{{t}}')
    t.set_arg('1', 'p', positional=True)
    t.set_arg('2', 'q', positional=True)
    assert '{{t|p|q}}' == t.string


def test_invalid_position():
    t = Template('{{t}}')
    with raises(ValueError) as err:
        t.set_arg('2', 'a', positional=True)
    assert err.value.args[0] == "cannot set arg '2' in positional form"

    t = Template('{{t}}')
    with raises(ValueError) as err:
        t.set_arg('v', 'a', positional=True)
    assert err.value.args[0] == "cannot set arg 'v' in positional form"
    assert '{{t}}' == t.string


def test_force_new_to_positional_when_old_is_keyword():
    t = Template('{{t|1=v}}')
    t.set_arg('1', 'v', positional=True)
    assert '{{t|v}}' == t.string


def test_nowiki_makes_equal_ineffective():
    a = Template('{{text|1<nowiki>=</nowiki>g}}').arguments[0]
    assert a.value == '1<nowiki>=</nowiki>g'
    assert a.name == '1'


def test_not_name_and_positional_is_none():
    t = Template('{{t}}')
    t.set_arg(None, 'v')
    assert '{{t|v}}' == t.string


def test_del_positional_arg():
    t = Template('{{t| a | b | 2 = c | d }}')
    t.del_arg('2')
    assert '{{t| a | d }}' == t.string


def test_parser_functions():
    assert (
        Template('{{t|{{#if:|}}}}').parser_functions[0].string == '{{#if:|}}'
    )


def test_setting_single_space_arg():  # 97
    t = Template('{{t|a= }}')
    t.set_arg('a', 'v', preserve_spacing=True)
    assert t.string == '{{t|a=v }}'


def test_preserve_spacing_left_and_right():
    t = Template('{{t|a=\tx }}')
    t.set_arg('a', 'y', preserve_spacing=True)
    assert t.string == '{{t|a=\ty }}'


def test_invalid_normal_name():  # 105
    assert '' == Template('{{template:}}').normal_name(capitalize=True)


def test_get_last_positional_index():
    t = Template('{{t|a|b|c=d}}')
    assert t.get_next_positional_index() == 2


def test_set_arg_can_convert_existing_positional_to_keyword():
    t = Template('{{t|  a  }}')
    t.set_arg('1', 'x', positional=False, preserve_spacing=True)
    assert '{{t|1=  x  }}' == t.string

    t = Template('{{t|  a  }}')
    t.set_arg('1', 'x', positional=False, preserve_spacing=False)
    assert '{{t|1=x}}' == t.string


def test_set_arg_can_convert_existing_keyword_to_positional():
    t = Template('{{t|  1  =  a  }}')
    t.set_arg('1', 'b', positional=True, preserve_spacing=True)
    assert '{{t|  b  }}' == t.string

    t = Template('{{t|  1  =  a  }}')
    t.set_arg('1', 'b', positional=True, preserve_spacing=False)
    assert '{{t|b}}' == t.string


def test_arguments_cache_is_invalidated_by_noop_replacement():
    t = Template('{{t|a=1|b=2}}')
    t.arguments  # populate the cache  # noqa: B018

    t[:] = t.string

    assert [arg.string for arg in t.arguments] == ['|a=1', '|b=2']


def test_has_arg_positional_value_whitespace_is_significant():
    t = Template('{{t| v }}')
    assert t.has_arg('1', ' v ')
    assert not t.has_arg('1', 'v')


def test_set_arg_with_none_name():
    t = Template('{{t|a}}')
    t.set_arg(None, 'x')
    assert t.string == '{{t|a|x}}'
    t = Template('{{t|a}}')
    t.set_arg(None, 'x', positional=True)
    assert t.string == '{{t|a|x}}'


def test_set_arg_preserve_spacing_tie_uses_first_occurrence():
    # Leading WS of the two existing args is a tie: '\t' (a) vs '  ' (b).
    # Arguments are traversed in reverse, so '  ' (the last arg) is seen
    # first and must win the tie.
    t = Template('{{t|\ta=v|  b=w}}')
    t.set_arg('c', 'X', preserve_spacing=True)
    assert t.string == '{{t|\ta=v|  b=w|  c=X}}'


def test_set_arg_preserve_spacing_empty_template_does_not_crash():
    t = Template('{{t}}')
    t.set_arg('1', 'x', preserve_spacing=True)
    assert t.string == '{{t|1=x}}'


def test_set_arg_preserve_spacing_empty_named():
    t = Template('{{t}}')
    t.set_arg('n', 'x', preserve_spacing=True)
    assert t.string == '{{t|n=x}}'


def test_set_arg_positional_true_rejects_non_canonical_indices():
    # to_index only accepts canonical decimal strings; everything else is
    # not a valid positional index, so positional=True must raise.
    # only exception is ' 1 ' which is allowed for spacing purposes.
    for name in ('01', '+1', '\uff11', '1_0', '0', '-1'):
        t = Template('{{t}}')
        with raises(ValueError):
            t.set_arg(name, 'X', positional=True)
        assert t.string == '{{t}}', name


def test_set_arg_positional_true_accepts_canonical_index():
    t = Template('{{t}}')
    t.set_arg('1', 'X', positional=True)
    assert t.string == '{{t|X}}'


def test_set_arg_positional_true_whitespace_padded_name():
    # MediaWiki strips whitespace around named-argument names, so ' 1 '
    # and '1' refer to the same argument. When the arg already exists,
    # set_arg updates it in place instead of raising, even though the
    # padded form is not a canonical positional index on its own.
    t = Template('{{t|a}}')
    t.set_arg(' 1 ', 'X', positional=True)
    a = t.get_arg(' 1 ')
    assert a is not None and a.value == 'X'


def test_set_arg_positional_true_whitespace_padded_name_empty_template():
    # On an empty template there is no existing arg to update, so the
    # padded name is not a valid positional index and positional=True
    # raises -- unlike the existing-arg case above.
    t = Template('{{t}}')
    assert t.get_arg(' 1 ') is None
    t.set_arg(' 1 ', 'X', positional=True)
    assert t.string == '{{t|X}}'
