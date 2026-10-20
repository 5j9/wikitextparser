from pytest import mark

from wikitextparser import parse
from wikitextparser._wikilist import WikiList


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


def test_multiline_tags_cr():
    lists = parse('#1<br\r/>{{note}}\r#2<s\r>s</s\r>\r#3').get_lists()[0].items
    assert len(lists) == 3


def test_definition_list_with_external_link():  # 91
    assert parse('; http://a.b :d\n').get_lists()[0].items == [
        ' http://a.b ',
        'd',
    ]


@mark.parametrize('newline', ['\n', '\r', '\r\n'])
def test_first_item_is_list(newline):  # 70
    l0 = parse(
        f'a{newline}###b{newline}###c{newline}##d{newline}#e{newline}f'
    ).get_lists()[0]

    assert l0.fullitems == [
        f'###b{newline}###c{newline}##d{newline}',
        f'#e{newline}',
    ]
    assert l0.items == ['', 'e']

    l0_0 = l0.get_lists()[0]
    assert l0_0.level == 2
    assert l0_0.pattern == r'\#\#'
    assert l0_0.items == ['', 'd']
    assert l0_0.fullitems == [
        f'###b{newline}###c{newline}',
        f'##d{newline}',
    ]


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
    lists = parse('a\n###b\n##*c\n##;d\n###e\n##f\n#g\nh\n').get_lists()
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


def test_dl_with_second_pattern():
    # <dl>
    #     <dt>
    #         <dl>
    #             <dt>a</dt>
    #             <dd>1</dd>
    #             <dt>b</dt>
    #             <dd>2</dd>
    #         </dl>
    #     </dt>
    #     <dt>c</dt>
    #     <dd>3</dd>
    # </dl>
    l0 = parse(';;a:1\n;;b:2\n;c:3\n').get_lists()
    assert l0[0].fullitems == [';;a:1\n;;b:2\n', ';c', ':3\n']
    assert l0[0].items == ['', 'c', '3']
    assert [l.string for l in l0[0].sublists()] == [';;a:1\n;;b:2\n']

    # <dl>
    #     <dt>t1</dt>
    #     <dd>d1</dd>
    #     <dt>
    #          <dl>
    #               <dt>t2</dt>
    #               <dd>:d2</dd>
    #               <dt>
    #                    <dl>
    #                         <dt>t3</dt>
    #                         <dd>::d3</dt>
    #                    </dl>
    #               </dt>
    #          </dl>
    #     </dt>
    # </dl>

    l0 = parse(';t1:d1\n;;t2::d2\n;;;t3:::d3').get_lists()
    assert l0[0].fullitems == [';t1', ':d1\n', ';;t2::d2\n;;;t3:::d3']
    l1 = l0[0].sublists(2)
    assert l1[0].fullitems == [';;t2', '::d2\n', ';;;t3:::d3']
    assert l1[0].items == ['t2', ':d2', '']

    l0 = parse('*;d1 :d2\n*;d3 :d4').get_lists()
    assert l0[0].fullitems == ['*;d1 :d2\n*;d3 :d4']
    l1 = l0[0].sublists(0)
    assert l1[0].fullitems == ['*;d1 ', ':d2\n', '*;d3 ', ':d4']

    l0 = parse('*#*#;*;;foo : bar\n*#*#;boo : baz').get_lists()
    assert l0[0].fullitems == ['*#*#;*;;foo : bar\n*#*#;boo : baz']
    l1 = l0[0].sublists(0)[0].sublists(0)[0].sublists(0)[0].sublists(0)[0]
    assert l1.fullitems == ['*#*#;*;;foo : bar\n', '*#*#;boo ', ': baz']

def test_dl_with_nested_elements():
    l0 = parse(';<b style=\"display: inline\">bold</b>').get_lists()
    assert l0[0].fullitems == [';<b style="display: inline">bold</b>']
    l0 = parse(";'''1:00''':bar\n").get_lists()
    assert l0[0].fullitems == [";'''1:00'''", ":bar\n"]
    l0 = parse(";''1:00'':bar\n").get_lists()
    assert l0[0].fullitems == [";''1:00''", ":bar\n"]
    l0 = parse(";[[Category:foo]]:bar\n").get_lists()
    assert l0[0].fullitems == [';[[Category:foo]]', ':bar\n']
    l0 = parse(";{{{a|:b}}}:bar\n").get_lists()
    assert l0[0].fullitems == [';{{{a|:b}}}', ':bar\n']
    l0 = parse(";{{t|:a|b=:c}}:bar\n").get_lists()
    assert l0[0].fullitems == [';{{t|:a|b=:c}}', ':bar\n']
    l0 = parse(";{{#if:a|b|c}}:bar\n").get_lists()
    assert l0[0].fullitems == [';{{#if:a|b|c}}', ':bar\n']

def test_get_lists_with_comments():
    l0 = parse('<!--c1-->*a\n<!--c2--><!--c3--><!--c4-->*b').get_lists()
    assert l0[0].fullitems == ['<!--c1-->*a\n', '<!--c2--><!--c3--><!--c4-->*b']
    l0 = parse('<!--c1-->*a\n<!--c2--><!--c3--><!--c4-->*b\n<!--c5-->**b1').get_lists()
    assert l0[0].fullitems == ['<!--c1-->*a\n', '<!--c2--><!--c3--><!--c4-->*b\n<!--c5-->**b1']
    assert l0[0].sublists(1)[0].fullitems == ['<!--c5-->**b1']
    l0 = parse('<!--c1-->*a\n<!--c2--><!--c3--><!--c4-->*b\n<!--c5-->*<!--c6-->*b1').get_lists()
    assert l0[0].fullitems == ['<!--c1-->*a\n', '<!--c2--><!--c3--><!--c4-->*b\n', '<!--c5-->*<!--c6-->*b1']
