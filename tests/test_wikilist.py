import unittest

from wikitextparser import WikiList, parse


class WikiListTest(unittest.TestCase):
    """Test the WikiList class."""

    def test_subitem_are_part_of_item(self):
        """A few basic examples from [[mw:Help:Lists]]."""
        ul = WikiList(
            '* Lists are easy to do:\n'
            '** start every line\n'
            '* with a star\n'
            '** more stars mean\n'
            '*** deeper levels',
            pattern=r'\*')
        items = ul.items
        self.assertEqual(items, [' Lists are easy to do:', ' with a star'])
        fullitems = ul.fullitems
        self.assertEqual(
            fullitems, [
                '* Lists are easy to do:\n** start every line\n',
                '* with a star\n** more stars mean\n*** deeper levels'])

    def test_commented_list_item(self):
        """One of the list items is commented through the wikitext."""
        wl = WikiList(
            '#1\n'
            '##1-1\n'
            '##1-2<!-- \n'
            '##1-3\n'
            ' -->\n'
            '#2\n',
            pattern=r'\#')
        self.assertEqual(wl.items[1], '2')

    def test_dont_return_shadow(self):
        wl = WikiList(
            '#1 {{t}}',
            pattern=r'\#')
        self.assertEqual(wl.items[0], '1 {{t}}')

    def test_subitems_for_the_first_item(self):
        wl = WikiList(
            '# 0\n'
            '## 0.0\n'
            '## 0.1\n'
            '#* 0.0\n'
            '# 2\n',
            pattern=r'\#')
        items = wl.items[0]
        self.assertEqual(items, ' 0')
        subitems0 = wl.sublists(0, r'\#')[0]
        self.assertEqual(subitems0.items, [' 0.0', ' 0.1'])
        # Test to see that arguments are optional.
        sublists = wl.sublists()
        self.assertEqual(sublists[1].fullitems, ['#* 0.0\n'])
        self.assertEqual(sublists[0].items, [' 0.0', ' 0.1'])

    def test_subitems_for_the_second_item(self):
        parsed = parse(
            'text\n'
            '* list item a\n'
            '* list item b\n'
            '** sub-list of b\n'
            '* list item c\n'
            'text')
        wikilist = parsed.lists(pattern=r'\*')[0]
        self.assertEqual(
            wikilist.items, [' list item a', ' list item b', ' list item c'])
        sublist = wikilist.sublists(1, r'\*')[0]
        self.assertEqual(sublist.items, [' sub-list of b'])

    def test_mixed_definition_lists(self):
        wl = WikiList(
            '; Mixed definition lists\n'
            '; item 1 : definition\n'
            ':; sub-item 1 plus term\n'
            ':: two colons plus definition\n'
            ':; sub-item 2 : colon plus definition\n'
            '; item 2 \n'
            ': back to the main list\n',
            pattern=r'[:;]\s*')
        self.assertEqual(
            wl.items, [
                'Mixed definition lists',
                'item 1 ',
                ' definition',
                'item 2 ',
                'back to the main list'])

    def test_travese_mixed_list_completely(self):
        wl = WikiList(
            '* Or create mixed lists\n'
            '*# and nest them\n'
            '*#* like this\n'
            '*#*; definitions\n'
            '*#*: work:\n'
            '*#*; apple\n'
            '*#*; banana\n'
            '*#*: fruits',
            pattern=r'\*')
        self.assertEqual(wl.items, [' Or create mixed lists'])
        swl = wl.sublists(0, r'\#')[0]
        self.assertEqual(swl.items, [' and nest them'])
        sswl = swl.sublists(0, r'\*')[0]
        self.assertEqual(sswl.items, [' like this'])
        ssswl = sswl.sublists(0, '[;:]')[0]
        self.assertEqual(ssswl.items, [
            ' definitions',
            ' work:',
            ' apple',
            ' banana',
            ' fruits'])

    def test_convert(self):
        wl = WikiList(
            ':*A1\n'
            ':*#B1\n'
            ':*#B2\n'
            ':*:continuing A1\n'
            ':*A2',
            pattern=r':\*')
        self.assertEqual(wl.level, 2)
        wl.convert('#')
        self.assertEqual(
            wl.string,
            '#A1\n'
            '##B1\n'
            '##B2\n'
            '#:continuing A1\n'
            '#A2')
        self.assertEqual(wl.pattern, r'\#')
        self.assertEqual(wl.level, 1)

    def test_cache_update(self):
        wl = WikiList('*a {{t}}', pattern=r'\*')
        wl.templates[0].name = 'ttt'
        self.assertEqual(wl.string, '*a {{ttt}}')


if __name__ == '__main__':
    unittest.main()
