"""Test the functionalities of spans.py."""


import unittest

import spans
import wikitextparser as wtp


class Spans(unittest.TestCase):
    """Test the spans."""

    def test_template_name_cannot_be_empty(self):
        wt = wtp.WikiText('{{_}}')
        self.assertEqual(wt._type_to_spans['Template'], [])
        wt = wtp.WikiText('{{_|text}}')
        self.assertEqual(wt._type_to_spans['Template'], [])
        wt = wtp.WikiText('{{text| {{_}} }}')
        self.assertEqual(len(wt._type_to_spans['Template']), 1)
        wt = wtp.WikiText('{{ {{_|text}} | a }}')
        self.assertEqual(len(wt._type_to_spans['Template']), 0)

    def test_template_in_template(self):
        wt = wtp.WikiText("""{{cite|{{t1}}|{{t2}}}}""")
        template_spans = wt._type_to_spans['Template']
        self.assertIn((7, 13), template_spans)
        self.assertIn((14, 20), template_spans)
        self.assertIn((0, 22), template_spans)

    def test_textmixed_multitemplate(self):
        wt = wtp.WikiText(
            "text1{{cite|{{t1}}|{{t2}}}}"
            "text2{{cite|{{t3}}|{{t4}}}}text3"
        )
        self.assertEqual(
            wt._type_to_spans['Template'],
            [(12, 18), (19, 25), (39, 45), (46, 52), (5, 27), (32, 54)],
        )

    def test_multiline_mutitemplate(self):
        wt = wtp.WikiText("""{{cite\n    |{{t1}}\n    |{{t2}}}}""")
        self.assertEqual(
            wt._type_to_spans['Template'],
            [(12, 18), (24, 30), (0, 32)],
        )

    def test_lacks_ending_braces(self):
        wt = wtp.WikiText("""{{cite|{{t1}}|{{t2}}""")
        self.assertEqual(
            [(7, 13), (14, 20)],
            wt._type_to_spans['Template'],
        )

    def test_lacks_starting_braces(self):
        wt = wtp.WikiText("""cite|{{t1}}|{{t2}}}}""")
        self.assertEqual(
            [(5, 11), (12, 18)],
            wt._type_to_spans['Template'],
        )

    def test_no_template_for_braces_around_wikilink(self):
        wt = wtp.WikiText("{{[[a]]}}")
        self.assertEqual(
            [],
            wt._type_to_spans['Template'],
        )

    def test_template_inside_parameter(self):
        wt = wtp.WikiText("""{{{1|{{colorbox|yellow|text1}}}}}""")
        self.assertEqual(
            [(5, 30)],
            wt._type_to_spans['Template'],
        )
        self.assertEqual(
            [(0, 33)],
            wt._type_to_spans['Parameter'],
        )

    def test_parameter_inside_template(self):
        wt = wtp.WikiText("""{{colorbox|yellow|{{{1|defualt_text}}}}}""")
        self.assertEqual(
            [(0, 40)],
            wt._type_to_spans['Template'],
        )
        self.assertEqual(
            [(18, 38)],
            wt._type_to_spans['Parameter'],
        )

    def test_template_name_cannot_contain_newline(self):
        tl = wtp.WikiText('{{\nColor\nbox\n|mytext}}')
        self.assertEqual(
            [],
            tl._type_to_spans['Template'],
        )

    def test_unicode_template(self):
        wt = wtp.WikiText('{{\nرنگ\n|متن}}')
        self.assertEqual(
            [(0, 13)],
            wt._type_to_spans['Template'],
        )

    def test_invoking_a_named_ref_is_not_a_ref_start(self):
        """See [[mw:Extension:Cite#Multiple_uses_of_the_same_footnote]].

        [[mw:Help:Extension:Cite]] may be helpful, too.

        """
        wt = wtp.WikiText(
            '{{text|1=v<ref name=n/>}}\ntext.<ref name=n>r</ref>'
        )
        self.assertEqual(
            [(0, 25)],
            wt._type_to_spans['Template'],
        )

    def test_invalid_refs_that_should_not_produce_any_template(self):
        wt = wtp.WikiText('f {{text|<ref \n > g}} <ref  name=n />\n</ref  >\n')
        self.assertEqual(
            [],
            wt._type_to_spans['Template'],
        )

    def test_unicode_parser_function(self):
        wt = wtp.WikiText('{{#اگر:|فلان}}')
        self.assertEqual(
            [(0, 14)],
            wt._type_to_spans['ParserFunction'],
        )

    def test_unicode_parameters(self):
        wt = wtp.WikiText('{{{پارا۱|{{{پارا۲|پيشفرض}}}}}}')
        self.assertEqual(
            [(9, 27), (0, 30)],
            wt._type_to_spans['Parameter'],
        )

    def test_image_containing_wikilink(self):
        parsed = wtp.parse(
            "[[File:xyz.jpg|thumb|1px|txt1 [[wikilink1]] txt2 [[Wikilink2]].]]"
        )
        self.assertEqual(
            [(30, 43), (49, 62), (0, 65)],
            parsed._type_to_spans['WikiLink'],
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
        self. assertRegex(b'{{PROTECTIONLEVEL:action}}', regex)
        self. assertRegex(b'{{DISPLAYTITLE:title}}', regex)
        self. assertRegex(b'{{DEFAULTCATEGORYSORT:sortkey}}', regex)
        self. assertRegex(b'{{DEFAULTSORT:sortkey}}', regex)
        self. assertRegex(b'{{DEFAULTSORTKEY:sortkey}}', regex)
        self. assertRegex(b'{{PROTECTIONEXPIRY:action}}', regex)
        # Statistic variables
        self. assertRegex(b'{{NUMBEROFPAGES:R}}', regex)
        self. assertRegex(b'{{NUMBEROFARTICLES:R}}', regex)
        self. assertRegex(b'{{NUMBEROFFILES:R}}', regex)
        self. assertRegex(b'{{NUMBEROFEDITS:R}}', regex)
        self. assertRegex(b'{{NUMBEROFVIEWS:R}}', regex)
        self. assertRegex(b'{{NUMBEROFUSERS:R}}', regex)
        self. assertRegex(b'{{NUMBEROFADMINS:R}}', regex)
        self. assertRegex(b'{{PAGESINCATEGORY:categoryname}}', regex)
        self. assertRegex(b'{{PAGESINCAT:categoryname}}', regex)
        self. assertRegex(b'{{PAGESINCATEGORY:categoryname|all}}', regex)
        self. assertRegex(b'{{NUMBERINGROUP:groupname}}', regex)
        self. assertRegex(b'{{NUMINGROUP:groupname}}', regex)
        self. assertRegex(b'{{PAGESINNS:index}}', regex)
        self. assertRegex(b'{{PAGESINNAMESPACE:index}}', regex)
        # Page name variables
        self. assertRegex(b'{{FULLPAGENAME:page}}', regex)
        self. assertRegex(b'{{PAGENAME:page}}', regex)
        self. assertRegex(b'{{BASEPAGENAME:page}}', regex)
        self. assertRegex(b'{{SUBPAGENAME:page}}', regex)
        self. assertRegex(b'{{SUBJECTPAGENAME:page}}', regex)
        self. assertRegex(b'{{ARTICLEPAGENAME:page}}', regex)
        self. assertRegex(b'{{TALKPAGENAME:page}}', regex)
        self. assertRegex(b'{{ROOTPAGENAME:page}}', regex)
        # URL encoded page name variables
        self. assertRegex(b'{{FULLPAGENAMEE:page}}', regex)
        self. assertRegex(b'{{PAGENAMEE:page}}', regex)
        self. assertRegex(b'{{BASEPAGENAMEE:page}}', regex)
        self. assertRegex(b'{{SUBPAGENAMEE:page}}', regex)
        self. assertRegex(b'{{SUBJECTPAGENAMEE:page}}', regex)
        self. assertRegex(b'{{ARTICLEPAGENAMEE:page}}', regex)
        self. assertRegex(b'{{TALKPAGENAMEE:page}}', regex)
        self. assertRegex(b'{{ROOTPAGENAMEE:page}}', regex)
        # Namespace variables
        self. assertRegex(b'{{NAMESPACE:page}}', regex)
        self. assertRegex(b'{{NAMESPACENUMBER:page}}', regex)
        self. assertRegex(b'{{SUBJECTSPACE:page}}', regex)
        self. assertRegex(b'{{ARTICLESPACE:page}}', regex)
        self. assertRegex(b'{{TALKSPACE:page}}', regex)
        # Encoded namespace variables
        self. assertRegex(b'{{NAMESPACEE:page}}', regex)
        self. assertRegex(b'{{SUBJECTSPACEE:page}}', regex)
        self. assertRegex(b'{{ARTICLESPACEE:page}}', regex)
        self. assertRegex(b'{{TALKSPACEE:page}}', regex)
        # Technical metadata parser functions
        self. assertRegex(b'{{PAGEID: page name }}', regex)
        self. assertRegex(b'{{PAGESIZE: page name }}', regex)
        self. assertRegex(b'{{PROTECTIONLEVEL:action | page name}}', regex)
        self. assertRegex(b'{{CASCADINGSOURCES:page name}}', regex)
        self. assertRegex(b'{{REVISIONID: page name }}', regex)
        self. assertRegex(b'{{REVISIONDAY: page name }}', regex)
        self. assertRegex(b'{{REVISIONDAY2: page name }}', regex)
        self. assertRegex(b'{{REVISIONMONTH: page name }}', regex)
        self. assertRegex(b'{{REVISIONMONTH1: page name }}', regex)
        self. assertRegex(b'{{REVISIONYEAR: page name }}', regex)
        self. assertRegex(b'{{REVISIONTIMESTAMP: page name }}', regex)
        self. assertRegex(b'{{REVISIONUSER: page name }}', regex)
        # URL data parser functions
        self. assertRegex(b'{{localurl:page name}}', regex)
        self. assertRegex(b'{{fullurl:page name}}', regex)
        self. assertRegex(b'{{canonicalurl:page name}}', regex)
        self. assertRegex(b'{{filepath:file name}}', regex)
        self. assertRegex(b'{{urlencode:string}}', regex)
        self. assertRegex(b'{{anchorencode:string}}', regex)
        # Namespace parser functions
        self. assertRegex(b'{{ns:-2}}', regex)
        self. assertRegex(b'{{nse:}}', regex)
        # Formatting parser functions
        self. assertRegex(b'{{formatnum:unformatted number}}', regex)
        self. assertRegex(b'{{lc:string}}', regex)
        self. assertRegex(b'{{lcfirst:string}}', regex)
        self. assertRegex(b'{{uc:string}}', regex)
        self. assertRegex(b'{{ucfirst:string}}', regex)
        self. assertRegex(b'{{padleft:xyz|stringlength}}', regex)
        self. assertRegex(b'{{padright:xyz|stringlength}}', regex)
        # Localization parser functions
        self. assertRegex(b'{{plural:2|is|are}}', regex)
        self. assertRegex(b'{{grammar:N|noun}}', regex)
        self. assertRegex(b'{{gender:username|text for every gender}}', regex)
        self. assertRegex(b'{{int:message name}}', regex)
        # Transclusion modifiers
        # May change in the future.
        self.assertNotRegex(b'{{msg:xyz}}', regex)
        self.assertNotRegex(b'{{raw:xyz}}', regex)
        self.assertNotRegex(b'{{raw:xyz}}', regex)
        # Miscellaneous
        self. assertRegex(b'{{#language:language code}}', regex)

    def test_wikilinks_inside_exttags(self):
        wt = wtp.WikiText("<ref>[[w]]</ref>")
        self.assertEqual(
            [(5, 10)],
            wt._type_to_spans['WikiLink'],
        )

if __name__ == '__main__':
    unittest.main()
