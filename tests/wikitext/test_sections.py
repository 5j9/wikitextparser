from pytest import mark

from wikitextparser import WikiText, parse


def test_grab_the_final_newline_for_the_last_section():
    wt = WikiText('== s ==\nc\n')
    assert '== s ==\nc\n' == wt.sections[1].string


def test_blank_lead():
    wt = WikiText('== s ==\nc\n')
    assert '== s ==\nc\n' == wt.sections[1].string


# Todo: Parser should also work with windows line endings.
@mark.xfail
def test_multiline_with_carriage_return():
    s = 'text\r\n= s =\r\n{|\r\n| a \r\n|}\r\ntext'
    p = parse(s)
    assert 'text\r\n' == p.sections[0].string


def test_inserting_into_sections():
    wt = WikiText('== s1 ==\nc\n')
    s1 = wt.sections[1]
    wt.insert(0, 'c\n== s0 ==\nc\n')
    assert '== s1 ==\nc\n' == s1.string
    assert 'c\n== s0 ==\nc\n== s1 ==\nc\n' == wt.string
    s0 = wt.sections[1]
    assert '== s0 ==\nc\n' == s0.string
    assert 'c\n== s0 ==\nc\n== s1 ==\nc\n' == wt.string
    s1.insert(len(wt.string), '=== s2 ===\nc\n')
    assert (
        'c\n'
        '== s0 ==\n'
        'c\n'
        '== s1 ==\n'
        'c\n'
        '=== s2 ===\n'
        'c\n') == wt.string
    s3 = wt.sections[3]
    assert '=== s2 ===\nc\n' == s3.string


def test_subsection():
    a = parse('0\n== a ==\n1\n=== b ===\n2\n==== c ====\n3\n').sections[1]
    assert '== a ==\n1\n=== b ===\n2\n==== c ====\n3\n' == a.string
    a_sections = a.sections
    assert '' == a_sections[0].string
    assert '== a ==\n1\n=== b ===\n2\n==== c ====\n3\n' == a_sections[1].string
    b = a_sections[2]
    assert '=== b ===\n2\n==== c ====\n3\n' == b.string
    # Sections use the same span object
    # noinspection PyProtectedMember
    assert b.sections[1]._span_data is b._span_data
    assert '==== c ====\n3\n' == b.sections[2].string


def test_tabs_in_heading():
    """Test that insert parses the inserted part."""
    t = '=\tt\t=\t'
    assert str(parse(t).sections[1]) == t


def test_deleting_a_section_wont_corrupt_others():
    z, a, b, c = parse('=a=\na\n==b==\nb\n==c==\nc').sections
    del b.string
    assert c.string == '==c==\nc'


def test_section_templates():
    """section.templates returns templates only from that section."""
    templates = parse('{{t1}}\n==section==\n{{t2}}').sections[1].templates
    assert len(templates) == 1
    assert templates[0].string == '{{t2}}'


def test_by_heading_pattern():
    wt = parse(
        'lead\n'
        '= h1 =\n'
        '== h2 ==\n'
        't2\n'
        '=== h3 ===\n'
        '3\n'
        '= h =\n'
        'end'
    )
    lead, h1, h2, h3, h = wt.get_sections(include_subsections=False)
    assert lead.string == 'lead\n'
    assert h1.string == '= h1 =\n'
    assert h2.string == '== h2 ==\nt2\n'
    assert h3.string == '=== h3 ===\n3\n'
    assert h.string == '= h =\nend'
    # return the same span when returning same section
    lead_, h1_, h2_, h3_, h_ = wt.get_sections(include_subsections=False)
    # noinspection PyProtectedMember
    assert lead._span_data is lead_._span_data
    # noinspection PyProtectedMember
    assert h._span_data is h_._span_data
    # do not create repeated spans
    # noinspection PyProtectedMember
    assert len(wt._type_to_spans['Section']) == 5
    h1, h = wt.get_sections(include_subsections=False, level=1)
    assert h1.string == '= h1 =\n'
    assert h.string == '= h =\nend'
