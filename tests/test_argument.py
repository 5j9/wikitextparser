"""Test the Argument class."""


from unittest import main, TestCase

from wikitextparser import Argument, Template, parse


class TestArgument(TestCase):

    """Argument test class."""

    def test_basic(self):
        a = Argument('| a = b ')
        self.assertEqual(' a ', a.name)
        self.assertEqual(' b ', a.value)
        self.assertEqual(False, a.positional)
        self.assertEqual(repr(a), "Argument('| a = b ')")

    def test_anonymous_parameter(self):
        a = Argument('| a ')
        self.assertEqual('1', a.name)
        self.assertEqual(' a ', a.value)

    def test_set_name(self):
        a = Argument('| a = b ')
        a.name = ' c '
        self.assertEqual('| c = b ', a.string)

    def test_set_name_at_subspan_boundary(self):
        a = Argument('|{{ a }}={{ b }}')
        a.name = ' c '
        self.assertEqual('| c ={{ b }}', a.string)
        self.assertEqual('{{ b }}', a.value)

    def test_set_name_for_positional_args(self):
        a = Argument('| b ')
        a.name = a.name
        self.assertEqual('|1= b ', a.string)

    def test_set_value(self):
        a = Argument('| a = b ')
        a.value = ' c '
        self.assertEqual('| a = c ', a.string)

    def test_removing_last_arg_should_not_effect_the_others(self):
        a, b, c = Template('{{t|1=v|v|1=v}}').arguments
        del c[:]
        self.assertEqual('|1=v', a.string)
        self.assertEqual('|v', b.string)

    def test_nowikied_arg(self):
        a = Argument('|<nowiki>1=3</nowiki>')
        self.assertEqual(True, a.positional)
        self.assertEqual('1', a.name)
        self.assertEqual('<nowiki>1=3</nowiki>', a.value)

    def test_value_after_convertion_of_positional_to_keywordk(self):
        a = Argument("""|{{{a|{{{b}}}}}}""")
        a.name = ' 1 '
        self.assertEqual('{{{a|{{{b}}}}}}', a.value)

    def test_name_of_positionals(self):
        self.assertEqual(
            ['1', '2', '3'],
            [a.name for a in parse('{{t|a|b|c}}').templates[0].arguments])

    def test_dont_confuse_subspan_equal_with_keyword_arg_equal(self):
        p = parse('{{text| {{text|1=first}} | b }}')
        a0, a1 = p.templates[0].arguments
        self.assertEqual(' {{text|1=first}} ', a0.value)
        self.assertEqual('1', a0.name)
        self.assertEqual(' b ', a1.value)
        self.assertEqual('2', a1.name)

    def test_setting_positionality(self):
        a = Argument("|1=v")
        a.positional = False
        self.assertEqual('|1=v', a.string)
        a.positional = True
        self.assertEqual('|v', a.string)
        a.positional = True
        self.assertEqual('|v', a.string)
        self.assertRaises(ValueError, setattr, a, 'positional', False)

    def test_parser_functions_at_the_end(self):
        pfs = Argument('| 1 ={{#ifeq:||yes}}').parser_functions
        self.assertEqual(1, len(pfs))

    def test_section_not_keyword_arg(self):
        a = Argument('|1=foo\n== section ==\nbar')
        self.assertEqual(
            (a.name, a.value), ('1', 'foo\n== section ==\nbar'))
        a = Argument('|\n==t==\nx')
        self.assertEqual(
            (a.name, a.value), ('1', '\n==t==\nx'))
        # Following cases is not treated as a section headings
        a = Argument('|==1==\n')
        self.assertEqual(
            (a.name, a.value), ('', '=1==\n'))
        # Todo: Prevents forming a template!
        # a = Argument('|\n==1==')
        # self.assertEqual(
        #     (a.name, a.value), ('1', '\n==1=='))

    def test_argument_name_not_external_link(self):
        # MediaWiki parses template parameters before external links,
        # so it goes with the named parameter in both cases.
        a = Argument('|[http://example.com?foo=bar]')
        self.assertEqual(
            (a.name, a.value), ('[http://example.com?foo', 'bar]'))
        a = Argument('|http://example.com?foo=bar')
        self.assertEqual(
            (a.name, a.value), ('http://example.com?foo', 'bar'))

    def test_lists(self):
        self.assertEqual(Argument('|list=*a\n*b').lists()[0].items, ['a', 'b'])
        self.assertEqual(Argument('|lst= *a\n*b').lists()[0].items, ['a', 'b'])
        self.assertEqual(Argument('|*a\n*b').lists()[0].items, ['a', 'b'])
        # the space at the beginning of a positional argument should not be
        # ignored. (?)
        self.assertEqual(Argument('| *a\n*b').lists()[0].items, ['b'])


if __name__ == '__main__':
    main()
