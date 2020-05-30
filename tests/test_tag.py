from regex import compile as regex_compile
from pytest import mark

from wikitextparser import Tag, parse
# noinspection PyProtectedMember
from wikitextparser._tag import TAG_FULLMATCH, END_TAG_PATTERN
# noinspection PyProtectedMember
from wikitextparser._wikitext import NAME_CAPTURING_HTML_START_TAG_FINDITER


def test_get_tags():
    assert repr(Tag('<b><s></s></b>').get_tags()) == "[Tag('<s></s>')]"


def test_start_tag_patterns():
    assert start_tag_finder(b'<b>').groupdict() == {
        'name': b'b', 'attr': None, 'quote': None,
        'start_tag': b'<b>', 'attr_name': None,
        'self_closing': None, 'attr_value': None}
    assert start_tag_finder(b'<b t>').groupdict() == {
        'name': b'b', 'attr': b' t', 'quote': None,
        'start_tag': b'<b t>', 'attr_name': b't', 'attr_value': b'',
        'self_closing': None}
    assert start_tag_finder(b'<div value=yes>').groupdict() == {
        'name': b'div', 'attr': b' value=yes', 'quote': None,
        'start_tag': b'<div value=yes>', 'attr_name': b'value',
        'attr_value': b'yes', 'self_closing': None}
    assert start_tag_finder(b"<div class='body'>").groupdict() == {
        'name': b'div', 'attr': b" class='body'", 'quote': b"'",
        'start_tag': b"<div class='body'>", 'attr_name': b'class',
        'attr_value': b'body', 'self_closing': None}
    # This is not standard HTML5, but could be useful to have.
    # ae(
    #     START_TAG_MATCH('<s style=>').groupdict(),
    #     {'name': 's', 'attr': 'style=', 'quote': None,
    #      'start': '<s style=>', 'attr_name': 'style', 'attr_value': ''
    #      'self_closing': None}
    # )
    assert start_tag_finder(b"<table a1=v1 a2=v2>").capturesdict() == {
        'attr_name': [b'a1', b'a2'], 'start_tag': [b'<table a1=v1 a2=v2>'],
        'attr': [b' a1=v1', b' a2=v2'], 'quote': [],
        'attr_value': [b'v1', b'v2'], 'self_closing': [],
        'name': [b'table']}


def test_end_tag_patterns():
    assert regex_compile(
            END_TAG_PATTERN.replace(b'{name}', b'p')
        ).search(b'</p>').groupdict() == {'end_tag': b'</p>'}


@mark.xfail
def test_content_cannot_contain_another_start():
    """Checking for such situations is not currently required."""
    assert TAG_FULLMATCH.search('<a><a>c</a></a>')[0] == '<a>c</a>'


def test_name():
    t = Tag('<t>c</t>')
    assert t.name == 't'
    t.name = 'a'
    assert repr(t) == "Tag('<a>c</a>')"
    t = Tag('<t/>')
    assert t.name == 't'
    t.name = 'n'
    assert t.string == '<n/>'


def test_contents():
    t = Tag('<t>\nc\n</t>')
    assert t.contents == '\nc\n'
    t.contents = 'n'
    assert t.string == '<t>n</t>'
    t = Tag('<t></t>')
    assert t.contents == ''
    t.contents = 'n'
    assert t.string == '<t>n</t>'
    t = Tag('<t/>')
    assert t.contents == ''
    t.contents = 'n'
    assert t.string == '<t>n</t>'


def test_get_attr_value():
    t = Tag('<t n1=v1 n2=v2 n1=v3 n2=v4>c</t>')
    assert t.get_attr('n1') == 'v3'
    assert t.get_attr('n2') == 'v4'
    t = Tag('<t a>c</t>')
    assert t.get_attr('a') == ''
    assert t.get_attr('z') is None


def test_set_attr_value():
    t = Tag('<t n1=v1 n2=v2 n1=\'v3\'>c</t>')
    t.set_attr('n1', 'v4')
    t.set_attr('n2', 'v5')
    assert t.string == '<t n1=v1 n2="v5" n1="v4">c</t>'
    t.set_attr('id', '1')
    assert t.string == '<t n1=v1 n2="v5" n1="v4" id="1">c</t>'
    t = Tag('<t>c</t>')
    t.set_attr('n', '')
    assert t.string == '<t n>c</t>'


def test_attr_deletion():
    t = Tag('<t n1=v1 n1=v333 n2=v22>c</t>')
    t.del_attr('n1')
    assert t.string == '<t n2=v22>c</t>'


def test_has_attr():
    t = Tag('<t n1=v1>c</t>')
    assert t.has_attr('n1') is True
    assert t.has_attr('n2') is False


def test_parsed_contents():
    t = Tag('<t>c [[w]]</t>')
    c1 = t.parsed_contents
    assert repr(c1) == "SubWikiText('c [[w]]')"
    assert c1.wikilinks[0].target == 'w'
    # The new contents object won't create a new span
    c2 = t.parsed_contents
    # noinspection PyProtectedMember
    assert len(c2._type_to_spans['WikiLink']) == 1


def test_parsed_content_offset():
    assert parse('t<b>1</b>t').get_tags()[0].parsed_contents.string == '1'


def test_attrs():
    assert Tag('<t n1=v1 n2="v2" n3>c</t>').attrs == {
        'n1': 'v1', 'n2': 'v2', 'n3': ''}


def test_contents_contains_tl():
    t = Tag('<b>{{text|t}}</b>')
    assert t.contents == '{{text|t}}'


def start_tag_finder(string):
    """Return the first found match of START_TAG_FINDITER."""
    return next(NAME_CAPTURING_HTML_START_TAG_FINDITER(string))
