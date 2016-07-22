"""Run all tests *_test.py modules plus the test for wikitextparser."""


import sys
import unittest

sys.path.insert(0, '..')
from wikitextparser import wikitextparser as wtp


class WikiText(unittest.TestCase):

    """Test the WikiText class."""

    def test_bare_link(self):
        s = 'text1 HTTP://mediawiki.org text2'
        wt = wtp.WikiText(s)
        self.assertEqual(
            'HTTP://mediawiki.org',
            str(wt.external_links[0]),
        )

    def test_with_lable(self):
        s = 'text1 [http://mediawiki.org MediaWiki] text2'
        wt = wtp.WikiText(s)
        self.assertEqual(
            'http://mediawiki.org',
            wt.external_links[0].url
        )
        self.assertEqual(
            'MediaWiki',
            wt.external_links[0].text
        )

    def test_numbered_link(self):
        s = 'text1 [http://mediawiki.org] text2'
        wt = wtp.WikiText(s)
        self.assertEqual(
            '[http://mediawiki.org]',
            str(wt.external_links[0]),
        )

    def test_protocol_relative(self):
        s = 'text1 [//en.wikipedia.org wikipedia] text2'
        wt = wtp.WikiText(s)
        self.assertEqual(
            '[//en.wikipedia.org wikipedia]',
            str(wt.external_links[0]),
        )

    def test_destroy(self):
        s = 'text1 [//en.wikipedia.org wikipedia] text2'
        wt = wtp.WikiText(s)
        wt.external_links[0].string = ''
        self.assertEqual(
            'text1  text2',
            str(wt),
        )

    def test_wikilink_inside_parser_function(self):
        wt = wtp.WikiText("{{ #if: {{{3|}}} | [[u:{{{3}}}|{{{3}}}]] }}")
        self.assertEqual("[[u:{{{3}}}|{{{3}}}]]", wt.wikilinks[0].string)

    def test_template_inside_wikilink(self):
        wt = wtp.WikiText("{{text |  [[ A | {{text|b}} ]] }}")
        self.assertEqual(2, len(wt.templates))

    def test_wikilink_in_template(self):
        s1 = "{{text |[[A|}}]]}}"
        wt = wtp.WikiText(s1)
        self.assertEqual(s1, str(wt.templates[0]))

    def test_wikilink_containing_closing_braces_in_template(self):
        s = '{{text|[[  A   |\n|}}[]<>]]\n}}'
        wt = wtp.WikiText(s)
        self.assertEqual(s, str(wt.templates[0]))

    def test_ignore_comments(self):
        s1 = "{{text |<!-- }} -->}}"
        wt = wtp.WikiText(s1)
        self.assertEqual(s1, str(wt.templates[0]))

    def test_ignore_nowiki(self):
        wt = wtp.WikiText("{{text |<nowiki>}} A </nowiki> }} B")
        self.assertEqual(
            "{{text |<nowiki>}} A </nowiki> }}",
            str(wt.templates[0])
        )

    def test_getting_comment(self):
        wt = wtp.WikiText('text1 <!--\n\ncomment\n{{A}}\n-->text2')
        self.assertEqual(
            "\n\ncomment\n{{A}}\n",
            wt.comments[0].contents
        )

    def test_template_in_wikilink(self):
        s = '[[A|{{text|text}}]]'
        wt = wtp.WikiText(s)
        self.assertEqual(s, str(wt.wikilinks[0]))

    def test_wikilink_target_may_contain_newline(self):
        s = '[[A | faf a\n\nfads]]'
        wt = wtp.WikiText(s)
        self.assertEqual(s, str(wt.wikilinks[0]))

    def test_template_inside_extension_tags(self):
        s = "<includeonly>{{t}}</includeonly>"
        wt = wtp.WikiText(s)
        self.assertEqual('{{t}}', str(wt.templates[0]))

    def test_dont_parse_source_tag(self):
        s = "<source>{{t}}</source>"
        wt = wtp.WikiText(s)
        self.assertEqual(0, len(wt.templates))

    def test_comment_in_parserfanction_name(self):
        s = "{{<!--c\n}}-->#if:|a}}"
        wt = wtp.WikiText(s)
        self.assertEqual(1, len(wt.parser_functions))

    def test_wikilink2externallink_fallback(self):
        p = wtp.parse('[[http://example.com foo bar]]')
        self.assertEqual(
            '[http://example.com foo bar]',
            p.external_links[0].string
        )
        self.assertEqual(0, len(p.wikilinks))

    @unittest.expectedFailure
    def test_no_bare_externallink_within_wikilinks(self):
        """Based on how Mediawiki behaves.

        There is a rather simple solution for this (move the detection of
        external links to spans.py) but maybe the current implementation
        is even more useful? Also it should be faster.
        """
        p = wtp.parse('[[ https://en.wikipedia.org/]]')
        self.assertEqual(1, len(p.wikilinks))
        self.assertEqual(0, len(p.external_links))


