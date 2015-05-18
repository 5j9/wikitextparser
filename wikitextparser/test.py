import unittest
import wikitextparser as wtp
from pprint import pprint as pp


class WikiText(unittest.TestCase):

    """Test Tempate class in wtp.py."""

    def test_grab_the_final_newline_for_the_last_section(self):
        s = 'text1 HTTP://mediawiki.org text2'
        wt = wtp.WikiText('== s ==\nc\n')
        self.assertEqual('== s ==\nc\n', wt.sections[1].string)
        
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


class SpansFunction(unittest.TestCase):

    """Test _spans."""

    def test_template_in_template(self):
        wt = wtp.WikiText("""{{cite|{{t1}}|{{t2}}}}""")
        template_spans =  wt._spans['t']
        self.assertIn((7, 13), template_spans)
        self.assertIn((14, 20), template_spans)
        self.assertIn((0, 22), template_spans)

    def test_textmixed_multitemplate(self):
        wt = wtp.WikiText(
            "text1{{cite|{{t1}}|{{t2}}}}"
            "text2{{cite|{{t3}}|{{t4}}}}text3"
        )
        self.assertEqual(
            wt._spans['t'],
            [(12, 18), (19, 25), (39, 45), (46, 52), (5, 27), (32, 54)],
        )

    def test_multiline_mutitemplate(self):
        wt = wtp.WikiText("""{{cite\n    |{{t1}}\n    |{{t2}}}}""")
        self.assertEqual(
            wt._spans['t'],
            [(12, 18), (24, 30), (0, 32)],
        )

    def test_lacks_ending_braces(self):
        wt = wtp.WikiText("""{{cite|{{t1}}|{{t2}}""")
        self.assertEqual(
            [(7, 13), (14, 20)],
            wt._spans['t'],
        )

    def test_lacks_starting_braces(self):
        wt = wtp.WikiText("""cite|{{t1}}|{{t2}}}}""")
        self.assertEqual(
            [(5, 11), (12, 18)],
            wt._spans['t'],
        )

    def test_template_inside_parameter(self):
        wt = wtp.WikiText("""{{{1|{{colorbox|yellow|text1}}}}}""")
        self.assertEqual(
            [(5, 30)],
            wt._spans['t'],
        )
        self.assertEqual(
            [(0, 33)],
            wt._spans['p'],
        )

    def test_parameter_inside_template(self):
        wt = wtp.WikiText("""{{colorbox|yellow|{{{1|defualt_text}}}}}""")
        self.assertEqual(
            [(0, 40)],
            wt._spans['t'],
        )
        self.assertEqual(
            [(18, 38)],
            wt._spans['p'],
        )

    def test_template_name_cannot_contain_newline(self):
        tl = wtp.WikiText('{{\nColor\nbox\n|mytext}}')
        self.assertEqual(
            [],
            tl._spans['t'],
        )

    def test_unicode_template(self):
        wt = wtp.WikiText('{{\nرنگ\n|متن}}')
        self.assertEqual(
            [(0, 13)],
            wt._spans['t'],
        )

    def test_unicode_parser_function(self):
        wt = wtp.WikiText('{{#اگر:|فلان}}')
        self.assertEqual(
            [(0, 14)],
            wt._spans['pf'],
        )

    def test_unicode_parameters(self):
        wt = wtp.WikiText('{{{پارا۱|{{{پارا۲|پيشفرض}}}}}}')
        self.assertEqual(
            [(9, 27), (0, 30)],
            wt._spans['p'],
        )

    def test_extracting_sections(self):
        wt = wtp.WikiText('== h2 ==\nt2\n\n=== h3 ===\nt3\n\n== h22 ==\nt22')
        sections = wt.sections
        self.assertEqual(4, len(sections))
        self.assertEqual(0, sections[0].level)
        self.assertEqual('', sections[0].title)
        self.assertEqual('', sections[0].contents)
        self.assertEqual(
            '== h2 ==\nt2\n\n=== h3 ===\nt3\n\n', str(sections[1])
        )

    @unittest.skip
    def test_section_title_may_contain_template_newline_etc(self):
        wt = wtp.WikiText('=== h3 {{text\n\n|text}}<!-- \nc -->'
                          '<nowiki>\nnw\n</nowiki> ===\nt3')
        sections = wt.sections
        self.assertEqual(2, len(sections))
        self.assertEqual(
            ' h3 {{text\n\n|text}}<!-- \nc --><nowiki>\nnw\n</nowiki> ',
            sections[1].title
        )
        self.assertEqual('t3', sections[1].contents)

    def test_keyword_and_positional_args_removal(self):
        wt = wtp.WikiText("text{{t1|kw=a|1=|pa|kw2=a|pa2}}{{t2|a|1|1=}}text")
        t1 = wt.templates[0]
        t2 = wt.templates[1]
        self.assertEqual('1', t1.arguments[2].name)
        self.assertEqual('kw2', t1.arguments[3].name)
        self.assertEqual('2', t1.arguments[4].name)
        self.assertEqual('1', t2.arguments[0].name)
        self.assertEqual('2', t2.arguments[1].name)
        self.assertEqual('1', t2.arguments[2].name)
        t1.arguments[0].string = ''
        self.assertEqual('1', t1.arguments[0].name)
        self.assertEqual('kw2', t1.arguments[2].name)
        self.assertEqual('|pa2', t1.arguments[3].string)
        self.assertEqual('1', t2.arguments[0].name)
        self.assertEqual('2', t2.arguments[1].name)
        self.assertEqual('1', t2.arguments[2].name)
        t1.arguments[1].string = ''
        self.assertEqual("text{{t1|1=|kw2=a|pa2}}{{t2|a|1|1=}}text", wt.string)
        self.assertEqual('pa2', t1.arguments[2].value)
        self.assertEqual('1', t1.arguments[2].name)
        self.assertEqual('a', t2.arguments[0].value)
        self.assertEqual('1', t2.arguments[0].name)

    def test_extension_tags(self):
        for tag in wtp.TAG_EXTENSIONS:
            s = "{{text|<" + tag + ">}}</" + tag + ">}}"
            wt = wtp.WikiText(s)
            self.assertEqual((0, len(s)), wt._spans['t'][0])
            
        s = "{{text|<!-- }} -->}}"
        wt = wtp.WikiText(s)
        self.assertEqual((0, len(s)), wt._spans['t'][0])
        
