from wikitextparser import Table, WikiText


# Todo: addrow, addcol, shiftrow, shiftcol, ...
# addrow([], -1)
# addcol([], -1)
#
# shiftrow(n,m)
# shiftcol(n,m)
#
# sort?
# transpose?


# Table.data

def test_each_row_on_a_newline():
    assert Table(
        '{|\n'
        '|Orange\n'
        '|Apple\n'
        '|-\n'
        '|Bread\n'
        '|Pie\n'
        '|-\n'
        '|Butter\n'
        '|Ice cream \n'
        '|}').data() == [
        ['Orange', 'Apple'], ['Bread', 'Pie'], ['Butter', 'Ice cream']]


def test_with_optional_rowseprator_on_first_row():
    assert Table(
        '{| class=wikitable | g\n'
        ' |- 132131 |||\n'
        '  | a | b\n'
        ' |-\n'
        '  | c\n'
        '|}').data() == [['b'], ['c']]


def test_all_rows_are_on_a_single_line():
    assert Table(
        '{|\n'
        '|a||b||c\n'
        '|-\n'
        '|d||e||f\n'
        '|-\n'
        '|g||h||i\n'
        '|}').data() == [['a', 'b', 'c'], ['d', 'e', 'f'], ['g', 'h', 'i']]


def test_extra_spaces_have_no_effect():
    assert Table(
        '{|\n|  Orange    ||   Apple   ||   more\n|-\n'
        '|   Bread    ||   Pie     ||   more\n|-\n'
        '|   Butter   || Ice cream ||  and more\n|}').data() == [
        ['Orange', 'Apple', 'more'],
        ['Bread', 'Pie', 'more'],
        ['Butter', 'Ice cream', 'and more']]


def test_longer_text_and_only_rstrip():
    assert Table(
            '{|\n|multi\nline\ntext. \n\n2nd paragraph. \n|'
            '\n* ulli1\n* ulli2\n* ulli3\n|}'
        ).data() == [
            ['multi\nline\ntext. \n\n2nd paragraph.',
             '\n* ulli1\n* ulli2\n* ulli3']]


def test_strip_is_false():
    assert Table(
        '{|class=wikitable\n| a || b \n|}'
    ).data(strip=False) == [[' a ', ' b ']]


def test_doublepipe_multiline():
    assert Table(
        '{|\n|| multi\nline\n||\n 1\n|}'
    ).data() == [['multi\nline', '\n 1']]


def test_with_headers():
    assert Table(
        '{|\n! style="text-align:left;"| Item\n! Amount\n! Cost\n|-\n'
        '|Orange\n|10\n|7.00\n|-\n|Bread\n|4\n|3.00\n|-\n'
        '|Butter\n|1\n|5.00\n|-\n!Total\n|\n|15.00\n|}').data() == [
        ['Item', 'Amount', 'Cost'],
        ['Orange', '10', '7.00'],
        ['Bread', '4', '3.00'],
        ['Butter', '1', '5.00'],
        ['Total', '', '15.00']]


def test_with_caption():
    assert Table(
        '{|\n|+Food complements\n|-\n|Orange\n|Apple\n|-\n'
        '|Bread\n|Pie\n|-\n|Butter\n|Ice cream \n|}').data() == [
        ['Orange', 'Apple'], ['Bread', 'Pie'], ['Butter', 'Ice cream']]


def test_with_caption_attrs():
    assert Table(
        '{|class=wikitable\n'
        '|+ sal | no\n'
        '|a \n'
        '|}'
    ).data() == [['a']]


def test_second_caption_is_ignored():
    assert Table(
        '{|\n'
        '  |+ c1\n'
        '  |+ c2\n'
        '|-\n'
        '|1\n'
        '|2\n'
        '|}').data() == [['1', '2']]


def test_unneeded_newline_after_table_start():
    assert Table('{|\n\n|-\n|c1\n|c2\n|}').data() == [['c1', 'c2']]


def test_text_after_tablestart_is_not_actually_inside_the_table():
    assert Table(
        '{|\n'
        '  text\n'
        '|-\n'
        '|c1\n'
        '|c2\n'
        '|}').data() == [['c1', 'c2']]


def test_empty_table():
    assert Table('{|class=wikitable\n|}').data() == []


def test_empty_table_comment_end():
    assert Table(
        '{|class=wikitable\n'
        '<!-- c -->|}').data() == []


def test_empty_table_semi_caption_comment():
    assert Table('{|class=wikitable\n|+\n<!-- c -->|}').data() == []


def test_empty_cell():
    assert Table(
        '{|class=wikitable\n||a || || c\n|}').data() == [['a', '', 'c']]


