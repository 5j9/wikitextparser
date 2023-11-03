from pytest import mark

from wikitextparser import Section


def test_level6():
    s = Section('====== == ======\n')
    assert 6 == s.level
    assert ' == ' == s.title


def test_nolevel7():
    s = Section('======= h6 =======\n')
    assert 6 == s.level
    assert '= h6 =' == s.title


def test_unbalanced_equalsigns_in_title():
    s = Section('====== ==   \n')
    assert 2 == s.level
    assert '==== ' == s.title

    s = Section('== ======   \n')
    assert 2 == s.level
    assert ' ====' == s.title

    s = Section('========  \n')
    assert 3 == s.level
    assert '==' == s.title


def test_leadsection():
    s = Section('lead text. \n== section ==\ntext.')
    assert 0 == s.level
    assert s.title is None


def test_set_title():
    s = Section('== section ==\ntext.')
    s.title = ' newtitle '
    assert ' newtitle ' == s.title


def test_del_title():
    s = Section('== section ==\ntext.')
    del s.title
    assert 'text.' == s.string
    assert s.title is None
    del s.title  # no change, no exception


@mark.xfail
def test_lead_set_title():
    s = Section('lead text')
    s.title = ' newtitle '


def test_set_contents():
    s = Section('== title ==\ntext.')
    s.contents = ' newcontents '
    assert ' newcontents ' == s.contents


def test_set_lead_contents():
    s = Section('lead')
    s.contents = 'newlead'
    assert 'newlead' == s.string


def test_set_level():
    s = Section('=== t ===\ntext')
    s.level = 2
    assert '== t ==\ntext' == s.string


def test_template_at_the_start():
    ts = Section('{{t}}').templates
    assert ts[0].string == '{{t}}'


def test_section_heading_tabs():
    s = Section('=\tt\t=\t')
    assert s.string == '=\tt\t=\t'
    assert s.title == '\tt\t'
    assert s.contents == ''


def test_trailing_space_setter():
    s = Section('=t= \no')
    s.contents = 'n'
    assert '=t= \nn' == s.string


def test_setting_lead_section_contents():
    s = Section('a\nb')
    s.contents = 'c'
    assert 'c' == s.string


def test_level_setter_does_not_overwrite_title():
    s = Section('={{t}}=\nb')
    t = s.templates[0]
    s.level = 1  # testing for no effect
    s.level = 2
    assert '=={{t}}==\nb' == s.string
    assert '{{t}}' == t.string
