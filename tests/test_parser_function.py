from pytest import main, mark

from wikitextparser import ParserFunction, WikiText
# noinspection PyProtectedMember
from wikitextparser._wikitext import WS


def test_parser_function():
    assert repr(ParserFunction('{{#if:a|{{#if:b|c}}}}').parser_functions[0]) \
        == "ParserFunction('{{#if:b|c}}')"


def test_args_containing_braces():
    assert 4 == len(ParserFunction('{{#pf:\n{|2\n|3\n|}\n}}').arguments)


def test_repr():
    assert repr(ParserFunction('{{#if:a|b}}')) ==\
            "ParserFunction('{{#if:a|b}}')"


def test_name_and_args():
    f = ParserFunction('{{ #if: test | true | false }}')
    assert ' #if' == f.name
    assert [': test ', '| true ', '| false '] ==\
           [a.string for a in f.arguments]


def test_set_name():
    pf = ParserFunction('{{   #if: test | true | false }}')
    pf.name = pf.name.strip(WS)
    assert '{{#if: test | true | false }}' == pf.string


def test_pipes_inside_params_or_templates():
    pf = ParserFunction('{{ #if: test | {{ text | aaa }} }}')
    assert [] == pf.parameters
    assert 2 == len(pf.arguments)
    pf = ParserFunction('{{ #if: test | {{{ text | aaa }}} }}')
    assert 1 == len(pf.parameters)
    assert 2 == len(pf.arguments)


def test_default_parser_function_without_hash_sign():
    assert 1 == len(WikiText("{{formatnum:text|R}}").parser_functions)


@mark.xfail
def test_parser_function_alias_without_hash_sign():
    """‍`آرایش‌عدد` is an alias for `formatnum` on Persian Wikipedia.

    See: //translatewiki.net/wiki/MediaWiki:Sp-translate-data-MagicWords/fa
    """
    assert 1 == len(WikiText("{{آرایش‌عدد:text|R}}").parser_functions)


def test_argument_with_existing_span():
    """Test when the span is already in type_to_spans."""
    pf = WikiText("{{formatnum:text}}").parser_functions[0]
    assert pf.arguments[0].value == 'text'
    assert pf.arguments[0].value == 'text'


def test_tag_containing_pipe():
    assert len(ParserFunction("{{text|a<s |>b</s>c}}").arguments) == 1


if __name__ == '__main__':
    main()