class Tables(unittest.TestCase):

    """Test the tables property."""

    def test_table_extraction(self):
        s = '{|class=wikitable\n|a \n|}'
        p = wtp.parse(s)
        self.assertEqual(s, p.tables[0].string)

    def test_table_start_after_space(self):
        s = '   {|class=wikitable\n|a \n|}'
        p = wtp.parse(s)
        self.assertEqual(s.strip(), p.tables[0].string)

    def test_ignore_comments_before_extracting_tables(self):
        s = '{|class=wikitable\n|a \n<!-- \n|} \n-->\n|b\n|}'
        p = wtp.parse(s)
        self.assertEqual(s, p.tables[0].string)

    def test_two_tables(self):
        s = 'text1\n {|\n|a \n|}\ntext2\n{|\n|b\n|}\ntext3\n'
        p = wtp.parse(s)
        self.assertEqual(2, len(p.tables))
        self.assertEqual('{|\n|a \n|}', p.tables[0].string)
        self.assertEqual('{|\n|b\n|}', p.tables[1].string)

    def test_nested_tables(self):
        s = (
            'text1\n{|class=wikitable\n|a\n|\n'
            '{|class=wikitable\n|b\n|}\n|}\ntext2'
        )
        p = wtp.parse(s)
        self.assertEqual(2, len(p.tables))
        self.assertEqual(s[6:-6], p.tables[1].string)
        self.assertEqual('{|class=wikitable\n|b\n|}', p.tables[0].string)

    def test_tables_in_different_sections(self):
        s = '{|\n| a\n|}\n\n= s =\n{|\n| b\n|}\n'
        p = wtp.parse(s).sections[1]
        self.assertEqual('{|\n| b\n|}', p.tables[0].string)