def test_pipe_as_text():
    assert Table(
        '{|class=wikitable\n||a | || c\n|}').data() == [['a |', 'c']]


def test_meaningless_rowsep():
    assert Table(
        '{|class=wikitable\n'
        '||a || || c\n'
        '|-\n'
        '|}').data() == [['a', '', 'c']]


def test_template_inside_table():
    assert Table('{|class=wikitable\n|-\n|{{text|a}}\n|}').data() ==\
           [['{{text|a}}']]


def test_only_pipes_can_seprate_attributes():
    """According to the note at mw:Help:Tables#Table_headers."""
    assert Table(
        '{|class=wikitable\n! style="text-align:left;"! '
        'Item\n! Amount\n! Cost\n|}').data() == [
        ['style="text-align:left;"! Item', 'Amount', 'Cost']]
    assert Table(
        '{|class=wikitable\n! style="text-align:left;"| '
        'Item\n! Amount\n! Cost\n|}').data() == [['Item', 'Amount', 'Cost']]


def test_double_exclamation_marks_are_valid_on_header_rows():
    assert Table('{|class=wikitable\n!a!!b!!c\n|}').data() == [['a', 'b', 'c']]


def test_double_exclamation_marks_are_valid_only_on_header_rows():
    # Actually I'm not sure about this in general.
    assert Table('{|class=wikitable\n|a!!b!!c\n|}').data() == [['a!!b!!c']]


def test_caption_in_row_is_treated_as_pipe_and_plut():
    assert Table('{|class=wikitable\n|a|+b||c\n|}').data() == [['+b', 'c']]


def test_odd_case1():
    assert Table(
        '{|class=wikitable\n'
        '  [[a]]\n'
        ' |+ cp1\n'
        'cp1\n'
        '! h1 ||+ h2\n'
        '|-\n'
        '! h3 !|+ h4\n'
        '|-\n'
        '! h5 |!+ h6\n'
        '|-\n'
        '|c1\n'
        '|+t [[w]]\n\n'
        'text\n'
        '|c2\n'
        '|}').data(span=False) == [
        ['h1', '+ h2'], ['+ h4'], ['!+ h6'], ['c1', 'c2']]


def test_colspan_and_rowspan_and_span_false():
    assert Table(
        '{| class="wikitable"\n!colspan= 6 |11\n|-\n'
        '|rowspan="2"|21\n|22\n|23\n|24\n|colspan="2"|25\n|-\n'
        '|31\n|colspan="2"|32\n|33\n|34\n|}'
    ).data(span=False) == [
        ['11'],
        ['21', '22', '23', '24', '25'],
        ['31', '32', '33', '34']]


def test_colspan_and_rowspan_and_span_true():
    assert Table(
        '{| class="wikitable"\n!colspan= 6 |11\n|-\n'
        '|rowspan="2"|21\n|22\n|23\n|24\n  |colspan="2"|25\n|-\n'
        '|31\n|colspan="2"|32\n|33\n|34\n|}'
    ).data(span=True) == [
        ['11', '11', '11', '11', '11', '11'],
        ['21', '22', '23', '24', '25', '25'],
        ['21', '31', '32', '32', '33', '34']]


def test_inline_colspan_and_rowspan():
    assert Table(
        '{| class=wikitable\n'
        ' !a !! b !!  c !! rowspan = 2 | d \n'
        ' |- \n'
        ' | e || colspan = "2"| f\n'
        '|}').data(span=True) == [
        ['a', 'b', 'c', 'd'],
        ['e', 'f', 'f', 'd']]


def test_growing_downward_growing_cells():
    assert Table(
        '{|class=wikitable\n'
        '| a || rowspan=0 | b\n'
        '|-\n'
        '| c\n'
        '|}').data(span=True) == [['a', 'b'], ['c', 'b']]


def test_colspan_0():
    assert Table(
        '{|class=wikitable\n'
        '| colspan=0 | a || b\n'
        '|-\n'
        '| c || d\n'
        '|}').data(span=True) == [['a', 'b'], ['c', 'd']]


def test_ending_row_group():
    assert Table(
        '{|class=wikitable\n'
        '| rowspan = 3 | a || b\n'
        '|-\n'
        '| c\n'
        '|}').data(span=True) == [['a', 'b'], ['a', 'c'], ['a', None]]


def test_ending_row_group_and_rowspan_0():
    assert Table(
        '{|class=wikitable\n'
        '| rowspan = 3 | a || rowspan = 0 | b || c\n'
        '|-\n'
        '| d\n'
        '|}').data(span=True) == [
        ['a', 'b', 'c'], ['a', 'b', 'd'], ['a', 'b', None]]


