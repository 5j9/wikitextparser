from pytest import warns

from wikitextparser import WikiList, parse


def test_lists():
    assert repr(WikiList('# a\n## b', '#').get_lists()) == "[WikiList('## b')]"
    with warns(DeprecationWarning):
        # noinspection PyDeprecation
        assert repr(WikiList('# a\n## b', '#').lists()) == "[WikiList('## b')]"


def test_subitem_are_part_of_item():
    """A few basic examples from [[mw:Help:Lists]]."""
    ul = WikiList(
        '* Lists are easy to do:\n'
        '** start every line\n'
        '* with a star\n'
        '** more stars mean\n'
        '*** deeper levels',
        pattern=r'\*')
    items = ul.items
    assert items == [' Lists are easy to do:', ' with a star']
    fullitems = ul.fullitems
    assert fullitems == [
        '* Lists are easy to do:\n** start every line\n',
        '* with a star\n** more stars mean\n*** deeper levels']


def test_commented_list_item():
    """One of the list items is commented through the wikitext."""
    wl = WikiList(
        '#1\n'
        '##1-1\n'
        '##1-2<!-- \n'
        '##1-3\n'
        ' -->\n'
        '#2\n',
        pattern=r'\#')
    assert wl.items[1] == '2'


def test_dont_return_shadow():
    wl = WikiList(
        '#1 {{t}}',
        pattern=r'\#')
    assert wl.items[0] == '1 {{t}}'


def test_subitems_for_the_first_item():
    wl = WikiList(
        '# 0\n'
        '## 0.0\n'
        '## 0.1\n'
        '#* 0.0\n'
        '# 2\n',
        pattern=r'\#')
    items = wl.items[0]
    assert items == ' 0'
    subitems0 = wl.sublists(0, r'\#')[0]
    assert subitems0.items == [' 0.0', ' 0.1']
    # Test to see that arguments are optional.
    sublists = wl.sublists()
    assert sublists[1].fullitems == ['#* 0.0\n']
    assert sublists[0].items == [' 0.0', ' 0.1']


def test_subitems_for_the_second_item():
    parsed = parse(
        'text\n'
        '* list item a\n'
        '* list item b\n'
        '** sub-list of b\n'
        '* list item c\n'
        'text')
    wikilist = parsed.get_lists(pattern=r'\*')[0]
    assert wikilist.items == [' list item a', ' list item b', ' list item c']
    sublist = wikilist.sublists(1, r'\*')[0]
    assert sublist.items == [' sub-list of b']


def test_link_in_definition_list():
    wl = WikiList("; https://github.com : definition", pattern=r'[:;]\s*')
    assert wl.items == ["https://github.com ", " definition"]
    wl = WikiList("; https://a.b : c https://d.e : f", pattern=r'[:;]\s*')
    assert wl.items == ["https://a.b ", " c https://d.e : f"]


def test_mixed_definition_lists():
    wl = WikiList(
        '; Mixed definition lists\n'
        '; item 1 : definition\n'
        ':; sub-item 1 plus term\n'
        ':: two colons plus definition\n'
        ':; sub-item 2 : colon plus definition\n'
        '; item 2 \n'
        ': back to the main list\n',
        pattern=r'[:;]\s*')
    assert wl.items == [
            'Mixed definition lists',
            'item 1 ',
            ' definition',
            'item 2 ',
            'back to the main list']


def test_travese_mixed_list_completely():
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
    assert wl.items == [' Or create mixed lists']
    swl = wl.sublists(0, r'\#')[0]
    assert swl.items == [' and nest them']
    sswl = swl.sublists(0, r'\*')[0]
    assert sswl.items == [' like this']
    ssswl = sswl.sublists(0, '[;:]')[0]
    assert ssswl.items == [
        ' definitions',
        ' work:',
        ' apple',
        ' banana',
        ' fruits']


def test_convert():
    wl = WikiList(
        ':*A1\n'
        ':*#B1\n'
        ':*#B2\n'
        ':*:continuing A1\n'
        ':*A2',
        pattern=r':\*')
    assert wl.level == 2
    wl.convert('#')
    assert wl.string == (
        '#A1\n'
        '##B1\n'
        '##B2\n'
        '#:continuing A1\n'
        '#A2')
    assert wl.pattern == r'\#'
    assert wl.level == 1


def test_cache_update():
    wl = WikiList('*a {{t}}', pattern=r'\*')
    wl.templates[0].name = 'ttt'
    assert wl.string == '*a {{ttt}}'

# todo: check if ref tags can contain lists and add a test for it.
