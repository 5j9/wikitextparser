import sys
import unittest

sys.path.insert(0, '..')
from wikitextparser import wikitextparser as wtp

"""Test the Argument class."""


class Argument(unittest.TestCase):

    """Argument test class."""

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
        

if __name__ == '__main__':
    unittest.main()