def test_row_data():
    assert Table(
        '{|\n|a||b||c\n|-\n|d||e||f\n|-\n|g||h||i\n|}'
    ).data(row=1) == ['d', 'e', 'f']


def test_column_data():
    assert Table(
        '{|\n|a||b||c\n|-\n|d||e||f\n|-\n|g||h||i\n|}'
    ).data(column=1) == ['b', 'e', 'h']


def test_column_and_row_data():
    assert Table(
        '{|\n|a||b||c\n|-\n|d||e||f\n|-\n|g||h||i\n|}'
    ).data(column=1, row=1) == 'e'


def test_header_attr_with_exclamation_mark():
    assert Table(
        '{|class=wikitable\n! 1 !! a1 ! a2 | 2 || class=a3 ! id=a4 | 3\n|}'
    ).data() == [['1', '2', '3']]


def test_nonheader_attr_with_exclamation_mark():
    assert Table(
        '{|class=wikitable\n'
        '| 1 !! 1 ! 1 |||| 3 || a4 ! a4 | 4\n'
        '|}').data() == [['1 !! 1 ! 1', '', '3', '4']]


def test_single_exclamation_is_not_attribute_data_separator():
    assert Table(
        '{|class=wikitable\n'
        '! 1 !! 2 ! 2 !!!! 4 || a5 ! a5 | 5\n'
        '|}').data() == [['1', '2 ! 2', '', '4', '5']]


def test_newline_cell_attr_closure_cant_be_cell_sep():
    assert Table(
        '{|class=wikitable\n'
        '||||| 2 ! 2\n'
        '|}').data() == [['', '', '2 ! 2']]


def test_attr_delimiter_cant_be_adjacent_to_cell_delimiter():
    """Couldn't find a logical explanation for MW's behaviour."""
    assert Table(
        '{|class=wikitable\n'
        '!a| !!b|c\n'
        '|}').data() == [['', 'c']]
    # Remove one space and...
    assert Table(
        '{|class=wikitable\n'
        '!a|!!b|c\n'
        '|}').data() == [['a', 'b|c']]


def test_unicode_data():
    r"""Note the \u201D character at line 2. wikitextparser/issues/9."""
    assert Table(
        '{|class=wikitable\n'
        '|align="center" rowspan="1"|A\u201D\n'
        '|align="center" rowspan="1"|B\n'
        '|}').data() == [['A”', 'B']]


# Table.caption, Table.caption_attrs

def test_no_caption():
    table = Table('{| class="wikitable"\n|a\n|+ ignore\n|}')
    assert table.caption is None
    assert table.caption_attrs is None
    table.caption = 'foo'
    assert table.string == '{| class="wikitable"\n|+foo\n|a\n|+ ignore\n|}'


def test_replace_caption_attrs():
    table = Table('{|class="wikitable"\n|+old|cap\n|}')
    table.caption_attrs = 'new'
    assert table.caption_attrs == 'new'


def test_set_caption_attrs_before_cap():
    table = Table('{| class="wikitable"\n|a\n|+ ignore\n|}')
    table.caption_attrs = 'style=""'
    assert table.caption_attrs == 'style=""'


def test_no_attrs_but_caption():
    text = (
        '{|\n|+Food complements\n|-\n|Orange\n|Apple\n|-'
        '\n|Bread\n|Pie\n|-\n|Butter\n|Ice cream \n|}')
    table = Table(text)
    assert table.caption == 'Food complements'
    assert table.caption_attrs is None
    table.caption = ' C '
    assert table.string == text.replace('Food complements', ' C ')


def test_attrs_and_caption():
    table = Table(
        '{| class="wikitable"\n'
        '|+ style="caption-side:bottom; color:#e76700;"|'
        '\'\'Food complements\'\'\n|-\n|Orange\n|Apple\n|-'
        '\n|Bread\n|Pie\n|-\n|Butter\n|Ice cream \n|}')
    assert table.caption == "''Food complements''"
    assert table.caption_attrs == \
        ' style="caption-side:bottom; color:#e76700;"'


def test_header_cell_starts_with_dash():
    assert Table('''{| class="wikitable"\n!-a\n!-b\n|}''').data() == \
           [['-a', '-b']]


# Table.table_attrs


def test_multiline_table():
    table = Table('{|s\n|a\n|}')
    assert table.attrs == {'s': ''}
    assert table.has_attr('s') is True
    assert table.has_attr('n') is False
    assert table.get_attr('s') == ''
    table.del_attr('s')
    table.set_attr('class', 'wikitable')
    assert repr(table) == "Table('{| class=\"wikitable\"\\n|a\\n|}')"

    assert table.get_attr('class') == 'wikitable'
    table.set_attr('class', 'sortable')
    assert table.attrs == {'class': 'sortable'}
    table.del_attr('class')
    assert table.attrs == {}


