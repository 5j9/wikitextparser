"""Test the section.py module."""


from unittest import TestCase, main, expectedFailure

from wikitextparser import Section


class TestSection(TestCase):

    """Test the Section class."""

    def test_level6(self):
        s = Section('====== == ======\n')
        self.assertEqual(6, s.level)
        self.assertEqual(' == ', s.title)

    def test_nolevel7(self):
        s = Section('======= h6 =======\n')
        self.assertEqual(6, s.level)
        self.assertEqual('= h6 =', s.title)

    def test_unbalanced_equalsigns_in_title(self):
        s = Section('====== ==   \n')
        self.assertEqual(2, s.level)
        self.assertEqual('==== ', s.title)

        s = Section('== ======   \n')
        self.assertEqual(2, s.level)
        self.assertEqual(' ====', s.title)

        s = Section('========  \n')
        self.assertEqual(3, s.level)
        self.assertEqual('==', s.title)

    def test_leadsection(self):
        s = Section('lead text. \n== section ==\ntext.')
        self.assertEqual(0, s.level)
        self.assertEqual('', s.title)

    def test_set_title(self):
        s = Section('== section ==\ntext.')
        s.title = ' newtitle '
        self.assertEqual(' newtitle ', s.title)

    @expectedFailure
    def test_lead_set_title(self):
        s = Section('lead text')
        s.title = ' newtitle '

    def test_set_contents(self):
        s = Section('== title ==\ntext.')
        s.contents = ' newcontents '
        self.assertEqual(' newcontents ', s.contents)

    def test_set_lead_contents(self):
        s = Section('lead')
        s.contents = 'newlead'
        self.assertEqual('newlead', s.string)

    def test_set_level(self):
        s = Section('=== t ===\ntext')
        s.level = 2
        self.assertEqual('== t ==\ntext', s.string)

    def test_template_at_the_start(self):
        ts = Section('{{t}}').templates
        self.assertEqual(ts[0].string, '{{t}}')

    def test_section_heading_tabs(self):
        s = Section('=\tt\t=\t')
        self.assertEqual(s.string, '=\tt\t=\t')
        self.assertEqual(s.title, '\tt\t')
        self.assertEqual(s.contents, '')

    def test_trailing_space_setter(self):
        s = Section('=t= \no')
        s.contents = 'n'
        self.assertEqual('=t= \nn', s.string)

    def test_setting_lead_section_contents(self):
        s = Section('a\nb')
        s.contents = 'c'
        self.assertEqual('c', s.string)

    def test_level_setter_does_not_overwrite_title(self):
        ae = self.assertEqual
        s = Section('={{t}}=\nb')
        t = s.templates[0]
        s.level = 1  # testing for no effect
        s.level = 2
        ae('=={{t}}==\nb', s.string)
        ae('{{t}}', t.string)


if __name__ == '__main__':
    main()
