from pytest import mark, param, raises

from wikitextparser import Argument, ParserFunction, Template, parse


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
    with raises(ValueError):
        a.positional = False


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


def test_tag_with_equal_sign():
    assert Argument('|a<ref name="abc">R</ref>').name == '1'


def test_section_heading_with_carriage_return_in_name():
    assert Argument('|a\r== heading ==\rb=c').name == 'a\r== heading ==\rb'


def test_set_arg_can_convert_existing_positional_to_keyword():
    t = Template('{{t|a}}')
    t.set_arg('1', 'x', positional=False)
    assert '{{t|1=x}}' == t.string


def test_set_arg_can_convert_existing_keyword_to_positional():
    t = Template('{{t|1=a}}')
    t.set_arg('1', 'b', positional=True)
    assert '{{t|b}}' == t.string


def test_set_arg_before_nonexistent_raises():
    t = Template('{{t|a|b|c}}')
    with raises(ValueError, match="no argument named 'nope'"):
        t.set_arg('x', 'v', before='nope')


def test_set_arg_after_nonexistent_raises():
    t = Template('{{t|a|b|c}}')
    with raises(ValueError, match="no argument named 'nope'"):
        t.set_arg('x', 'v', after='nope')


def test_mode_tie_breaks_by_first_occurrence():
    from wikitextparser._argument import mode

    # All counts equal -> first occurrence wins, deterministically.
    assert mode(['a', 'b', 'c']) == 'a'
    assert mode(['b', 'a', 'c']) == 'b'
    assert mode(['c', 'b', 'a']) == 'c'

    # A clear winner still wins regardless of position.
    assert mode(['a', 'b', 'b']) == 'b'
    assert mode(['b', 'b', 'a']) == 'b'

    # Ties among the most common -> first of the tied maxima.
    assert mode(['a', 'a', 'b', 'b', 'c']) == 'a'
    assert mode(['b', 'b', 'a', 'a', 'c']) == 'b'


def test_set_arg_ignore_equals_strips_whitespace_padded_index():
    # Under ignore_equals=True, set_arg treats surrounding whitespace as
    # formatting and interprets ' 1 ' as index 1. The created positional
    # is addressable by its canonical index '1'.
    f = ParserFunction('{{#f}}')
    f.set_arg(' 1 ', 'X', ignore_equals=True, positional=True)
    assert f.string == '{{#f:X}}'
    a = f.get_arg('1', ignore_equals=True)
    assert a is not None and a.string == ':X'
    # Canonical lookups remain strict: ' 1 ' is not a canonical index.
    a = f.get_arg(' 1 ', ignore_equals=True)
    assert a is not None and a.string == ':X'


@mark.parametrize(
    'src, name, value, kwargs, expected',
    [
        # --- Template, positional=None, name IS the next positional index ---
        # 1. all existing args positional -> mode=positional -> new arg positional
        param(
            '{{t|a|b}}',
            '3',
            'c',
            {},
            '{{t|a|b|c}}',
            id='all-positional-next-name',
        ),
        # 2. all existing args keyword -> mode=keyword -> new arg keyword
        param(
            '{{t|1=a|2=b}}',
            '3',
            'c',
            {},
            '{{t|1=a|2=b|3=c}}',
            id='all-keyword-next-name',
        ),
        # 3. tie (1 pos, 1 kw) -> last-arg kind wins (kw) -> new arg keyword
        param(
            '{{t|a|1=b}}',
            '2',
            'c',
            {},
            '{{t|a|1=b|2=c}}',
            id='tie-last-arg-keyword',
        ),
        # 4. majority positional (2 pos, 1 kw) -> new arg positional
        param(
            '{{t|a|b|1=c}}',
            '3',
            'd',
            {},
            '{{t|a|b|1=c|3=d}}',
            id='trailing-keyword-wins',
        ),
        param(
            '{{t|1=a|2=b|c}}',
            '3',
            'd',
            {},
            '{{t|1=a|2=b|c|3=d}}',
            id='non-next-name-after-keywords-falls-back-to-keyword',
        ),
        param(
            '{{t|1=a|2=b|c}}',
            '2',
            'd',
            {},
            '{{t|1=a|2=d|c}}',
            id='existing-keyword-name-updates-in-place',
        ),
        param(
            '{{t|1=a|b|c}}',
            '3',
            'd',
            {},
            '{{t|1=a|b|c|d}}',
            id='last-arg-positional-wins',
        ),
        # --- Template, positional=None, name is NOT the next positional index ---
        # 5. name doesn't match -> fall back to keyword regardless of mode
        param(
            '{{t|a|b}}',
            '5',
            'c',
            {},
            '{{t|a|b|5=c}}',
            id='non-next-name-falls-back-to-keyword',
        ),
        # --- Collision: name resolves to an EXISTING arg -> update, no mode ---
        # 6. keyword '2=c' already exists; new positional would also be named 2.
        #    Existing-arg branch wins: overwrite the keyword.
        param(
            '{{t|a|1=b|2=c}}',
            '2',
            'd',
            {},
            '{{t|a|1=b|2=d}}',
            id='existing-name-updates-in-place',
        ),
        # --- Explicit positional=True must win (and raise if impossible) ---
        # 7. name IS next index -> positional
        param(
            '{{t|a|b}}',
            '3',
            'c',
            {'positional': True},
            '{{t|a|b|c}}',
            id='explicit-positional-next-name',
        ),
        # 8. name is NOT next index -> raise
        param(
            '{{t|a|b}}',
            '5',
            'c',
            {'positional': True},
            ValueError,
            id='explicit-positional-non-next-name-raises',
        ),
        # --- Explicit positional=False must win ---
        # 9. even though name IS next index and mode would say positional
        param(
            '{{t|a|b}}',
            '3',
            'c',
            {'positional': False},
            '{{t|a|b|3=c}}',
            id='explicit-keyword-wins',
        ),
        # --- ParserFunction, ignore_equals=True ---
        # 10. name == next slot -> mode is degenerate (all positional) -> positional
        param(
            '{{#f:a|b}}',
            '3',
            'c',
            {'ignore_equals': True},
            '{{#f:a|b|c}}',
            id='pf-ie-matching-name-positional',
        ),
        # 11. name != next slot -> keyword (fall back)
        param(
            '{{#f:a|b}}',
            '4',
            'c',
            {'ignore_equals': True},
            '{{#f:a|b|4=c}}',
            id='pf-ie-non-matching-name-keyword',
        ),
        param(
            '{{#f:a|b=c}}',
            '3',
            'd',
            {'ignore_equals': True},
            '{{#f:a|b=c|d}}',
            id='pf-ie-eq-arg-matching-name-positional',
        ),
    ],
)
def test_set_arg_positional_none_mode(src, name, value, kwargs, expected):
    cls = ParserFunction if '#f' in src else Template
    t = cls(src)
    if expected is ValueError:
        with raises(ValueError):
            t.set_arg(name, value, **kwargs)
        return
    t.set_arg(name, value, **kwargs)
    assert t.string == expected


def test_set_arg_ie_true_preserve_spacing_matching_name_ignores_spacing():
    # Under ignore_equals=True and positional=None, a name that denotes the
    # next slot yields a positional argument, so preserve_spacing is ignored
    # (see the _set_arg docstring: "Ignore preserve_spacing if positional is
    # True"). Pinned so a future change that starts honoring spacing here is
    # noticed.
    f = ParserFunction('{{#pf: a | b }}')
    f.set_arg('3', 'c', preserve_spacing=True, ignore_equals=True)
    assert f.string == '{{#pf: a | b |c}}'
