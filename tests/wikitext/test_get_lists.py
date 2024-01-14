from pytest import mark

from wikitextparser import parse


def test_get_lists_with_no_pattern():
    parsed = parse('*a\n;c:d\n#b')
    lists = parsed.get_lists()
    assert len(lists) == 3
    assert lists[1].items == ['c', 'd']


def test_multiline_tags():
    i1, i2, i3 = (
        parse('#1<br\n/>{{note}}\n#2<s\n>s</s\n>\n#3').get_lists()[0].items
    )
    assert i1 == '1<br\n/>{{note}}'
    assert i2 == '2<s\n>s</s\n>'
    assert i3 == '3'
    # an invalid tag name containing newlines will break the list
    assert len(parse('#1<br/\n>\n#2<abc\n>\n#3').get_lists()[0].items) == 2


def test_definition_list_with_external_link():  # 91
    assert parse('; http://a.b :d\n').get_lists()[0].items == [
        ' http://a.b ',
        'd',
    ]


def test_first_item_is_list():  # 70
    l0 = parse('a\n' '###b\n' '###c\n' '##d\n' '#e\n' 'f').get_lists()[0]
    assert l0.fullitems == ['###b\n###c\n##d\n', '#e\n']
    assert l0.items == ['', 'e']
    l0_0 = l0.get_lists()[0]
    assert l0_0.level == 2
    assert l0_0.pattern == r'\#\#'
    assert l0_0.items == ['', 'd']
    assert l0_0.fullitems == ['###b\n###c\n', '##d\n']


def test_listitems_with_different_patterns():
    # <ol>
    #     <li>
    #         <ol>
    #             <li>
    #                 <ol>
    #                     <li>b</li>
    #                 </ol>
    #                 <ul>
    #                     <li>c</li>
    #                 </ul>
    #                 <dl>
    #                     <dt>d</dt>
    #                 </dl>
    #                 <ol>
    #                     <li>e</li>
    #                 </ol>
    #             </li>
    #             <li>f</li>
    #         </ol>
    #     </li>
    #     <li>g</li>
    # </ol>
    lists = parse(
        'a\n' '###b\n' '##*c\n' '##;d\n' '###e\n' '##f\n' '#g\n' 'h\n'
    ).get_lists()
    assert len(lists) == 1
    l0 = lists[0]
    assert l0.items == ['', 'g']
    assert l0.fullitems == ['###b\n##*c\n##;d\n###e\n##f\n', '#g\n']

    lists = l0.get_lists()
    assert len(lists) == 1
    l0_0 = lists[0]
    assert l0_0.items == ['', 'f']
    assert l0_0.fullitems == ['###b\n##*c\n##;d\n###e\n', '##f\n']

    lists = l0_0.get_lists()
    assert len(lists) == 4
    assert [li.items for li in lists] == [['b'], ['c'], ['d'], ['e']]


@mark.xfail
def test_dl_with_second_pattern():
    # <dl>
    #     <dt>a</dt>
    #     <dd>
    #         <dl>
    #             <dt>1</dt>
    #             <dt>b</dt>
    #             <dd>2</dd>
    #         </dl>
    #     </dd>
    # </dl>
    # <dl>
    #     <dt>c</dt>
    #     <dd>3</dd>
    # </dl>
    assert len(parse(';;a:1\n;;b:2\n;c:3\n').get_lists()) == 2
