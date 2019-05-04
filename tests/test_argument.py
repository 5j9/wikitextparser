"""Test the Argument class."""


from unittest import main, TestCase

from wikitextparser import Argument, Template, parse


class TestArgument(TestCase):

    """Argument test class."""

    def test_basic(self):
        a = Argument('| a = b ')
        ae = self.assertEqual
        ae(' a ', a.name)
        ae(' b ', a.value)
        ae(False, a.positional)
        ae(repr(a), "Argument('| a = b ')")

    def test_anonymous_parameter(self):
        ae = self.assertEqual
        a = Argument('| a ')
        ae('1', a.name)
        ae(' a ', a.value)

    def test_set_name(self):
        a = Argument('| a = b ')
        a.name = ' c '
        self.assertEqual('| c = b ', a.string)

    def test_set_name_at_subspan_boundary(self):
        ae = self.assertEqual
        a = Argument('|{{ a }}={{ b }}')
        a.name = ' c '
        ae('| c ={{ b }}', a.string)
        ae('{{ b }}', a.value)

    def test_set_name_for_positional_args(self):
        a = Argument('| b ')
        a.name = a.name
        self.assertEqual('|1= b ', a.string)

    def test_value_setter(self):
        a = Argument('| a = b ')
        a.value = ' c '
        self.assertEqual('| a = c ', a.string)

    def test_removing_last_arg_should_not_effect_the_others(self):
        ae = self.assertEqual
        a, b, c = Template('{{t|1=v|v|1=v}}').arguments
        del c[:]
        ae('|1=v', a.string)
        ae('|v', b.string)

    def test_nowikied_arg(self):
        ae = self.assertEqual
        a = Argument('|<nowiki>1=3</nowiki>')
        ae(True, a.positional)
        ae('1', a.name)
        ae('<nowiki>1=3</nowiki>', a.value)

    def test_value_after_convertion_of_positional_to_keywordk(self):
        a = Argument("""|{{{a|{{{b}}}}}}""")
        a.name = ' 1 '
        self.assertEqual('{{{a|{{{b}}}}}}', a.value)

    def test_name_of_positionals(self):
        self.assertEqual(
            ['1', '2', '3'],
            [a.name for a in parse('{{t|a|b|c}}').templates[0].arguments])

    def test_dont_confuse_subspan_equal_with_keyword_arg_equal(self):
        ae = self.assertEqual
        p = parse('{{text| {{text|1=first}} | b }}')
        a0, a1 = p.templates[0].arguments
        ae(' {{text|1=first}} ', a0.value)
        ae('1', a0.name)
        ae(' b ', a1.value)
        ae('2', a1.name)

    def test_setting_positionality(self):
        ae = self.assertEqual
        a = Argument("|1=v")
        a.positional = False
        ae('|1=v', a.string)
        a.positional = True
        ae('|v', a.string)
        a.positional = True
        ae('|v', a.string)
        self.assertRaises(ValueError, setattr, a, 'positional', False)

    def test_parser_functions_at_the_end(self):
        pfs = Argument('| 1 ={{#ifeq:||yes}}').parser_functions
        self.assertEqual(1, len(pfs))

    def test_section_not_keyword_arg(self):
        ae = self.assertEqual
        a = Argument('|1=foo\n== section ==\nbar')
        ae((a.name, a.value), ('1', 'foo\n== section ==\nbar'))
        a = Argument('|\n==t==\nx')
        ae((a.name, a.value), ('1', '\n==t==\nx'))
        # Following cases is not treated as a section headings
        a = Argument('|==1==\n')
        ae((a.name, a.value), ('', '=1==\n'))
        # Todo: Prevents forming a template!
        # a = Argument('|\n==1==')
        # ae(
        #     (a.name, a.value), ('1', '\n==1=='))

    def test_argument_name_not_external_link(self):
        ae = self.assertEqual
        # MediaWiki parses template parameters before external links,
        # so it goes with the named parameter in both cases.
        a = Argument('|[http://example.com?foo=bar]')
        ae((a.name, a.value), ('[http://example.com?foo', 'bar]'))
        a = Argument('|http://example.com?foo=bar')
        ae((a.name, a.value), ('http://example.com?foo', 'bar'))

    def test_lists(self):
        ae = self.assertEqual
        ae(Argument('|list=*a\n*b').lists()[0].items, ['a', 'b'])
        ae(Argument('|lst= *a\n*b').lists()[0].items, ['a', 'b'])
        ae(Argument('|*a\n*b').lists()[0].items, ['a', 'b'])
        # the space at the beginning of a positional argument should not be
        # ignored. (?)
        ae(Argument('| *a\n*b').lists()[0].items, ['b'])


if __name__ == '__main__':
    main()
