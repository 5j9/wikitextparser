"""Test the functionalities of spans.py."""


import sys
import unittest

import spans
sys.path.insert(0, '..')
from wikitextparser import wikitextparser as wtp


class Spans(unittest.TestCase):

    """Test the spans."""

    def test_template_in_template(self):
        wt = wtp.WikiText("""{{cite|{{t1}}|{{t2}}}}""")
        template_spans =  wt._spans['templates']
        self.assertIn((7, 13), template_spans)
        self.assertIn((14, 20), template_spans)
        self.assertIn((0, 22), template_spans)

    def test_textmixed_multitemplate(self):
        wt = wtp.WikiText(
            "text1{{cite|{{t1}}|{{t2}}}}"
            "text2{{cite|{{t3}}|{{t4}}}}text3"
        )
        self.assertEqual(
            wt._spans['templates'],
            [(12, 18), (19, 25), (39, 45), (46, 52), (5, 27), (32, 54)],
        )

    def test_multiline_mutitemplate(self):
        wt = wtp.WikiText("""{{cite\n    |{{t1}}\n    |{{t2}}}}""")
        self.assertEqual(
            wt._spans['templates'],
            [(12, 18), (24, 30), (0, 32)],
        )

    def test_lacks_ending_braces(self):
        wt = wtp.WikiText("""{{cite|{{t1}}|{{t2}}""")
        self.assertEqual(
            [(7, 13), (14, 20)],
            wt._spans['templates'],
        )

    def test_lacks_starting_braces(self):
        wt = wtp.WikiText("""cite|{{t1}}|{{t2}}}}""")
        self.assertEqual(
            [(5, 11), (12, 18)],
            wt._spans['templates'],
        )

    def test_template_inside_parameter(self):
        wt = wtp.WikiText("""{{{1|{{colorbox|yellow|text1}}}}}""")
        self.assertEqual(
            [(5, 30)],
            wt._spans['templates'],
        )
        self.assertEqual(
            [(0, 33)],
            wt._spans['parameters'],
        )

    def test_parameter_inside_template(self):
        wt = wtp.WikiText("""{{colorbox|yellow|{{{1|defualt_text}}}}}""")
        self.assertEqual(
            [(0, 40)],
            wt._spans['templates'],
        )
        self.assertEqual(
            [(18, 38)],
            wt._spans['parameters'],
        )

    def test_template_name_cannot_contain_newline(self):
        tl = wtp.WikiText('{{\nColor\nbox\n|mytext}}')
        self.assertEqual(
            [],
            tl._spans['templates'],
        )

    def test_unicode_template(self):
        wt = wtp.WikiText('{{\nرنگ\n|متن}}')
        self.assertEqual(
            [(0, 13)],
            wt._spans['templates'],
        )

    def test_unicode_parser_function(self):
        wt = wtp.WikiText('{{#اگر:|فلان}}')
        self.assertEqual(
            [(0, 14)],
            wt._spans['functions'],
        )

    def test_unicode_parameters(self):
        wt = wtp.WikiText('{{{پارا۱|{{{پارا۲|پيشفرض}}}}}}')
        self.assertEqual(
            [(9, 27), (0, 30)],
            wt._spans['parameters'],
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
        wt = wtp.WikiText(
            '\n== 1 ==\n== 2 ==\n=== 2.1 ===\n==== 2.1.1 ====\n'
            '===== 2.1.1.1 =====\n=== 2.2 ===\n=== 2.3 ===\n==== 2.3.1 ====\n'
            '2.3.1\n== 3 ==\n'
        )
        self.assertEqual(
            "[Section('\\n'), Section('== 1 ==\\n'), "
            "Section('== 2 ==\\n=== 2.1 ===\\n==== 2.1.1 ====\\n"
            "===== 2.1.1.1 =====\\n=== 2.2 ===\\n=== 2.3 ===\\n"
            "==== 2.3.1 ====\\n2.3.1\\n'), Section('=== 2.1 ===\\n"
            "==== 2.1.1 ====\\n===== 2.1.1.1 =====\\n'), "
            "Section('==== 2.1.1 ====\\n===== 2.1.1.1 =====\\n'), "
            "Section('===== 2.1.1.1 =====\\n'), Section('=== 2.2 ===\\n'), "
            "Section('=== 2.3 ===\\n==== 2.3.1 ====\\n2.3.1\\n'), "
            "Section('==== 2.3.1 ====\\n2.3.1\\n'), Section('== 3 ==\\n')]",
            str(wt.sections)
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

    def test_parser_function_regex(self):
        regex = spans.PARSER_FUNCTION_REGEX
        # Technical metadata variables
        self. assertRegex('{{PROTECTIONLEVEL:action}}', regex)
        self. assertRegex('{{DISPLAYTITLE:title}}', regex)
        self. assertRegex('{{DEFAULTCATEGORYSORT:sortkey}}', regex)
        self. assertRegex('{{DEFAULTSORT:sortkey}}', regex)
        self. assertRegex('{{DEFAULTSORTKEY:sortkey}}', regex)
        # Statistic variables
        self. assertRegex('{{NUMBEROFPAGES:R}}', regex)
        self. assertRegex('{{NUMBEROFARTICLES:R}}', regex)
        self. assertRegex('{{NUMBEROFFILES:R}}', regex)
        self. assertRegex('{{NUMBEROFEDITS:R}}', regex)
        self. assertRegex('{{NUMBEROFVIEWS:R}}', regex)
        self. assertRegex('{{NUMBEROFUSERS:R}}', regex)
        self. assertRegex('{{NUMBEROFADMINS:R}}', regex)
        self. assertRegex('{{PAGESINCATEGORY:categoryname}}', regex)
        self. assertRegex('{{PAGESINCAT:categoryname}}', regex)
        self. assertRegex('{{PAGESINCATEGORY:categoryname|all}}', regex)
        self. assertRegex('{{NUMBERINGROUP:groupname}}', regex)
        self. assertRegex('{{NUMINGROUP:groupname}}', regex)
        self. assertRegex('{{PAGESINNS:index}}', regex)
        self. assertRegex('{{PAGESINNAMESPACE:index}}', regex)
        # Page name variables
        self. assertRegex('{{FULLPAGENAME:page}}', regex)
        self. assertRegex('{{PAGENAME:page}}', regex)
        self. assertRegex('{{BASEPAGENAME:page}}', regex)
        self. assertRegex('{{SUBPAGENAME:page}}', regex)
        self. assertRegex('{{SUBJECTPAGENAME:page}}', regex)
        self. assertRegex('{{ARTICLEPAGENAME:page}}', regex)
        self. assertRegex('{{TALKPAGENAME:page}}', regex)
        self. assertRegex('{{ROOTPAGENAME:page}}', regex)
        # URL encoded page name variables
        self. assertRegex('{{FULLPAGENAMEE:page}}', regex)
        self. assertRegex('{{PAGENAMEE:page}}', regex)
        self. assertRegex('{{BASEPAGENAMEE:page}}', regex)
        self. assertRegex('{{SUBPAGENAMEE:page}}', regex)
        self. assertRegex('{{SUBJECTPAGENAMEE:page}}', regex)
        self. assertRegex('{{ARTICLEPAGENAMEE:page}}', regex)
        self. assertRegex('{{TALKPAGENAMEE:page}}', regex)
        self. assertRegex('{{ROOTPAGENAMEE:page}}', regex)
        # Namespace variables
        self. assertRegex('{{NAMESPACE:page}}', regex)
        self. assertRegex('{{NAMESPACENUMBER:page}}', regex)
        self. assertRegex('{{SUBJECTSPACE:page}}', regex)
        self. assertRegex('{{ARTICLESPACE:page}}', regex)
        self. assertRegex('{{TALKSPACE:page}}', regex)
        # Encoded namespace variables
        self. assertRegex('{{NAMESPACEE:page}}', regex)
        self. assertRegex('{{SUBJECTSPACEE:page}}', regex)
        self. assertRegex('{{ARTICLESPACEE:page}}', regex)
        self. assertRegex('{{TALKSPACEE:page}}', regex)
        # Technical metadata parser functions
        self. assertRegex('{{PAGEID: page name }}', regex)
        self. assertRegex('{{PAGESIZE: page name }}', regex)
        self. assertRegex('{{PROTECTIONLEVEL:action | page name}}', regex)
        self. assertRegex('{{CASCADINGSOURCES:page name}}', regex)
        self. assertRegex('{{REVISIONID: page name }}', regex)
        self. assertRegex('{{REVISIONDAY: page name }}', regex)
        self. assertRegex('{{REVISIONDAY2: page name }}', regex)
        self. assertRegex('{{REVISIONMONTH: page name }}', regex)
        self. assertRegex('{{REVISIONMONTH1: page name }}', regex)
        self. assertRegex('{{REVISIONYEAR: page name }}', regex)
        self. assertRegex('{{REVISIONTIMESTAMP: page name }}', regex)
        self. assertRegex('{{REVISIONUSER: page name }}', regex)
        # URL data parser functions
        self. assertRegex('{{localurl:page name}}', regex)
        self. assertRegex('{{fullurl:page name}}', regex)
        self. assertRegex('{{canonicalurl:page name}}', regex)
        self. assertRegex('{{filepath:file name}}', regex)
        self. assertRegex('{{urlencode:string}}', regex)
        self. assertRegex('{{anchorencode:string}}', regex)
        # Namespace parser functions
        self. assertRegex('{{ns:-2}}', regex)
        self. assertRegex('{{nse:}}', regex)
        # Formatting parser functions
        self. assertRegex('{{formatnum:unformatted number}}', regex)
        self. assertRegex('{{lc:string}}', regex)
        self. assertRegex('{{lcfirst:string}}', regex)
        self. assertRegex('{{uc:string}}', regex)
        self. assertRegex('{{ucfirst:string}}', regex)
        self. assertRegex('{{padleft:xyz|stringlength}}', regex)
        self. assertRegex('{{padright:xyz|stringlength}}', regex)
        # Localization parser functions
        self. assertRegex('{{plural:2|is|are}}', regex)
        self. assertRegex('{{grammar:N|noun}}', regex)
        self. assertRegex('{{gender:username|text for every gender}}', regex)
        self. assertRegex('{{int:message name}}', regex)
        # Transclusion modifiers
        # May change in the future.
        self.assertNotRegex('{{msg:xyz}}', regex)
        self.assertNotRegex('{{raw:xyz}}', regex)
        self.assertNotRegex('{{raw:xyz}}', regex)
        # Miscellaneous
        self. assertRegex('{{#language:language code}}', regex)

if __name__ == '__main__':
    unittest.main()
