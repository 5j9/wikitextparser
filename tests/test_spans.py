"""Test the functionalities of spans.py."""


from unittest import expectedFailure, main, TestCase

# noinspection PyProtectedMember
from wikitextparser._spans import PARSER_FUNCTION_FINDITER, parse_to_spans
import wikitextparser as wtp


class Spans(TestCase):
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
        wt = wtp.WikiText('{{cite|{{t1}}|{{t2}}}}')
        template_spans = wt._type_to_spans['Template']
        self.assertIn([7, 13], template_spans)
        self.assertIn([14, 20], template_spans)
        self.assertIn([0, 22], template_spans)

    def test_textmixed_multitemplate(self):
        wt = wtp.WikiText(
            'text1{{cite|{{t1}}|{{t2}}}}'
            'text2{{cite|{{t3}}|{{t4}}}}text3'
        )
        self.assertEqual(
            wt._type_to_spans['Template'],
            [[5, 27], [12, 18], [19, 25], [32, 54], [39, 45], [46, 52]],
        )

    def test_multiline_mutitemplate(self):
        wt = wtp.WikiText('{{cite\n    |{{t1}}\n    |{{t2}}}}')
        self.assertEqual(
            wt._type_to_spans['Template'],
            [[0, 32], [12, 18], [24, 30]],
        )

    def test_lacks_ending_braces(self):
        wt = wtp.WikiText('{{cite|{{t1}}|{{t2}}')
        self.assertEqual(
            [[7, 13], [14, 20]],
            wt._type_to_spans['Template'],
        )

    def test_lacks_starting_braces(self):
        wt = wtp.WikiText('cite|{{t1}}|{{t2}}}}')
        self.assertEqual(
            [[5, 11], [12, 18]],
            wt._type_to_spans['Template'],
        )

    def test_no_template_for_braces_around_wikilink(self):
        wt = wtp.WikiText('{{[[a]]}}')
        self.assertEqual(
            [],
            wt._type_to_spans['Template'],
        )

    def test_template_inside_parameter(self):
        wt = wtp.WikiText('{{{1|{{colorbox|yellow|text1}}}}}')
        self.assertEqual(
            [[5, 30]],
            wt._type_to_spans['Template'],
        )
        self.assertEqual(
            [[0, 33]],
            wt._type_to_spans['Parameter'],
        )

    def test_parameter_inside_template(self):
        wt = wtp.WikiText('{{colorbox|yellow|{{{1|defualt_text}}}}}')
        self.assertEqual(
            [[0, 40]],
            wt._type_to_spans['Template'],
        )
        self.assertEqual(
            [[18, 38]],
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
            [[0, 13]],
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
            [[0, 25]],
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
            [[0, 14]],
            wt._type_to_spans['ParserFunction'],
        )

    def test_unicode_parameters(self):
        wt = wtp.WikiText('{{{پارا۱|{{{پارا۲|پيشفرض}}}}}}')
        self.assertEqual(
            [[0, 30], [9, 27]],
            wt._type_to_spans['Parameter'],
        )

    def test_image_containing_wikilink(self):
        parsed = wtp.parse(
            "[[File:xyz.jpg|thumb|1px|txt1 [[wikilink1]] txt2 [[Wikilink2]].]]"
        )
        self.assertEqual(
            [[0, 65], [30, 43], [49, 62]],
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
        finditer = PARSER_FUNCTION_FINDITER
        parser_functions = (
            # Technical metadata variables
            b'{{PROTECTIONLEVEL:action}}',
            b'{{DISPLAYTITLE:title}}',
            b'{{DEFAULTCATEGORYSORT:sortkey}}',
            b'{{DEFAULTSORT:sortkey}}',
            b'{{DEFAULTSORTKEY:sortkey}}',
            b'{{PROTECTIONEXPIRY:action}}',
            # Statistic variables
            b'{{NUMBEROFPAGES:R}}',
            b'{{NUMBEROFARTICLES:R}}',
            b'{{NUMBEROFFILES:R}}',
            b'{{NUMBEROFEDITS:R}}',
            b'{{NUMBEROFVIEWS:R}}',
            b'{{NUMBEROFUSERS:R}}',
            b'{{NUMBEROFADMINS:R}}',
            b'{{PAGESINCATEGORY:categoryname}}',
            b'{{PAGESINCAT:categoryname}}',
            b'{{PAGESINCATEGORY:categoryname|all}}',
            b'{{NUMBERINGROUP:groupname}}',
            b'{{NUMINGROUP:groupname}}',
            b'{{PAGESINNS:index}}',
            b'{{PAGESINNAMESPACE:index}}',
            # Page name variables
            b'{{FULLPAGENAME:page}}',
            b'{{PAGENAME:page}}',
            b'{{BASEPAGENAME:page}}',
            b'{{SUBPAGENAME:page}}',
            b'{{SUBJECTPAGENAME:page}}',
            b'{{ARTICLEPAGENAME:page}}',
            b'{{TALKPAGENAME:page}}',
            b'{{ROOTPAGENAME:page}}',
            # URL encoded page name variables
            b'{{FULLPAGENAMEE:page}}',
            b'{{PAGENAMEE:page}}',
            b'{{BASEPAGENAMEE:page}}',
            b'{{SUBPAGENAMEE:page}}',
            b'{{SUBJECTPAGENAMEE:page}}',
            b'{{ARTICLEPAGENAMEE:page}}',
            b'{{TALKPAGENAMEE:page}}',
            b'{{ROOTPAGENAMEE:page}}',
            # Namespace variables
            b'{{NAMESPACE:page}}',
            b'{{NAMESPACENUMBER:page}}',
            b'{{SUBJECTSPACE:page}}',
            b'{{ARTICLESPACE:page}}',
            b'{{TALKSPACE:page}}',
            # Encoded namespace variables
            b'{{NAMESPACEE:page}}',
            b'{{SUBJECTSPACEE:page}}',
            b'{{ARTICLESPACEE:page}}',
            b'{{TALKSPACEE:page}}',
            # Technical metadata parser functions
            b'{{PAGEID: page name }}',
            b'{{PAGESIZE: page name }}',
            b'{{PROTECTIONLEVEL:action | page name}}',
            b'{{CASCADINGSOURCES:page name}}',
            b'{{REVISIONID: page name }}',
            b'{{REVISIONDAY: page name }}',
            b'{{REVISIONDAY2: page name }}',
            b'{{REVISIONMONTH: page name }}',
            b'{{REVISIONMONTH1: page name }}',
            b'{{REVISIONYEAR: page name }}',
            b'{{REVISIONTIMESTAMP: page name }}',
            b'{{REVISIONUSER: page name }}',
            # URL data parser functions
            b'{{localurl:page name}}',
            b'{{fullurl:page name}}',
            b'{{canonicalurl:page name}}',
            b'{{filepath:file name}}',
            b'{{urlencode:string}}',
            b'{{anchorencode:string}}',
            # Namespace parser functions
            b'{{ns:-2}}',
            b'{{nse:}}',
            # Formatting parser functions
            b'{{formatnum:unformatted number}}',
            b'{{lc:string}}',
            b'{{lcfirst:string}}',
            b'{{uc:string}}',
            b'{{ucfirst:string}}',
            b'{{padleft:xyz|stringlength}}',
            b'{{padright:xyz|stringlength}}',
            # Localization parser functions
            b'{{plural:2|is|are}}',
            b'{{grammar:N|noun}}',
            b'{{gender:username|text for every gender}}',
            b'{{int:message name}}',
            # Miscellaneous
            b'{{#language:language code}}',
        )
        for pf in parser_functions:
            self.assertEqual(next(finditer(pf))[0], pf)
        # Transclusion modifiers
        # May change in the future.
        self.assertFalse(list(finditer(b'{{msg:xyz}}')))
        self.assertFalse(list(finditer(b'{{raw:xyz}}')))
        self.assertFalse(list(finditer(b'{{raw:xyz}}')))

    def test_wikilinks_inside_exttags(self):
        self.assertEqual(
            [[5, 10]],
            wtp.WikiText('<ref>[[w]]</ref>')._type_to_spans['WikiLink'],
        )

    def test_single_brace_in_tl(self):
        self.assertEqual(
            [[0, 12]],
            parse_to_spans(bytearray(b'{{text|i}n}}'))['Template'],
        )

    def test_single_brace_after_first_tl_removal(self):
        self.assertEqual(
            [[0, 20], [7, 16]],
            parse_to_spans(bytearray(b'{{text|{{text|}}} }}'))['Template'],
        )

    def test_parse_inner_contents_of_wikilink_inside_ref(self):
        self.assertEqual(
            [[7, 20]],
            parse_to_spans(bytearray(
                b'<ref>[[{{text|link}}]]</ref>'
            ))['Template'],
        )

    def test_nested_param_semiparser(self):
        self.assertEqual(
            [[1, 14]],
            parse_to_spans(bytearray(
                b'{{{#if:v|y|n}}}'
            ))['ParserFunction'],
        )

    def test_single_brace_after_pf_remove(self):
        self.assertEqual(
            {
                'Parameter': [], 'ParserFunction': [[4, 17]],
                'Template': [[1, 21]], 'WikiLink': [], 'Comment': [],
                'ExtensionTag': []
            },
            parse_to_spans(bytearray(
                b'{{{ {{#if:v|y|n}}} }}'
            ))
        )

    def test_nested_wikilinks_in_ref(self):
        self.assertEqual(
            {
                'Parameter': [], 'ParserFunction': [],
                'Template': [], 'WikiLink': [[5, 40], [30, 38]], 'Comment': [],
                'ExtensionTag': [[0, 46]]
            },
            parse_to_spans(bytearray(
                b'<ref>[[File:Example.jpg|thumb|[[Link]]]]</ref>'
            ))
        )

    @expectedFailure
    def test_invalid_nested_wikilinks(self):
        self.assertEqual(
            {
                'Parameter': [], 'ParserFunction': [],
                'Template': [], 'WikiLink': [[10, 15]], 'Comment': [],
                'ExtTag': [[0, 24]]
            },
            parse_to_spans(bytearray(
                b'<ref>[[L| [[S]] ]]</ref>'
            ))
        )

    @expectedFailure
    def test_invalid_nested_wikilinks_in_ref(self):
        self.assertEqual(
            {
                'Parameter': [], 'ParserFunction': [],
                'Template': [], 'WikiLink': [[0, 13]], 'Comment': [],
                'ExtTag': []
            },
            parse_to_spans(bytearray(
                b'[[L| [[S]] ]]'
            ))
        )


if __name__ == '__main__':
    main()