class Template(unittest.TestCase):

    """Test Tempate class in wtp.py."""

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

    def test_set_arg(self):
        # Template with no args, keyword
        t = wtp.Template('{{t}}')
        t.set_arg('a', 'b')
        self.assertEqual('{{t|a=b}}', t.string)
        # Template with no args, auto positional
        t = wtp.Template('{{t}}')
        t.set_arg('1', 'b')
        self.assertEqual('{{t|b}}', t.string)
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
        
class WikiLink(unittest.TestCase):

    """Test WikiLink functionalities."""

    def test_wikilink_target_text(self):
        wl = wtp.WikiLink('[[A | faf a\n\nfads]]')
        self.assertEqual('A ', wl.target)
        self.assertEqual(' faf a\n\nfads', wl.text)

    def test_set_target(self):
        wl = wtp.WikiLink('[[A | B]]')
        wl.target = ' C '
        self.assertEqual('[[ C | B]]', wl.string)

    def test_set_text(self):
        wl = wtp.WikiLink('[[A | B]]')
        wl.text = ' C '
        self.assertEqual('[[A | C ]]', wl.string)
        


class ExternalLinks(unittest.TestCase):
    """Test capturing of external links."""

    def test_numberedmailto(self):
        s = (
            '[mailto:'
            'info@example.org?Subject=URL%20Encoded%20Subject&body='
            'Body%20Textinfo]'
        )
        el = wtp.ExternalLink(s)
        self.assertEqual(s[1:-1], el.url)
        self.assertEqual('', el.text)
        self.assertEqual(True, el.in_brackets)

    def test_bare_link(self):
        el = wtp.ExternalLink('HTTP://mediawiki.org')
        self.assertEqual('HTTP://mediawiki.org', el.url)
        self.assertEqual('HTTP://mediawiki.org', el.text)
        self.assertEqual(False, el.in_brackets)

    def test_inbracket_with_text(self):
        el = wtp.ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
        self.assertEqual('ftp://mediawiki.org', el.url)
        self.assertEqual('mediawiki ftp', el.text)
        self.assertEqual(True, el.in_brackets)

    def test_set_text(self):
        el = wtp.ExternalLink('[ftp://mediawiki.org mediawiki ftp]')
        el.text = 'mwftp'
        self.assertEqual('[ftp://mediawiki.org mwftp]', el.string)
        el = wtp.ExternalLink('ftp://mediawiki.org')
        el.text = 'mwftp'
        self.assertEqual('[ftp://mediawiki.org mwftp]', el.string)

    def test_set_url(self):
        el = wtp.ExternalLink('[ftp://mediawiki.org mw]')
        el.url = 'https://www.mediawiki.org/'
        self.assertEqual('[https://www.mediawiki.org/ mw]', el.string)
        el = wtp.ExternalLink('ftp://mediawiki.org')
        el.url = 'https://www.mediawiki.org/'
        self.assertEqual('https://www.mediawiki.org/', el.string)
        

        
