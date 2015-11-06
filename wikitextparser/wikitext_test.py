"""Test the functionalities of wikitext.py module."""

import sys
import unittest

sys.path.insert(0, '..')
from wikitextparser import wikitextparser as wtp


class Contains(unittest.TestCase):

    """Test the __contains__ method of the WikiText class."""

    def test_a_is_actually_in_b(self):
        s = '{{b|{{a}}}}'
        a, b = wtp.WikiText(s).templates
        self.assertTrue(a in b)
        self.assertFalse(b in a)

    def test_a_seems_to_be_in_b_but_in_another_span(self):
        s = '{{b|{{a}}}}{{a}}'
        a1, a2, b = wtp.WikiText(s).templates
        self.assertTrue(a1 in b)
        self.assertFalse(a2 in b)
        self.assertFalse(a2 in a1)
        self.assertFalse(a1 in a2)

    def test_a_b_from_different_objects(self):
        s = '{{b|{{a}}}}'
        a1, b1 = wtp.WikiText(s).templates
        a2, b2 = wtp.WikiText(s).templates
        self.assertTrue(a1 in b1)
        self.assertTrue(a2 in b2)
        self.assertFalse(a2 in b1)
        self.assertFalse(a1 in b2)


class ShrinkSpanUpdate(unittest.TestCase):
    
    """Test the _shrink_span_update method."""
    
    def test_stripping_template_name_should_update_its_arg_spans(self):
        t = wtp.Template('{{ t\n |1=2}}')
        a = t.arguments[0]
        t.name = t.name.strip()
        self.assertEqual('|1=2', a.string)
        
    def test_opcodes_in_spans_should_be_referenced_based_on_self_lststr0(self):
        wt = wtp.WikiText('{{a}}{{ b\n|d=}}')
        template = wt.templates[1]
        arg = template.arguments[0]
        template.name = template.name.strip()
        self.assertEqual('|d=', arg.string)
        

class ExpandSpanUpdate(unittest.TestCase):
    
    """Test the _expand_span_update method."""
    
    def test_extending_template_name_should_not_effect_arg_string(self):
        t = wtp.Template('{{t|1=2}}')
        a = t.arguments[0]
        t.name = 't\n    '
        self.assertEqual('|1=2', a.string)
        
    def test_extend_selfspan_when_inserting_at_the_end_of_selfspan(self):
        wt = wtp.WikiText('{{ t|a={{#if:c|a}}|b=}}\n')
        a = wt.templates[0].arguments[0]
        pf = wt.parser_functions[0]
        a.value = a.value + '    \n'
        self.assertEqual('|a={{#if:c|a}}    \n', a.string)
        self.assertEqual('{{#if:c|a}}', pf.string)
        

class IndentLevel(unittest.TestCase):

    """Test the _get_indent_level method of the WikiText class."""

    def test_a_in_b(self):
        s = '{{b|{{a}}}}'
        a, b = wtp.WikiText(s).templates
        self.assertEqual(1, b._get_indent_level())
        self.assertEqual(2, a._get_indent_level())

    def test_with_respect_to(self):
        s = '{{c {{b|{{a}}}} }}'
        a, b, c = wtp.WikiText(s).templates
        self.assertEqual(3, a._get_indent_level())
        self.assertEqual(2, a._get_indent_level(with_respect_to=b))
        s = '{{#if: {{c {{b|{{a}}}} }} | ifyes }}'
        a, b, c = wtp.WikiText(s).templates
        self.assertEqual(4, a._get_indent_level())
        self.assertEqual(2, a._get_indent_level(with_respect_to=b))


class StringSetter(unittest.TestCase):

    """Test the string setter method."""

    def test_sequencematcher(self):
        t = wtp.Template('{{t|a|b|c}}')
        t.string = '{{t|0|a|b|c}}'
        self.assertEqual('0', t.get_arg('1').value)
        self.assertEqual('c', t.get_arg('4').value)


if __name__ == '__main__':
    unittest.main()
