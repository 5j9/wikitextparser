"""Test the ExternalLink class."""


from unittest import TestCase, main, expectedFailure

from wikitextparser import ParserFunction, WikiText
# noinspection PyProtectedMember
from wikitextparser._wikitext import WS


class TestParserFunction(TestCase):

    """Test the ParserFunction class."""

    def test_parser_function(self):
        self.assertEqual(
            repr(ParserFunction('{{#if:a|{{#if:b|c}}}}').parser_functions[0]),
            "ParserFunction('{{#if:b|c}}')")

    def test_args_containing_braces(self):
        self.assertEqual(
            4, len(ParserFunction('{{#pf:\n{|2\n|3\n|}\n}}').arguments))

    def test_repr(self):
        self.assertEqual(
            repr(ParserFunction('{{#if:a|b}}')),
            "ParserFunction('{{#if:a|b}}')")

    def test_name_and_args(self):
        ae = self.assertEqual
        f = ParserFunction('{{ #if: test | true | false }}')
        ae(' #if', f.name)
        ae([': test ', '| true ', '| false '], [a.string for a in f.arguments])

    def test_set_name(self):
        pf = ParserFunction('{{   #if: test | true | false }}')
        pf.name = pf.name.strip(WS)
        self.assertEqual('{{#if: test | true | false }}', pf.string)

    def test_pipes_inside_params_or_templates(self):
        ae = self.assertEqual
        pf = ParserFunction('{{ #if: test | {{ text | aaa }} }}')
        ae([], pf.parameters)
        ae(2, len(pf.arguments))
        pf = ParserFunction('{{ #if: test | {{{ text | aaa }}} }}')
        ae(1, len(pf.parameters))
        ae(2, len(pf.arguments))

    def test_default_parser_function_without_hash_sign(self):
        self.assertEqual(
            1, len(WikiText("{{formatnum:text|R}}").parser_functions))

    @expectedFailure
    def test_parser_function_alias_without_hash_sign(self):
        """‍`آرایش‌عدد` is an alias for `formatnum` on Persian Wikipedia.

        See: //translatewiki.net/wiki/MediaWiki:Sp-translate-data-MagicWords/fa
        """
        self.assertEqual(
            1, len(WikiText("{{آرایش‌عدد:text|R}}").parser_functions))

    def test_argument_with_existing_span(self):
        """Test when the span is already in type_to_spans."""
        ae = self.assertEqual
        pf = WikiText("{{formatnum:text}}").parser_functions[0]
        ae(pf.arguments[0].value, 'text')
        ae(pf.arguments[0].value, 'text')

    def test_tag_containing_pipe(self):
        self.assertEqual(len(
            ParserFunction("{{text|a<s |>b</s>c}}").arguments), 1)


if __name__ == '__main__':
    main()