def test_attr_contains_template_newline_invalid_chars():
    assert WikiText(
        '  {| class=wikitable |ب style="color: {{text| 1 =\n'
        'red}};"\n'
        '| cell\n'
        '|}\n'
    ).tables[0].get_attr('style') == 'color: {{text| 1 =\nred}};'


def test_pipe_in_text():
    table = Table('{|\n| colspan="2" | text | with pipe\n|}')
    assert table.cells()[0][0].attrs == {"colspan": "2"}


# Table.cells


def test_cell_extraction():
    table = Table(
        '{|class=wikitable\n'
        '|| 1 | 1 || a | 2\n'
        '| 3 ||| 4\n'
        '|| 5\n'
        '! 6 !! a | 7\n'
        '!| 8 || 9\n'
        '|}')
    cells = table.cells()
    assert len(cells) == 1
    assert len(cells[0]) == 9
    cell_string = (
        '\n|| 1 | 1 ',
        '|| a | 2',
        '\n| 3 ',
        '||| 4',
        '\n|| 5',
        '\n! 6 ',
        '!! a | 7',
        '\n!| 8 ',
        '|| 9')
    for r in cells:
        for i, c in enumerate(r):
            assert c.string == cell_string[i]
    # Single cell
    assert table.cells(row=0, column=4).string == cell_string[4]
    # Column only
    assert table.cells(column=4)[0].string == cell_string[4]
    # Row only
    assert table.cells(row=0)[4].string == cell_string[4]


def test_cell_spans():
    assert WikiText(
        '<!-- c -->{|class=wikitable\n| a \n|}'
    ).tables[0].cells(row=0, column=0).value == ' a '


def test_changing_cell_should_effect_the_table():
    t = Table('{|class=wikitable\n|a=b|c\n|}')
    c = t.cells(0, 0)
    c.value = 'v'
    assert c.value == 'v'
    c.set_attr('a', 'b2')
    assert t.string == '{|class=wikitable\n|a="b2"|v\n|}'
    c.del_attr('a')
    assert t.string == '{|class=wikitable\n||v\n|}'
    c.set_attr('c', 'd')
    assert t.string == '{|class=wikitable\n| c="d"|v\n|}'


def test_cell_span_false():
    assert len(Table(
        '{|class=wikitable\n|a=b|c\n|}').cells(span=False)) == 1


def test_get_get_tables():
    assert repr(
        Table('{|\n|a\n|-\n{|\n|b\n|}\n|}').get_tables()
    ) == "[Table('{|\\n|b\\n|}')]"


def test_weird_colspan():
    assert Table(
        '{|class=wikitable\n'
        '! colspan="" | 1 !!colspan=" " | 2 !! 3 !! 4\n'
        '|-\n'
        '| colspan=" 2a2"| a\n'
        '|colspan="1.5"| b\n'
        '|}').data() == [['1', '2', '3', '4'], ['a', 'a', 'b', None]]


def test_caption_containing_piped_wikilink():
    assert Table('{|\n|+a [[b|c]]\n|}').caption == 'a [[b|c]]'


def test_caption_multiline():
    assert Table('{|\n|+a\nb\nc\n|}').caption == "a\nb\nc"


def test_caption_end():
    # MW renders the following test input as """
    # <table>
    #  <caption>caption</caption>
    #  <caption>second caption!</caption>
    #  <tbody><tr><td></td></tr></tbody>
    # </table>
    # """ but only one caption is valid in HTML. Most browsers ignore the
    # second caption tag. wikitextparser only returns the first one.
    assert Table('{|\n|+ caption|| second caption!\n|}').caption == " caption"
    assert Table('{|\n|+style="color:red;"|caption\n|}').caption == "caption"
    assert Table('{|\n|+caption ! caption\n|}').caption == "caption ! caption"
    assert Table('{|\n|+caption !! caption\n! header\n|}').caption \
        == "caption !! caption"


def test_caption_multiline_rows():
    assert Table('{|\n|+a\nb\nc\n|-\n|cell\n|}').caption == "a\nb\nc"


def test_cell_header():
    assert Table('{|\n!1!!style="color:red;"|2\n|}').cells(
        row=0, column=1).is_header is True


def test_not_cell_header():
    assert Table('{|\n!Header\n|Not a header|}').cells(
        row=0, column=1).is_header is False


def test_table_attr_span_false():  # 71
    cell = Table('{|\n|colspan=2| Test1 \n|| Test 2 \n|| Test 3 \n|}').cells(
        span=False)[0][0]
    assert cell.attrs == {'colspan': '2'}
