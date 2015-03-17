import unittest
import wikitextparser as wtp


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
        self.assertEqual(s, t.string)

    def test_dont_touch_empty_strings(self):
        s1 = '{{template|url=||work=|accessdate=}}'
        s2 = '{{template|url=||work=|accessdate=}}'
        t = wtp.Template(s1)
        self.assertEqual(s2, t.string)

    def test_remove_first_duplicate_keep_last(self):
        s1 = '{{template|year=9999|year=2000}}'
        s2 = '{{template|year=2000}}'
        t = wtp.Template(s1)
        self.assertEqual(s2, t.string)

    def test_duplicate_replace(self):
        s1 = """{{cite|{{t1}}|{{t1}}}}"""
        t = wtp.Template(s1)
        self.assertEqual(s1, t.string)

    def test_name(self):
        s1 = "{{ wrapper | p1 | {{ cite | sp1 | dateformat = ymd}} }}"
        t = wtp.Template(s1)
        self.assertEqual(' wrapper ', t.name)

    def test_dont_remove_duplicate_subparameter(self):
        s1 = "{{i| c = {{g}} |p={{t|h={{g}}}} |q={{t|h={{g}}}}}}"
        t = wtp.Template(s1)
        self.assertEqual(s1, t.string)


class WikiText(unittest.TestCase):

    """Test Tempate class in wtp.py."""
    
    def test_wikilink_in_template(self):
        s1 = "{{text |[[A|}}]]}}"
        wt = wtp.WikiText(s1)
        self.assertEqual(s1, wt.get_templates()[0].string)

    def test_wikilink_containing_closing_braces_in_template(self):
        s = '{{text|[[  A   |\n|}}[]<>]]\n}}'
        wt = wtp.WikiText(s)
        self.assertEqual(s, wt.get_templates()[0].string)

    def test_ignore_comments(self):
        s1 = "{{text |<!-- }} -->}}"
        wt = wtp.WikiText(s1)
        self.assertEqual(s1, wt.get_templates()[0].string)
        
    def test_ignore_nowiki(self):
        wt = wtp.WikiText("{{text |<nowiki>}} A </nowiki> }} B")
        self.assertEqual(
            "{{text |<nowiki>}} A </nowiki> }}",
            wt.get_templates()[0].string
        )

    def test_getting_comment(self):
        wt = wtp.WikiText('text1 <!--\n\ncomment\n{{A}}\n-->text2')
        self.assertEqual(
            "\n\ncomment\n{{A}}\n",
            wt.get_comments()[0].contents
        )

    
class WikiLink(unittest.TestCase):

    """Test WikiLink functionalities."""

    def test_template_in_link(self):
        s = '[[A|{{text|text}}]]'
        wt = wtp.WikiText(s)
        self.assertEqual(s, wt.get_wikilinks()[0].string)

    def test_wikilink_target_may_contain_newline(self):
        s = '[[A | faf a\n\nfads]]'
        wt = wtp.WikiText(s)
        self.assertEqual(s, wt.get_wikilinks()[0].string)


class ExternalLinks(unittest.TestCase):
    """Test capturing of external links."""
    
    def test_bare_link(self):
        s = 'text1 HTTP://mediawiki.org text2'
        wt = wtp.WikiText(s)
        self.assertEqual(
            'HTTP://mediawiki.org',
            wt.get_external_links()[0].string
        )
        
    def test_with_lable(self):
        s = 'text1 [http://mediawiki.org MediaWiki] text2'
        wt = wtp.WikiText(s)
        self.assertEqual(
            'http://mediawiki.org',
            wt.get_external_links()[0].url
        )
        self.assertEqual(
            'MediaWiki',
            wt.get_external_links()[0].title
        )

    def test_numbered_link(self):
        s = 'text1 [http://mediawiki.org] text2'
        wt = wtp.WikiText(s)
        self.assertEqual(
            '[http://mediawiki.org]',
            wt.get_external_links()[0].string
        )

    def test_protocol_relative(self):
        s = 'text1 [//en.wikipedia.org wikipedia] text2'
        wt = wtp.WikiText(s)
        self.assertEqual(
            '[//en.wikipedia.org wikipedia]',
            wt.get_external_links()[0].string
        )

    def test_mailto(self):
        s = (
            '[mailto:'
            'info@example.org?Subject=URL%20Encoded%20Subject&body=Body%20Text'
            'info]'
        )
        wt = wtp.WikiText(s)
        self.assertEqual(s, wt.get_external_links()[0].string)


