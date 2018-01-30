"""Test the ExternalLink class."""


import unittest

from wikitextparser import Template


class TemplateTest(unittest.TestCase):

    """Test the Template class."""

    def test_named_parameters(self):
        s = '{{یادکرد کتاب|عنوان = ش{{--}}ش|سال=۱۳۴۵}}'
        t = Template(s)
        self.assertEqual(s, str(t))

    def test_ordered_parameters(self):
        s = '{{example|{{foo}}|bar|2}}'
        t = Template(s)
        self.assertEqual(s, str(t))

    def test_ordered_and_named_parameters(self):
        s = '{{example|para1={{foo}}|bar=3|2}}'
        t = Template(s)
        self.assertEqual(s, str(t))

    def test_no_parameters(self):
        s = '{{template}}'
        t = Template(s)
        self.assertEqual("Template('{{template}}')", repr(t))

    def test_contains_newlines(self):
        s = '{{template\n|s=2}}'
        t = Template(s)
        self.assertEqual(s, str(t))

    def test_name(self):
        s1 = "{{ wrapper | p1 | {{ cite | sp1 | dateformat = ymd}} }}"
        t = Template(s1)
        self.assertEqual(' wrapper ', t.name)

    def test_dont_remove_nonkeyword_argument(self):
        t = Template("{{t|a|a}}")
        self.assertEqual("{{t|a|a}}", str(t))

    def test_set_name(self):
        t = Template("{{t|a|a}}")
        t.name = ' u '
        self.assertEqual("{{ u |a|a}}", t.string)

    def test_normal_name(self):
        t = Template('{{ u |a}}')
        self.assertEqual('u', t.normal_name())
        self.assertEqual('U', t.normal_name(capital_links=True))
        t = Template('{{ template: u |a}}')
        self.assertEqual('u', t.normal_name())
        t = Template('{{ الگو:u |a}}')
        self.assertEqual('u', t.normal_name(['الگو']))
        t = Template('{{a_b}}')
        self.assertEqual('a b', t.normal_name())
        t = Template('{{t#a|a}}')
        self.assertEqual('t', t.normal_name())
        t = Template('{{ : fa : Template : t  # A }}')
        self.assertEqual('t', t.normal_name(code='fa'))
        t = Template('{{ : t |a}}')
        self.assertEqual('t', t.normal_name())
        t = Template('{{A___B}}')
        self.assertEqual('A B', t.normal_name())

    def test_keyword_and_positional_args(self):
        t = Template("{{t|kw=a|1=|pa|kw2=a|pa2}}")
        self.assertEqual('1', t.arguments[2].name)

    def test_rm_first_of_dup_args(self):
        # Remove first of duplicates, keep last
        t = Template('{{template|year=9999|year=2000}}')
        t.rm_first_of_dup_args()
        self.assertEqual('{{template|year=2000}}', str(t))
        # Don't remove duplicate positional args in different positions
        s = """{{cite|{{t1}}|{{t1}}}}"""
        t = Template(s)
        t.rm_first_of_dup_args()
        self.assertEqual(s, str(t))
        # Don't remove duplicate subargs
        s1 = "{{i| c = {{g}} |p={{t|h={{g}}}} |q={{t|h={{g}}}}}}"
        t = Template(s1)
        t.rm_first_of_dup_args()
        self.assertEqual(s1, str(t))
        # test_dont_touch_empty_strings
        s1 = '{{template|url=||work=|accessdate=}}'
        s2 = '{{template|url=||work=|accessdate=}}'
        t = Template(s1)
        t.rm_first_of_dup_args()
        self.assertEqual(s2, str(t))
        # Positional args
        t = Template('{{t|1=v|v}}')
        t.rm_first_of_dup_args()
        self.assertEqual('{{t|v}}', str(t))
        # Triple duplicates:
        t = Template('{{t|1=v|v|1=v}}')
        t.rm_first_of_dup_args()
        self.assertEqual('{{t|1=v}}', str(t))

    def test_rm_dup_args_safe(self):
        # Don't remove duplicate positional args in different positions
        s = "{{cite|{{t1}}|{{t1}}}}"
        t = Template(s)
        t.rm_dup_args_safe()
        self.assertEqual(s, t.string)
        # Don't remove duplicate args if the have different values
        s = '{{template|year=9999|year=2000}}'
        t = Template(s)
        t.rm_dup_args_safe()
        self.assertEqual(s, t.string)
        # Detect positional and keyword duplicates
        t = Template('{{t|1=|}}')
        t.rm_dup_args_safe()
        self.assertEqual('{{t|}}', t.string)
        # Detect same-name same-value.
        # It's OK to ignore whitespace in positional arguments.
        t = Template('{{t|n=v|  n=v  }}')
        t.rm_dup_args_safe()
        self.assertEqual('{{t|  n=v  }}', t.string)
        # It's not OK to ignore whitespace in positional arguments.
        t = Template('{{t| v |1=v}}')
        t.rm_dup_args_safe()
        self.assertEqual('{{t| v |1=v}}', t.string)
        # Removing a positional argument affects the name of later ones.
        t = Template("{{t|1=|||}}")
        t.rm_dup_args_safe()
        self.assertEqual("{{t|||}}", t.string)
        # Triple duplicates
        t = Template('{{t|1=v|v|1=v}}')
        t.rm_dup_args_safe()
        self.assertEqual('{{t|1=v}}', t.string)
        # If the last duplicate has a defferent value, still remove of the
        # first two
        t = Template('{{t|1=v|v|1=u}}')
        t.rm_dup_args_safe()
        self.assertEqual('{{t|v|1=u}}', t.string)
        # tag
        # Remove safe duplicates even if tag option is activated
        t = Template('{{t|1=v|v|1=v}}')
        t.rm_dup_args_safe(tag='<!-- dup -->')
        self.assertEqual('{{t|1=v}}', t.string)
        # Tag even if one of the duplicate values is different.
        t = Template('{{t|1=v|v|1=u}}')
        t.rm_dup_args_safe(tag='<!-- dup -->')
        self.assertEqual('{{t|v<!-- dup -->|1=u}}', t.string)
        # Duplicate argument's value is empty
        t = Template('{{t|b|1=c|1=}}')
        t.rm_dup_args_safe()
        self.assertEqual('{{t|b|1=c}}', t.string)

    def test_has_arg(self):
        t = Template('{{t|a|b=c}}')
        self.assertEqual(True, t.has_arg('1'))
        self.assertEqual(True, t.has_arg('1', 'a'))
        self.assertEqual(True, t.has_arg('b'))
        self.assertEqual(True, t.has_arg('b', 'c'))
        self.assertEqual(False, t.has_arg('2'))
        self.assertEqual(False, t.has_arg('1', 'b'))
        self.assertEqual(False, t.has_arg('c'))
        self.assertEqual(False, t.has_arg('b', 'd'))

    def test_get_arg(self):
        t = Template('{{t|a|b=c}}')
        self.assertEqual('|a', t.get_arg('1').string)
        self.assertEqual(None, t.get_arg('c'))

    def test_name_contains_a_param_with_default(self):
        t = Template('{{t {{{p1|d1}}} | {{{p2|d2}}} }}')
        self.assertEqual('t {{{p1|d1}}} ', t.name)
        self.assertEqual('| {{{p2|d2}}} ', t.arguments[0].string)
        t.name = 'g'
        self.assertEqual('g', t.name)

    def test_overwriting_on_a_string_subspancontaining_string(self):
        t = Template('{{t {{{p1|d1}}} | {{{p2|d2}}} }}')
        t.name += 's'
        self.assertEqual('t {{{p1|d1}}} s', t.name)

    def test_overwriting_on_a_string_causes_loss_of_spans(self):
        t = Template('{{t {{{p1|d1}}} | {{{p2|d2}}} }}')
        p = t.parameters[0]
        t.name += 's'
        self.assertEqual('', p.string)

    def test_no_param_template_name(self):
        t = Template("{{صعود}}")
        self.assertEqual('صعود', t.name)


