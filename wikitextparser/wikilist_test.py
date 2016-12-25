import unittest

import wikitextparser as wtp


class WikiListTest(unittest.TestCase):
    """Test the WikiList class."""

    def test_subitem_are_part_of_item(self):
        """A few basic examples from [[mw:Help:Lists]]."""
        ul = wtp.WikiList(
            '* Lists are easy to do:\n'
            '** start every line\n'
            '* with a star\n'
            '** more stars mean\n'
            '*** deeper levels',
            pattern='\*'
        )
        items = ul.items
        self.assertEqual(items, [' Lists are easy to do:', ' with a star'])
        fullitems = ul.fullitems
        self.assertEqual(
            fullitems,
            [
                '* Lists are easy to do:\n** start every line\n',
                '* with a star\n** more stars mean\n*** deeper levels',
            ],
        )

    def test_commented_list_item(self):
        """One of the list items is commented through the wikitext."""
        wl = wtp.WikiList(
            '#1\n'
            '##1-1\n'
            '##1-2<!-- \n'
            '##1-3\n'
            ' -->\n'
            '#2\n',
            pattern='\#'
        )
        self.assertEqual(wl.items[1], '2')

    def test_dont_return_shadow(self):
        wl = wtp.WikiList(
            '#1 {{t}}',
            pattern='\#'
        )
        self.assertEqual(wl.items[0], '1 {{t}}')

    def test_subitems_for_an_item(self):
        wl = wtp.WikiList(
            '# 0\n'
            '## 0.0\n'
            '## 0.1\n'
            '#* 0.0\n'
            '# 2\n',
            pattern='\#'
        )
        items = wl.items[0]
        self.assertEqual(items, ' 0')
        subitems0 = wl.sublists(0, '\#')[0]
        self.assertEqual(subitems0.items, [' 0.0', ' 0.1'])

    def test_mixed_definition_lists(self):
        wl = wtp.WikiList(
            '; Mixed definition lists\n'
            '; item 1 : definition\n'
            ':; sub-item 1 plus term\n'
            ':: two colons plus definition\n'
            ':; sub-item 2 : colon plus definition\n'
            '; item 2 \n'
            ': back to the main list\n',
            pattern='[:;]\s*'
        )
        self.assertEqual(
            wl.items,
            [
                'Mixed definition lists',
                'item 1 : definition',
                'item 2 ',
                'back to the main list',
            ]
        )


if __name__ == '__main__':
    unittest.main()