class Section(unittest.TestCase):

    """Test the Section class."""

    def test_level6(self):
        s = wtp.Section('====== == ======\n')
        self.assertEqual(6, s.level)
        self.assertEqual(' == ', s.title)

    def test_nolevel7(self):
        s = wtp.Section('======= h6 =======\n')
        self.assertEqual(6, s.level)
        self.assertEqual('= h6 =', s.title)


    def test_unbalanced_equalsigns_in_title(self):
        s = wtp.Section('====== ==   \n')
        self.assertEqual(2, s.level)
        self.assertEqual('==== ', s.title)
        
        s = wtp.Section('== ======   \n')
        self.assertEqual(2, s.level)
        self.assertEqual(' ====', s.title)
        
        s = wtp.Section('========  \n')
        self.assertEqual(3, s.level)
        self.assertEqual('==', s.title)

    def test_leadsection(self):
        s = wtp.Section('lead text. \n== section ==\ntext.')
        self.assertEqual(0, s.level)
        self.assertEqual('', s.title)

    def test_set_title(self):
        s = wtp.Section('== section ==\ntext.')
        s.title = ' newtitle '
        self.assertEqual(' newtitle ', s.title)

    @unittest.expectedFailure
    def test_lead_set_title(self):
        s = wtp.Section('lead text')
        s.title = ' newtitle '

    def test_set_contents(self):
        s = wtp.Section('== title ==\ntext.')
        s.contents = ' newcontents '
        self.assertEqual(' newcontents ', s.contents)

    def test_set_lead_contents(self):
        s = wtp.Section('lead')
        s.contents = 'newlead'
        self.assertEqual('newlead', s.string)
        

class Argument(unittest.TestCase):

    """Test the Argument class."""

    def test_basic(self):
        a = wtp.Argument('| a = b ')
        self.assertEqual(' a ', a.name)
        self.assertEqual(' b ', a.value)
        self.assertEqual(False, a.positional)

    def test_anonymous_parameter(self):
        a = wtp.Argument('| a ')
        self.assertEqual('1', a.name)
        self.assertEqual(' a ', a.value)
        
    def test_set_name(self):
        a = wtp.Argument('| a = b ')
        a.name = ' c '
        self.assertEqual('| c = b ', a.string)
        
    def test_set_value(self):
        a = wtp.Argument('| a = b ')
        a.value = ' c '
        self.assertEqual('| a = c ', a.string)

    def test_removing_last_arg_should_not_effect_the_others(self):
        a, b, c = wtp.Template('{{t|1=v|v|1=v}}').arguments
        c.string = ''
        self.assertEqual('|1=v', a.string)
        self.assertEqual('|v', b.string)

    def test_nowikied_arg(self):
        a = wtp.Argument('|<nowiki>1=3</nowiki>')
        self.assertEqual(True, a.positional)
        self.assertEqual('1', a.name)
        self.assertEqual('<nowiki>1=3</nowiki>', a.value)
        

