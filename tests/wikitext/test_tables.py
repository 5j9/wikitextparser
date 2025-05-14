from operator import attrgetter

from wikitextparser import parse

# noinspection PyProtectedMember
from wikitextparser._wikitext import WS


def test_table_extraction():
    s = '{|class=wikitable\n|a \n|}'
    p = parse(s)
    assert s == p.tables[0].string


def test_table_start_after_space():
    s = '   {|class=wikitable\n|a \n|}'
    p = parse(s)
    assert s.strip(WS) == p.tables[0].string


def test_ignore_comments_before_extracting_tables():
    s = '{|class=wikitable\n|a \n<!-- \n|} \n-->\n|b\n|}'
    p = parse(s)
    assert s == p.tables[0].string


def test_two_tables():
    s = 'text1\n {|\n|a \n|}\ntext2\n{|\n|b\n|}\ntext3\n'
    p = parse(s)
    tables = p.tables
    assert 2 == len(tables)
    assert '{|\n|a \n|}' == tables[0].string
    assert '{|\n|b\n|}' == tables[1].string


def test_nested_tables():
    s = 'text1\n{|class=wikitable\n|a\n|\n{|class=wikitable\n|b\n|}\n|}\ntext2'
    p = parse(s)
    assert 1 == len(p.get_tables())  # non-recursive
    tables = p.tables  # recursive
    assert 2 == len(tables)
    table0 = tables[0]
    assert s[6:-6] == table0.string
    assert 0 == table0.nesting_level
    table1 = tables[1]
    assert '{|class=wikitable\n|b\n|}' == table1.string
    assert 1 == table1.nesting_level


def test_tables_in_different_sections():
    s = '{|\n| a\n|}\n\n= s =\n{|\n| b\n|}\n'
    p = parse(s).sections[1]
    assert '{|\n| b\n|}' == p.tables[0].string


def test_match_index_is_none():
    wt = parse('{|\n| b\n|}\n')
    assert len(wt.tables) == 1
    wt.insert(0, '{|\n| a\n|}\n')
    tables = wt.tables
    assert tables[0].string == '{|\n| a\n|}'
    assert tables[1].string == '{|\n| b\n|}'


def test_tables_may_be_indented():
    s = ' ::{|class=wikitable\n|a\n|}'
    wt = parse(s)
    assert wt.tables[0].string == '{|class=wikitable\n|a\n|}'


def test_comments_before_table_start():
    s = ' <!-- c -->::{|class=wikitable\n|a\n|}'
    wt = parse(s)
    assert wt.tables[0].string == '{|class=wikitable\n|a\n|}'


def test_comments_between_indentation():
    s = ':<!-- c -->:{|class=wikitable\n|a\n|}'
    wt = parse(s)
    assert wt.tables[0].string == '{|class=wikitable\n|a\n|}'


def test_comments_between_indentation_after_them():
    assert (
        parse(':<!-- c -->: <!-- c -->{|class=wikitable\n|a\n|}')
        .tables[0]
        .string
        == '{|class=wikitable\n|a\n|}'
    )


def test_indentation_cannot_be_inside_nowiki():
    """A very unusual case. It would be OK to have false positives here.

    Also false positive for tables are pretty much harmless here.

    The same thing may happen for tables which start right after a
    templates, parser functions, wiki links, comments, or
    other extension tags.

    """
    assert (
        len(parse('<nowiki>:</nowiki>{|class=wikitable\n|a\n|}').tables) == 0
    )


def test_template_before_or_after_table():
    # This tests self._shadow function.
    s = '{{t|1}}\n{|class=wikitable\n|a\n|}\n{{t|1}}'
    p = parse(s)
    assert [['a']] == p.tables[0].data()


def test_nested_tables_sorted():
    s = (
        '{| style="border: 1px solid black;"\n'
        '| style="border: 1px solid black;" | 0\n'
        '| style="border: 1px solid black; text-align:center;" | 1\n'
        '{| style="border: 2px solid black; background: green;" '
        '<!-- The nested table must be on a new line -->\n'
        '| style="border: 2px solid darkgray;" | 1_G00\n'
        '|-\n'
        '| style="border: 2px solid darkgray;" | 1_G10\n'
        '|}\n'
        '| style="border: 1px solid black; vertical-align: bottom;" '
        '| 2\n'
        '| style="border: 1px solid black; width:100px" |\n'
        '{| style="border: 2px solid black; background: yellow"\n'
        '| style="border: 2px solid darkgray;" | 3_Y00\n'
        '|}\n'
        '{| style="border: 2px solid black; background: Orchid"\n'
        '| style="border: 2px solid darkgray;" | 3_O00\n'
        '| style="border: 2px solid darkgray;" | 3_O01\n'
        '|}\n'
        '| style="border: 1px solid black; width: 50px" |\n'
        '{| style="border: 2px solid black; background:blue; float:left"\n'
        '| style="border: 2px solid darkgray;" | 4_B00\n'
        '|}\n'
        '{| style="border: 2px solid black; background:red; float:right"\n'
        '| style="border: 2px solid darkgray;" | 4_R00\n'
        '|}\n'
        '|}'
    )
    p = parse(s)
    assert 1 == len(p.get_tables())  # non-recursive
    tables = p.tables
    assert tables == sorted(tables, key=attrgetter('_span_data'))
    t0 = tables[0]
    assert s == t0.string
    assert t0.data(strip=False) == [
        [
            ' 0',
            ' 1\n'
            '{| style="border: 2px solid black; background: green;" '
            '<!-- The nested table must be on a new line -->\n'
            '| style="border: 2px solid darkgray;" | 1_G00\n|-\n'
            '| style="border: 2px solid darkgray;" | 1_G10\n'
            '|}',
            ' 2',
            '\n{| style="border: 2px solid black; background: yellow"\n'
            '| style="border: 2px solid darkgray;" | 3_Y00\n|}\n'
            '{| style="border: 2px solid black; background: Orchid"\n'
            '| style="border: 2px solid darkgray;" | 3_O00\n'
            '| style="border: 2px solid darkgray;" | 3_O01\n|}',
            '\n{| style="border: 2px solid black; background:blue; float:left"'
            '\n| style="border: 2px solid darkgray;" | 4_B00\n|}\n'
            '{| style="border: 2px solid black; background:red; float:right"\n'
            '| style="border: 2px solid darkgray;" | 4_R00\n|}',
        ]
    ]
    assert tables[3].data() == [['3_O00', '3_O01']]
    assert 5 == len(tables[0].tables)
    # noinspection PyProtectedMember
    dynamic_spans = p._type_to_spans['Table']
    assert len(dynamic_spans) == 6
    pre_insert_spans = dynamic_spans[:]
    p.insert(0, '{|\na\n|}\n')
    assert len(dynamic_spans) == 6
    assert 2 == len(p.get_tables())  # non-recursive for the second time
    assert len(dynamic_spans) == 7
    for os, ns in zip(dynamic_spans[1:], pre_insert_spans):
        assert os is ns


def test_tables_in_parsable_tag_extensions():  # 85
    (table,) = parse('<onlyinclude>\n{|\n|}\n</onlyinclude>').tables
    assert table.span == (14, 19)


def test_table_with_no_end_mark():  # 124
    text = """
    {| class=wikitable
    ! a !! b
    {{end}}
    """
    parsed = parse(text)
    assert parsed.tables[0].data() == [['a', 'b\n    {{end}}']]


def test_test_table_with_no_end_mark2():  # 125
    print(parse('{| class=wikitable\n! a !! b\n|-\n').tables[0].data())