class PrettyPrint(unittest.TestCase):

    """Test the pprint method of the WikiText class."""

    def test_template_with_multi_args(self):
        s = "{{a|b=b|c=c|d=d|e=e}}"
        wt = wtp.WikiText(s)
        self.assertEqual(
            '{{a\n    | b = b\n    | c = c\n    | d = d\n    | e = e\n}}',
            wt.pprint(),
        )

    def test_double_space_indent(self):
        s = "{{a|b=b|c=c|d=d|e=e}}"
        wt = wtp.WikiText(s)
        self.assertEqual(
            '{{a\n  | b = b\n  | c = c\n  | d = d\n  | e = e\n}}',
            wt.pprint('  '),
        )

    def test_remove_comments(self):
        s = "{{a|<!--b=b|c=c|d=d|-->e=e}}"
        wt = wtp.WikiText(s)
        self.assertEqual(
            '{{a\n  | e = e\n}}',
            wt.pprint('  ', remove_comments=True),
        )

    def test_first_arg_of_tag_is_whitespace_sensitive(self):
        """The second argument of #tag is an exception.

        See the last warning on [[mw:Help:Magic_words#Miscellaneous]]:
        You must write {{#tag:tagname||attribute1=value1|attribute2=value2}}
        to pass an empty content. No space is permitted in the area reserved
        for content between the pipe characters || before attribute1.
        """
        s = '{{#tag:ref||name="n1"}}'
        wt = wtp.WikiText(s)
        self.assertEqual(s, wt.pprint())
        s = '{{#tag:foo| }}'
        wt = wtp.WikiText(s)
        self.assertEqual(s, wt.pprint())

    def test_invoke(self):
        """#invoke args are also whitespace-sensitive."""
        s = '{{#invoke:module|func|arg}}'
        wt = wtp.WikiText(s)
        self.assertEqual(s, wt.pprint())

    def test_on_parserfunction(self):
        s = "{{#switch:case|abcde = f| g=h}}"
        wt = wtp.parse(s)
        self.assertEqual(
            '{{#switch: case\n    | abcde = f\n    | g=h\n}}',
            wt.pprint(),
        )

    def test_parserfunction_with_no_pos_arg(self):
        s = "{{#switch:case|a|b}}"
        wt = wtp.parse(s)
        self.assertEqual(
            '{{#switch: case\n    | a\n    | b\n}}',
            wt.pprint(),
        )

    def test_convert_positional_to_keyword_if_possible(self):
        self.assertEqual(
            '{{t\n    | 1 = a\n    | 2 = b\n    | 3 = c\n}}',
            wtp.parse('{{t|a|b|c}}').pprint(),
        )

    def test_if_first_arg_is_coverted_then_all_should_be(self):
        """Otherwise the second positional arg will also be passed as 1.

        The result of not doing this will be duplicate arguments.
        """
        self.assertEqual(
            '{{t\n'
            '    | 1 = a\n'
            '    | 2 = <nowiki></nowiki> a <nowiki></nowiki>\n'
            '}}',
            wtp.parse('{{t|a| a }}').pprint(),
        )

    def test_dont_treat_parser_function_arguments_as_kwargs(self):
        """The `=` is usually just a part of parameter value.

        Another example: {{fullurl:Category:Top level|action=edit}}.
        """
        self.assertEqual(
            '{{#if: true\n    | <span style="color:Blue;">text</span>\n}}',
            wtp.parse(
                '{{#if:true|<span style="color:Blue;">text</span>}}'
            ).pprint(),
        )

    def test_ignore_zwnj_for_alignment(self):
        self.assertEqual(
            '{{ا\n    | نیم\u200cفاصله       = ۱\n    | بدون نیم فاصله = ۲\n}}',
            wtp.parse('{{ا|نیم‌فاصله=۱|بدون نیم فاصله=۲}}').pprint(),
        )

    def test_arabic_ligature_lam_with_alef(self):
        """'ل' + 'ا' creates a ligature with one character width.

        Some terminal emulators do not support this but it's defined in
        Courier New font which is the main (almost only) font used for
        monospaced Persian texts on Windows. Also tested on Arabic Wikipedia.
        """
        self.assertEqual(
            '{{ا\n    | الف = ۱\n    | لا   = ۲\n}}',
            wtp.parse('{{ا|الف=۱|لا=۲}}').pprint(),
        )

    def test_pf_inside_t(self):
        wt = wtp.parse('{{t|a= {{#if:I|I}} }}')
        self.assertEqual(
            '{{t\n    | a = {{#if: I\n        | I\n    }}\n}}',
            wt.pprint(),
        )

    def test_nested_pf_inside_tl(self):
        wt = wtp.parse('{{t1|{{t2}}{{#pf:a}}}}')
        self.assertEqual(
            '{{t1\n    | 1 = {{t2}}{{#pf:a}}\n}}',
            wt.pprint(),
        )

    def test_html_tag_equal(self):
        wt = wtp.parse('{{#iferror:<t a="">|yes|no}}')
        self.assertEqual(
            '{{#iferror: <t a="">\n    | yes\n    | no\n}}',
            wt.pprint(),
        )

    @unittest.expectedFailure
    def test_pprint_pf_directly(self):
        """Templates and parser functions are not pretty-printed directly."""
        # Todo: Add support for pretty-printing templates directly.
        pf = wtp.ParserFunction('{{#iferror:<t a="">|yes|no}}')
        self.assertEqual(
            '{{#iferror: <t a="">\n    | yes\n    | no\n}}',
            pf.pprint(),
        )

    def test_function_inside_template(self):
        p = wtp.parse('{{t|{{#ifeq:||yes}}|a2}}')
        self.assertEqual(
            '{{t\n    | 1 = {{#ifeq: \n'
            '        | \n        | yes\n    }}\n    | 2 = a2\n}}',
            p.pprint(),
        )

    def test_parser_template_parser(self):
        p = wtp.parse('{{#f:c|e|{{t|a={{#g:b|c}}}}}}')
        self.assertEqual(
            '{{#f: c\n    | e\n    | {{t\n        | a = {{#g: b\n'
            '            | c\n        }}\n    }}\n}}',
            p.pprint(),
        )


