import unittest
import wikitextparser as wtp


class Template(unittest.TestCase):

    """Test Tempate class in wtp.py."""

    def test_named_parameters(self):
        s = '{{یادکرد کتاب|عنوان = ش{{--}}ش|سال=۱۳۴۵}}'
        t = wtp.Template(s)
        self.assertEqual(str(t), s)

    def test_ordered_parameters(self):
        s = '{{example|{{foo}}|bar|2}}'
        t = wtp.Template(s)
        self.assertEqual(str(t), s)

    def test_ordered_and_named_parameters(self):
        s = '{{example|para1={{foo}}|bar=3|2}}'
        t = wtp.Template(s)
        self.assertEqual(str(t), s)

    def test_no_parameters(self):
        s = '{{template}}'
        t = wtp.Template(s)
        self.assertEqual(str(t), s)

    def test_contains_newlines(self):
        s = '{{template\n|s=2}}'
        t = wtp.Template(s)
        self.assertEqual(t.string, s)

    def test_dont_touch_empty_strings(self):
        s1 = '{{template|url=||work=|accessdate=}}'
        s2 = '{{template|url=||work=|accessdate=}}'
        t = wtp.Template(s1)
        self.assertEqual(t.string, s2)

    def test_remove_first_duplicate_keep_last(self):
        s1 = '{{template|year=9999|year=2000}}'
        s2 = '{{template|year=2000}}'
        t = wtp.Template(s1)
        self.assertEqual(t.string, s2)

    def test_duplicate_replace(self):
        s1 = """{{cite|{{t1}}|{{t1}}}}"""
        t = wtp.Template(s1)
        self.assertEqual(t.string, s1)

    def test_name(self):
        s1 = "{{ wrapper | p1 | {{ cite | sp1 | dateformat = ymd}} }}"
        t = wtp.Template(s1)
        self.assertEqual(t.name, ' wrapper ')

    def test_dont_remove_duplicate_subparameter(self):
        s1 = "{{i| c = {{g}} |p={{t|h={{g}}}} |q={{t|h={{g}}}}}}"
        t = wtp.Template(s1)
        self.assertEqual(s1, t.string)


class GetSpansFunction(unittest.TestCase):

    """Test _ppft_spans."""

    def test_template_in_template(self):
        wt = wtp.WikiText("""{{cite|{{t1}}|{{t2}}}}""")
        (
            parameter_spans,
            parser_function_spans,
            template_spans,
        ) = wt._ppft_spans
        self.assertIn((7, 13), template_spans)
        self.assertIn((14, 20), template_spans)
        self.assertIn((0, 22), template_spans)

    def test_textmixed_multitemplate(self):
        wt = wtp.WikiText(
            "text1{{cite|{{t1}}|{{t2}}}}"
            "text2{{cite|{{t3}}|{{t4}}}}text3"
        )
        (
            parameter_spans,
            parser_function_spans,
            template_spans,
        ) = wt._ppft_spans
        self.assertEqual(
            template_spans,
            [(12, 18), (19, 25), (39, 45), (46, 52), (5, 27), (32, 54)],
        )

    def test_multiline_mutitemplate(self):
        wt = wtp.WikiText("""{{cite\n    |{{t1}}\n    |{{t2}}}}""")
        (
            parameter_spans,
            parser_function_spans,
            template_spans,
        ) = wt._ppft_spans
        self.assertEqual(
            template_spans,
            [(12, 18), (24, 30), (0, 32)],
        )

    def test_lacks_ending_braces(self):
        wt = wtp.WikiText("""{{cite|{{t1}}|{{t2}}""")
        (
            parameter_spans,
            parser_function_spans,
            template_spans,
        ) = wt._ppft_spans
        
        self.assertEqual(
            [(7, 13), (14, 20)],
            template_spans,
        )

    def test_lacks_starting_braces(self):
        string = """cite|{{t1}}|{{t2}}}}"""
        wt = wtp.WikiText(string)
        (
            parameter_spans,
            parser_function_spans,
            template_spans,
        ) = wt._ppft_spans
        self.assertEqual(
            template_spans,
            [(5, 11), (12, 18)],
        )

    def test_template_inside_parameter(self):
        string = """{{{1|{{colorbox|yellow|text1}}}}}"""
        wt = wtp.WikiText(string)
        (
            parameter_spans,
            parser_function_spans,
            template_spans,
        ) = wt._ppft_spans
        
        self.assertEqual(
            template_spans,
            [(5, 30)],
        )
        self.assertEqual(
            parameter_spans,
            [(0, 33)],
        )

    def test_parameter_inside_template(self):
        string = """{{colorbox|yellow|{{{1|defualt_text}}}}}"""
        wt = wtp.WikiText(string)
        (
            parameter_spans,
            parser_function_spans,
            template_spans,
        ) = wt._ppft_spans
        
        self.assertEqual(
            template_spans,
            [(0, 40)],
        )
        self.assertEqual(
            parameter_spans,
            [(18, 38)],
        )

    def test_template_name_cannot_contain_newline(self):
        tl = wtp.WikiText('{{\nColor\nbox\n|mytext}}')
        (
            parameter_spans,
            parser_function_spans,
            template_spans,
        ) = tl._ppft_spans
        
        self.assertEqual(
            template_spans,
            [],
        )

    def test_unicode_template(self):
        wt = wtp.WikiText('{{\nرنگ\n|متن}}')
        (
            parameter_spans,
            parser_function_spans,
            template_spans,
        ) = wt._ppft_spans
        
        self.assertEqual(
            template_spans,
            [(0, 13)],
        )

    def test_unicode_parser_function(self):
        string = '{{#اگر:|فلان}}'
        wt = wtp.WikiText(string)
        (
            parameter_spans,
            parser_function_spans,
            template_spans,
        ) = wt._ppft_spans
        
        self.assertEqual(
            parser_function_spans,
            [(0, 14)],
        )

    def test_unicode_parameters(self):
        wt = wtp.WikiText('{{{پارا۱|{{{پارا۲|پيشفرض}}}}}}')
        (
            parameter_spans,
            parser_function_spans,
            template_spans,
        ) = wt._ppft_spans
        
        self.assertEqual(
            parameter_spans,
            [(9, 27), (0, 30)],
        ) 


class GetSubspans(unittest.TestCase):

    """Test get_subspans() function."""

    def test_1(self):
        wt = wtp.WikiText('text')
        wt._ppft_spans = [
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
        ]
        span = [0,6]
        self.assertEqual(
            wt._get_subspans(span),
            [
                [(2, 5)],
                [(2, 5)],
                [(2, 5)]
            ],
        )

    def test_2(self):
        wt = wtp.WikiText('text')
        wt._ppft_spans = [
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
            [(2, 5), (6, 10), (0, 20), (22, 24), (26, 28)],
        ]
        span = [5,11]
        self.assertEqual(
            wt._get_subspans(span),
            [
                [(1, 5)],
                [(1, 5)],
                [(1, 5)]
            ],
        )
        

if __name__ == '__main__':
    unittest.main()