class SetArg(unittest.TestCase):

    """Test set_arg method of Template class."""

    def test_set_arg(self):
        # Template with no args, keyword
        t = Template('{{t}}')
        t.set_arg('a', 'b')
        self.assertEqual('{{t|a=b}}', t.string)
        # Template with no args, auto positional
        t = Template('{{t}}')
        t.set_arg('1', 'b')
        self.assertEqual('{{t|1=b}}', t.string)
        # Force keyword
        t = Template('{{t}}')
        t.set_arg('1', 'b', positional=False)
        self.assertEqual('{{t|1=b}}', t.string)
        # Arg already exist, positional
        t = Template('{{t|a}}')
        t.set_arg('1', 'b')
        self.assertEqual('{{t|b}}', t.string)
        # Append new keyword when there is more than one arg
        t = Template('{{t|a}}')
        t.set_arg('z', 'z')
        self.assertEqual('{{t|a|z=z}}', t.string)
        # Preserve spacing
        t = Template('{{t\n  | p1   = v1\n  | p22  = v2\n}}')
        t.set_arg('z', 'z')
        self.assertEqual(
            '{{t\n  | p1   = v1\n  | p22  = v2\n  | z    = z\n}}', t.string
        )

    def test_preserve_spacing_with_only_one_arg(self):
        t = Template('{{t\n  |  afadfaf =   value \n}}')
        t.set_arg('z', 'z')
        self.assertEqual(
            '{{t\n  |  afadfaf =   value\n  |  z       =   z\n}}', t.string
        )

    def test_multiline_arg(self):
        t = Template('{{text|\na=\nb\nc\n}}')
        t.set_arg('d', 'e')
        self.assertEqual('{{text|\na=\nb\nc|\nd=\ne\n}}', t.string)
        t = Template('{{text\n\n | a = b\n\n}}')
        t.set_arg('c', 'd')
        self.assertEqual('{{text\n\n | a = b\n\n | c = d\n\n}}', t.string)

    def test_existing_dont_preserve_space(self):
        t = Template('{{t\n  |  a =   v \n}}')
        t.set_arg('a', 'w', preserve_spacing=False)
        self.assertEqual(
            '{{t\n  |  a =w}}', t.string
        )

    def test_new_dont_preserve_space(self):
        t = Template('{{t\n  |  a =   v \n}}')
        t.set_arg('b', 'w', preserve_spacing=False)
        self.assertEqual(
            '{{t\n  |  a =   v \n|b=w}}', t.string
        )

    def test_before(self):
        t = Template('{{t|a|b|c=c|d}}')
        t.set_arg('e', 'e', before='c')
        self.assertEqual('{{t|a|b|e=e|c=c|d}}', t.string)

    def test_after(self):
        t = Template('{{t|a|b|c=c|d}}')
        t.set_arg('e', 'e', after='c')
        self.assertEqual('{{t|a|b|c=c|e=e|d}}', t.string)

    def test_multi_set_positional_args(self):
        t = Template('{{t}}')
        t.set_arg('1', 'p', positional=True)
        t.set_arg('2', 'q', positional=True)
        self.assertEqual('{{t|p|q}}', t.string)

    @unittest.expectedFailure
    def test_invalid_position(self):
        t = Template('{{t}}')
        t.set_arg('2', 'a', positional=True)
        self.assertEqual('{{t|2=a}}', t.string)

    def test_force_new_to_positional_when_old_is_keyword(self):
        t = Template('{{t|1=v}}')
        t.set_arg('1', 'v', positional=True)
        self.assertEqual('{{t|v}}', t.string)

    def test_nowiki_makes_equal_ineffective(self):
        t = Template('{{text|1<nowiki>=</nowiki>g}}')
        a = t.arguments[0]
        self.assertEqual(a.value, '1<nowiki>=</nowiki>g')
        self.assertEqual(a.name, '1')

    def test_not_name_and_positional_is_none(self):
        t = Template('{{t}}')
        t.set_arg(None, 'v')
        self.assertEqual('{{t|v}}', t.string)


if __name__ == '__main__':
    unittest.main()