class Sections(unittest.TestCase):

    """Test the sections method of the WikiText class."""

    def test_grab_the_final_newline_for_the_last_section(self):
        s = 'text1 HTTP://mediawiki.org text2'
        wt = wtp.WikiText('== s ==\nc\n')
        self.assertEqual('== s ==\nc\n', wt.sections[1].string)

    def test_blank_lead(self):
        s = 'text1 HTTP://mediawiki.org text2'
        wt = wtp.WikiText('== s ==\nc\n')
        self.assertEqual('== s ==\nc\n', wt.sections[1].string)

    @unittest.expectedFailure
    def test_multiline_with_carriage_return(self):
        s = 'text\r\n= s =\r\n{|\r\n| a \r\n|}\r\ntext'
        p = wtp.parse(s)
        self.assertEqual('text\r\n', p.sections[0].string)


class Template(unittest.TestCase):

    """Test Tempate class."""

    def test_named_parameters(self):
        s = '{{یادکرد کتاب|عنوان = ش{{--}}ش|سال=۱۳۴۵}}'
        t = wtp.Template(s)
        self.assertEqual(s, str(t))

    def test_ordered_parameters(self):
        s = '{{example|{{foo}}|bar|2}}'
        t = wtp.Template(s)
        self.assertEqual(s, str(t))

    def test_ordered_and_named_parameters(self):
        s = '{{example|para1={{foo}}|bar=3|2}}'
        t = wtp.Template(s)
        self.assertEqual(s, str(t))

    def test_no_parameters(self):
        s = '{{template}}'
        t = wtp.Template(s)
        self.assertEqual(s, str(t))

    def test_contains_newlines(self):
        s = '{{template\n|s=2}}'
        t = wtp.Template(s)
        self.assertEqual(s, str(t))

    def test_name(self):
        s1 = "{{ wrapper | p1 | {{ cite | sp1 | dateformat = ymd}} }}"
        t = wtp.Template(s1)
        self.assertEqual(' wrapper ', t.name)

    def test_dont_remove_nonkeyword_argument(self):
        t = wtp.Template("{{t|a|a}}")
        self.assertEqual("{{t|a|a}}", str(t))

    def test_set_name(self):
        t = wtp.Template("{{t|a|a}}")
        t.name = ' u '
        self.assertEqual("{{ u |a|a}}", t.string)

    def test_keyword_and_positional_args(self):
        t = wtp.Template("{{t|kw=a|1=|pa|kw2=a|pa2}}")
        self.assertEqual('1', t.arguments[2].name)

    def test_rm_first_of_dup_args(self):
        # Remove first of duplicates, keep last
        t = wtp.Template('{{template|year=9999|year=2000}}')
        t.rm_first_of_dup_args()
        self.assertEqual('{{template|year=2000}}', str(t))
        # Don't remove duplicate positional args in different positions
        s = """{{cite|{{t1}}|{{t1}}}}"""
        t = wtp.Template(s)
        t.rm_first_of_dup_args()
        self.assertEqual(s, str(t))
        # Don't remove duplicate subargs
        s1 = "{{i| c = {{g}} |p={{t|h={{g}}}} |q={{t|h={{g}}}}}}"
        t = wtp.Template(s1)
        t.rm_first_of_dup_args()
        self.assertEqual(s1, str(t))
        # test_dont_touch_empty_strings
        s1 = '{{template|url=||work=|accessdate=}}'
        s2 = '{{template|url=||work=|accessdate=}}'
        t = wtp.Template(s1)
        t.rm_first_of_dup_args()
        self.assertEqual(s2, str(t))
        # Positional args
        t = wtp.Template('{{t|1=v|v}}')
        t.rm_first_of_dup_args()
        self.assertEqual('{{t|v}}', str(t))
        # Triple duplicates:
        t = wtp.Template('{{t|1=v|v|1=v}}')
        t.rm_first_of_dup_args()
        self.assertEqual('{{t|1=v}}', str(t))

    def test_rm_dup_args_safe(self):
        # Don't remove duplicate positional args in different positions
        s = "{{cite|{{t1}}|{{t1}}}}"
        t = wtp.Template(s)
        t.rm_dup_args_safe()
        self.assertEqual(s, t.string)
        # Don't remove duplicate args if the have different values
        s = '{{template|year=9999|year=2000}}'
        t = wtp.Template(s)
        t.rm_dup_args_safe()
        self.assertEqual(s, t.string)
        # Detect positional and keyword duplicates
        t = wtp.Template('{{t|1=|}}')
        t.rm_dup_args_safe()
        self.assertEqual('{{t|}}', t.string)
        # Detect same-name same-value.
        # It's OK to ignore whitespace in positional arguments.
        t = wtp.Template('{{t|n=v|  n=v  }}')
        t.rm_dup_args_safe()
        self.assertEqual('{{t|  n=v  }}', t.string)
        # It's not OK to ignore whitespace in positional arguments.
        t = wtp.Template('{{t| v |1=v}}')
        t.rm_dup_args_safe()
        self.assertEqual('{{t| v |1=v}}', t.string)
        # Removing a positional argument affects the name of later ones.
        t = wtp.Template("{{t|1=|||}}")
        t.rm_dup_args_safe()
        self.assertEqual("{{t|||}}", t.string)
        # Triple duplicates
        t = wtp.Template('{{t|1=v|v|1=v}}')
        t.rm_dup_args_safe()
        self.assertEqual('{{t|1=v}}', t.string)
        # If the last duplicate has a defferent value, still remove of the
        # first two
        t = wtp.Template('{{t|1=v|v|1=u}}')
        t.rm_dup_args_safe()
        self.assertEqual('{{t|v|1=u}}', t.string)
        # tag
        # Remove safe duplicates even if tag option is activated
        t = wtp.Template('{{t|1=v|v|1=v}}')
        t.rm_dup_args_safe(tag='<!-- dup -->')
        self.assertEqual('{{t|1=v}}', t.string)
        # Tag even if one of the duplicate values is different.
        t = wtp.Template('{{t|1=v|v|1=u}}')
        t.rm_dup_args_safe(tag='<!-- dup -->')
        self.assertEqual('{{t|v<!-- dup -->|1=u}}', t.string)

    def test_has_arg(self):
        t = wtp.Template('{{t|a|b=c}}')
        self.assertEqual(True, t.has_arg('1'))
        self.assertEqual(True, t.has_arg('1', 'a'))
        self.assertEqual(True, t.has_arg('b'))
        self.assertEqual(True, t.has_arg('b', 'c'))
        self.assertEqual(False, t.has_arg('2'))
        self.assertEqual(False, t.has_arg('1', 'b'))
        self.assertEqual(False, t.has_arg('c'))
        self.assertEqual(False, t.has_arg('b', 'd'))

    def test_get_arg(self):
        t = wtp.Template('{{t|a|b=c}}')
        self.assertEqual('|a', t.get_arg('1').string)
        self.assertEqual(None, t.get_arg('c'))

    def test_name_contains_a_param_with_default(self):
        t = wtp.Template('{{t {{{p1|d1}}} | {{{p2|d2}}} }}')
        self.assertEqual('t {{{p1|d1}}} ', t.name)
        self.assertEqual('| {{{p2|d2}}} ', t.arguments[0].string)
        t.name = 'g'
        self.assertEqual('g', t.name)

    def test_overwriting_on_a_string_subspancontaining_string(self):
        t = wtp.Template('{{t {{{p1|d1}}} | {{{p2|d2}}} }}')
        t.name += 's'
        self.assertEqual('t {{{p1|d1}}} s', t.name)

    def test_overwriting_on_a_string_causes_loss_of_spans(self):
        t = wtp.Template('{{t {{{p1|d1}}} | {{{p2|d2}}} }}')
        p = t.parameters[0]
        t.name += 's'
        self.assertEqual('', p.string)

    def test_no_param_template_name(self):
        t = wtp.Template("{{صعود}}")
        self.assertEqual('صعود', t.name)


