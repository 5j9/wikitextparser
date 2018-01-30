"""Test the ExternalLink class."""


import unittest

from wikitextparser import ParserFunction, WikiText
# noinspection PyProtectedMember
from wikitextparser._wikitext import WS


class TestParserFunction(unittest.TestCase):

    """Test the ParserFunction class."""

    def test_repr(self):
        pf = ParserFunction('{{#if:a|b}}')
        self.assertEqual(repr(pf), "ParserFunction('{{#if:a|b}}')")

    def test_name_and_args(self):
        pf = ParserFunction('{{ #if: test | true | false }}')
        self.assertEqual(' #if', pf.name)
        self.assertEqual(
            [': test ', '| true ', '| false '],
            [a.string for a in pf.arguments]
        )

    def test_set_name(self):
        pf = ParserFunction('{{   #if: test | true | false }}')
        pf.name = pf.name.strip(WS)
        self.assertEqual('{{#if: test | true | false }}', pf.string)

    def test_pipes_inside_params_or_templates(self):
        pf = ParserFunction('{{ #if: test | {{ text | aaa }} }}')
        self.assertEqual([], pf.parameters)
        self.assertEqual(2, len(pf.arguments))
        pf = ParserFunction('{{ #if: test | {{{ text | aaa }}} }}')
        self.assertEqual(1, len(pf.parameters))
        self.assertEqual(2, len(pf.arguments))

    def test_default_parser_function_without_hash_sign(self):
        wt = WikiText("{{formatnum:text|R}}")
        self.assertEqual(1, len(wt.parser_functions))

    @unittest.expectedFailure
    def test_parser_function_alias_without_hash_sign(self):
        """‍`آرایش‌عدد` is an alias for `formatnum` on Persian Wikipedia.

        See: //translatewiki.net/wiki/MediaWiki:Sp-translate-data-MagicWords/fa

        """
        self.assertEqual(
            1, len(WikiText("{{آرایش‌عدد:text|R}}").parser_functions)
        )

    def test_argument_with_existing_span(self):
        """Test when the span is already in type_to_spans."""
        pf = WikiText("{{formatnum:text}}").parser_functions[0]
        self.assertEqual(pf.arguments[0].value, 'text')
        self.assertEqual(pf.arguments[0].value, 'text')


if __name__ == '__main__':
    unittest.main()
