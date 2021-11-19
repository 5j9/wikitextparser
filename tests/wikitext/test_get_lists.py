from pytest import warns

from wikitextparser import ParserFunction, parse


def test_get_lists_with_no_pattern():
    wikitext = '*a\n;c:d\n#b'
    parsed = parse(wikitext)
    with warns(DeprecationWarning):
        # noinspection PyDeprecation
        lists = parsed.lists()
    assert len(lists) == 3
    assert lists[1].items == ['c', 'd']


def test_multiline_tags():
    i1, i2, i3 = parse(
        '#1<br\n/>{{note}}\n#2<s\n>s</s\n>\n#3').get_lists()[0].items
    assert i1 == '1<br\n/>{{note}}'
    assert i2 == '2<s\n>s</s\n>'
    assert i3 == '3'
    # an invalid tag name containing newlines will break the list
    assert len(parse('#1<br/\n>\n#2<abc\n>\n#3').get_lists()[0].items) == 2


def test_get_lists_deprecation():
    with warns(DeprecationWarning):
        # noinspection PyTypeChecker
        list_ = ParserFunction('{{#if:|*a\n*b}}').get_lists(None)[0]
    with warns(DeprecationWarning):
        # noinspection PyTypeChecker
        list_.get_lists(None)
    with warns(DeprecationWarning):
        # noinspection PyTypeChecker
        list_.sublists(pattern=None)


def test_definition_list_with_external_link():  # 91
    assert parse("; http://a.b :d\n").get_lists()[0].items == \
        [' http://a.b ', 'd']