class TemplateSetArg(unittest.TestCase):

    """Test set_arg function of Template class."""

    def test_set_arg(self):
        # Template with no args, keyword
        t = wtp.Template('{{t}}')
        t.set_arg('a', 'b')
        self.assertEqual('{{t|a=b}}', t.string)
        # Template with no args, auto positional
        t = wtp.Template('{{t}}')
        t.set_arg('1', 'b')
        self.assertEqual('{{t|1=b}}', t.string)
        # Force keyword
        t = wtp.Template('{{t}}')
        t.set_arg('1', 'b', positional=False)
        self.assertEqual('{{t|1=b}}', t.string)
        # Arg already exist, positional
        t = wtp.Template('{{t|a}}')
        t.set_arg('1', 'b')
        self.assertEqual('{{t|b}}', t.string)
        # Append new keyword when there is more than one arg
        t = wtp.Template('{{t|a}}')
        t.set_arg('z', 'z')
        self.assertEqual('{{t|a|z=z}}', t.string)
        # Preserve spacing
        t = wtp.Template('{{t\n  | p1   = v1\n  | p22  = v2\n}}')
        t.set_arg('z', 'z')
        self.assertEqual(
            '{{t\n  | p1   = v1\n  | p22  = v2\n  | z    = z\n}}', t.string
        )
        # Preserve spacing, only one argument
        t = wtp.Template('{{t\n  |  afadfaf =   value \n}}')
        t.set_arg('z', 'z')
        self.assertEqual(
            '{{t\n  |  afadfaf =   value\n  |  z       =   z\n}}', t.string
        )

    def test_before(self):
        t = wtp.Template('{{t|a|b|c=c|d}}')
        t.set_arg('e', 'e', before='c')
        self.assertEqual('{{t|a|b|e=e|c=c|d}}', t.string)

    def test_after(self):
        t = wtp.Template('{{t|a|b|c=c|d}}')
        t.set_arg('e', 'e', after='c')
        self.assertEqual('{{t|a|b|c=c|e=e|d}}', t.string)

    def test_multi_set_positional_args(self):
        t = wtp.Template('{{t}}')
        t.set_arg('1', 'p', positional=True)
        t.set_arg('2', 'q', positional=True)
        self.assertEqual('{{t|p|q}}', t.string)

    @unittest.expectedFailure
    def test_invalid_position(self):
        t = wtp.Template('{{t}}')
        t.set_arg('2', 'a', positional=True)
        self.assertEqual('{{t|2=a}}', t.string)

    def test_force_new_to_positional_when_old_is_keyword(self):
        t = wtp.Template('{{t|1=v}}')
        t.set_arg('1', 'v', positional=True)
        self.assertEqual('{{t|v}}', t.string)


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


class Tag(unittest.TestCase):

    """Test the Tag class."""

    @unittest.expectedFailure
    def test_basic(self):
        t = wtp.Tag('<ref>text</ref>')


if __name__ == '__main__':
    tests = unittest.defaultTestLoader.discover('.', '*_test.py')
    runner = unittest.runner.TextTestRunner()
    runner.run(tests)
