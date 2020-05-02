from unittest import TestCase, main

from wikitextparser import WikiList, parse


class WikiListTest(TestCase):
    """Test the WikiList class."""

    def test_subitem_are_part_of_item(self):
        """A few basic examples from [[mw:Help:Lists]]."""
        ae = self.assertEqual
        ul = WikiList(
            '* Lists are easy to do:\n'
            '** start every line\n'
            '* with a star\n'
            '** more stars mean\n'
            '*** deeper levels',
            pattern=r'\*')
        items = ul.items
        ae(items, [' Lists are easy to do:', ' with a star'])
        fullitems = ul.fullitems
        ae(fullitems, [
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
        ae = self.assertEqual
        wl = WikiList(
            '# 0\n'
            '## 0.0\n'
            '## 0.1\n'
            '#* 0.0\n'
            '# 2\n',
            pattern=r'\#')
        items = wl.items[0]
        ae(items, ' 0')
        subitems0 = wl.sublists(0, r'\#')[0]
        ae(subitems0.items, [' 0.0', ' 0.1'])
        # Test to see that arguments are optional.
        sublists = wl.sublists()
        ae(sublists[1].fullitems, ['#* 0.0\n'])
        ae(sublists[0].items, [' 0.0', ' 0.1'])

    def test_subitems_for_the_second_item(self):
        ae = self.assertEqual
        parsed = parse(
            'text\n'
            '* list item a\n'
            '* list item b\n'
            '** sub-list of b\n'
            '* list item c\n'
            'text')
        wikilist = parsed.get_lists(pattern=r'\*')[0]
        ae(
            wikilist.items, [' list item a', ' list item b', ' list item c'])
        sublist = wikilist.sublists(1, r'\*')[0]
        ae(sublist.items, [' sub-list of b'])

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
        ae = self.assertEqual
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
        ae(wl.items, [' Or create mixed lists'])
        swl = wl.sublists(0, r'\#')[0]
        ae(swl.items, [' and nest them'])
        sswl = swl.sublists(0, r'\*')[0]
        ae(sswl.items, [' like this'])
        ssswl = sswl.sublists(0, '[;:]')[0]
        ae(ssswl.items, [
            ' definitions',
            ' work:',
            ' apple',
            ' banana',
            ' fruits'])

    def test_convert(self):
        ae = self.assertEqual
        wl = WikiList(
            ':*A1\n'
            ':*#B1\n'
            ':*#B2\n'
            ':*:continuing A1\n'
            ':*A2',
            pattern=r':\*')
        ae(wl.level, 2)
        wl.convert('#')
        ae(
            wl.string,
            '#A1\n'
            '##B1\n'
            '##B2\n'
            '#:continuing A1\n'
            '#A2')
        ae(wl.pattern, r'\#')
        ae(wl.level, 1)

    def test_cache_update(self):
        wl = WikiList('*a {{t}}', pattern=r'\*')
        wl.templates[0].name = 'ttt'
        self.assertEqual(wl.string, '*a {{ttt}}')


if __name__ == '__main__':
    main()

# todo: check if ref tags can contain lists and add a test for it.