class GetSpansFunction(unittest.TestCase):

    """Test _ppft_spans."""

    def test_template_in_template(self):
        wt = wtp.WikiText("""{{cite|{{t1}}|{{t2}}}}""")
        template_spans =  wt._spans[2]
        self.assertIn((7, 13), template_spans)
        self.assertIn((14, 20), template_spans)
        self.assertIn((0, 22), template_spans)

    def test_textmixed_multitemplate(self):
        wt = wtp.WikiText(
            "text1{{cite|{{t1}}|{{t2}}}}"
            "text2{{cite|{{t3}}|{{t4}}}}text3"
        )
        self.assertEqual(
            wt._spans[2],
            [(12, 18), (19, 25), (39, 45), (46, 52), (5, 27), (32, 54)],
        )

    def test_multiline_mutitemplate(self):
        wt = wtp.WikiText("""{{cite\n    |{{t1}}\n    |{{t2}}}}""")
        self.assertEqual(
            wt._spans[2],
            [(12, 18), (24, 30), (0, 32)],
        )

    def test_lacks_ending_braces(self):
        wt = wtp.WikiText("""{{cite|{{t1}}|{{t2}}""")
        self.assertEqual(
            [(7, 13), (14, 20)],
            wt._spans[2],
        )

    def test_lacks_starting_braces(self):
        wt = wtp.WikiText("""cite|{{t1}}|{{t2}}}}""")
        self.assertEqual(
            [(5, 11), (12, 18)],
            wt._spans[2],
        )

    def test_template_inside_parameter(self):
        wt = wtp.WikiText("""{{{1|{{colorbox|yellow|text1}}}}}""")
        self.assertEqual(
            [(5, 30)],
            wt._spans[2],
        )
        self.assertEqual(
            [(0, 33)],
            wt._spans[0],
        )

    def test_parameter_inside_template(self):
        wt = wtp.WikiText("""{{colorbox|yellow|{{{1|defualt_text}}}}}""")
        self.assertEqual(
            [(0, 40)],
            wt._spans[2],
        )
        self.assertEqual(
            [(18, 38)],
            wt._spans[0],
        )

    def test_template_name_cannot_contain_newline(self):
        tl = wtp.WikiText('{{\nColor\nbox\n|mytext}}')
        self.assertEqual(
            [],
            tl._spans[2],
        )

    def test_unicode_template(self):
        wt = wtp.WikiText('{{\nرنگ\n|متن}}')
        self.assertEqual(
            [(0, 13)],
            wt._spans[2],
        )

    def test_unicode_parser_function(self):
        wt = wtp.WikiText('{{#اگر:|فلان}}')
        self.assertEqual(
            [(0, 14)],
            wt._spans[1],
        )

    def test_unicode_parameters(self):
        wt = wtp.WikiText('{{{پارا۱|{{{پارا۲|پيشفرض}}}}}}')
        self.assertEqual(
            [(9, 27), (0, 30)],
            wt._spans[0],
        ) 


class GetSubspans(unittest.TestCase):

    """Test get_subspans() function."""

    def test_1(self):
        wt = wtp.WikiText('text')
        wt._spans = [
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
        ]
        span = [0,6]
        self.assertEqual(
            [
                [(2, 5)],
                [(2, 5)],
                [(2, 5)],
            ],
            wt._get_subspans(span),
        )

    def test_2(self):
        wt = wtp.WikiText('text')
        wt._spans = [
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
        ]
        span = [5,11]
        self.assertEqual(
            [
                [(1, 5)],
                [(1, 5)],
                [(1, 5)],
            ],
            wt._get_subspans(span),
        )
        

if __name__ == '__main__':
    unittest.main()
