"""Test the section.py module."""


import unittest

import wikitextparser as wtp


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

    def test_set_level(self):
        s = wtp.Section('=== t ===\ntext')
        s.level = 2
        self.assertEqual('== t ==\ntext', s.string)

    def test_template_at_the_start(self):
        ts = wtp.Section('{{t}}').templates
        self.assertEqual(ts[0].string, '{{t}}')


if __name__ == '__main__':
    unittest.main()