class ParserFunction(unittest.TestCase):

    """Test the ParserFunction class."""

    def test_basic(self):
        pf = wtp.ParserFunction('{{ #if: test | true | false }}')
        self.assertEqual('if', pf.name)
        self.assertEqual(
            [': test ', '| true ', '| false '],
            [a.string for a in pf.arguments]
        )

class Parameter(unittest.TestCase):

    """Test the ParserFunction class."""

    def test_basic(self):
        p = wtp.Parameter('{{{P}}}')
        self.assertEqual('P', p.name)
        self.assertEqual('', p.pipe)
        self.assertEqual('', p.default)
        p.name = ' Q '
        self.assertEqual('{{{ Q }}}', p.string)
        p.default = ' V '
        self.assertEqual('{{{ Q | V }}}', p.string)
        p = wtp.Parameter('{{{P|D}}}')
        self.assertEqual('P', p.name)
        self.assertEqual('|', p.pipe)
        self.assertEqual('D', p.default)
        p.name = ' Q '
        self.assertEqual('{{{ Q |D}}}', p.string)
        p.default = ' V '
        self.assertEqual('{{{ Q | V }}}', p.string)

    def test_appending_default(self):
        p = wtp.Parameter('{{{p1|{{{p2|}}}}}}')
        p.append_default('p3')
        self.assertEqual('{{{p1|{{{p2|{{{p3|}}}}}}}}}', p.string)
        # What happens if we try it again
        p.append_default('p4')
        self.assertEqual('{{{p1|{{{p2|{{{p4|{{{p3|}}}}}}}}}}}}', p.string)
        # Appending to and inner parameter without default
        p = wtp.Parameter('{{{p1|{{{p2}}}}}}')
        p.append_default('p3')
        self.assertEqual('{{{p1|{{{p2|{{{p3}}}}}}}}}', p.string)
        # Don't change and inner parameter which is not a default
        p = wtp.Parameter('{{{p1|head {{{p2}}} tail}}}')
        p.append_default('p3')
        self.assertEqual('{{{p1|{{{p3|head {{{p2}}} tail}}}}}}', p.string)
        # Appending to parameter with no default
        p = wtp.Parameter('{{{p1}}}')
        p.append_default('p3')
        self.assertEqual('{{{p1|{{{p3}}}}}}', p.string)
        # Preserve whitespace
        p = wtp.Parameter('{{{ p1 |{{{ p2 | }}}}}}')
        p.append_default(' p3 ')
        self.assertEqual('{{{ p1 |{{{ p2 |{{{ p3 | }}}}}}}}}', p.string)
        # White space before or after a prameter makes it a value (not default)
        p = wtp.Parameter('{{{ p1 | {{{ p2 | }}} }}}')
        p.append_default(' p3 ')
        self.assertEqual('{{{ p1 |{{{ p3 | {{{ p2 | }}} }}}}}}', p.string)
        # If the parameter already exists among defaults, it won't be added.
        p = wtp.Parameter('{{{p1|{{{p2|}}}}}}')
        p.append_default('p1')
        self.assertEqual('{{{p1|{{{p2|}}}}}}', p.string)
        p.append_default('p2')
        self.assertEqual('{{{p1|{{{p2|}}}}}}', p.string)


class Tag(unittest.TestCase):

    """Test the Tag class."""

    @unittest.expectedFailure
    def test_basic(self):
        t = wtp.Tag('<ref>text</ref>')

        
if __name__ == '__main__':
    unittest.main()
