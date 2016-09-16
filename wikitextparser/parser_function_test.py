"""Test the ExternalLink class."""


import unittest

import wikitextparser as wtp


class ParserFunction(unittest.TestCase):

    """Test the ParserFunction class."""

    def test_name_and_args(self):
        pf = wtp.ParserFunction('{{ #if: test | true | false }}')
        self.assertEqual(' #if', pf.name)
        self.assertEqual(
            [': test ', '| true ', '| false '],
            [a.string for a in pf.arguments]
        )

    def test_set_name(self):
        pf = wtp.ParserFunction('{{   #if: test | true | false }}')
        pf.name = pf.name.strip()
        self.assertEqual('{{#if: test | true | false }}', pf.string)

    def test_pipes_inside_params_or_templates(self):
        pf = wtp.ParserFunction('{{ #if: test | {{ text | aaa }} }}')
        self.assertEqual([], pf.parameters)
        self.assertEqual(2, len(pf.arguments))
        pf = wtp.ParserFunction('{{ #if: test | {{{ text | aaa }}} }}')
        self.assertEqual(1, len(pf.parameters))
        self.assertEqual(2, len(pf.arguments))

    def test_default_parser_function_without_hash_sign(self):
        wt = wtp.WikiText("{{formatnum:text|R}}")
        self.assertEqual(1, len(wt.parser_functions))

    @unittest.expectedFailure
    def test_parser_function_alias_without_hash_sign(self):
        """‍`آرایش‌عدد` is an alias for `formatnum` on Persian Wikipedia.

        See: //translatewiki.net/wiki/MediaWiki:Sp-translate-data-MagicWords/fa

        """
        wt = wtp.WikiText("""{{آرایش‌عدد:text|R}}""")
        self.assertEqual(1, len(wt.parser_functions))


if __name__ == '__main__':
    unittest.main()
