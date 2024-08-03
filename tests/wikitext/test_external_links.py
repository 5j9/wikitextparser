from wikitextparser import Template, WikiText, parse


def test_external_links_in_brackets_in_parser_elements():  # 50
    assert (
        parse('{{t|[http://a b]}}').external_links[0].string == '[http://a b]'
    )
    assert (
        parse('<ref>[http://a b]</ref>').external_links[0].string
        == '[http://a b]'
    )
    assert (
        parse('<ref>[http://a{{b}}]</ref>').external_links[0].string
        == '[http://a{{b}}]'
    )
    assert (
        parse('{{a|{{b|[http://c{{d}}]}}}}').external_links[0].string
        == '[http://c{{d}}]'
    )


def test_with_nowiki():
    assert (
        parse('[http://a.b <nowiki>[c]</nowiki>]').external_links[0].text
        == '<nowiki>[c]</nowiki>'
    )


def test_ipv6_brackets():
    # See:
    # https://en.wikipedia.org/wiki/IPv6_address#Literal_IPv6_addresses_in_network_resource_identifiers
    assert (
        parse('https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/')
        .external_links[0]
        .url
        == 'https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/'
    )
    el = parse(
        '[https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/ t]'
    ).external_links[0]
    assert el.url == 'https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/'
    assert el.text == 't'
    s = '[//[fe80::1ff:fe23:4567:890a]:443/ t]'
    assert parse(s).external_links[0].string == s


def test_in_template():
    # with brackets
    els = parse('{{text|http://example.com?foo=bar}}').external_links
    assert len(els) == 1
    assert els[0].url == 'http://example.com?foo=bar'
    # without brackets
    els = parse('{{text|[http://example.com?foo=bar]}}').external_links
    assert len(els) == 1
    assert els[0].url == 'http://example.com?foo=bar'


def test_starting_boundary():
    assert not parse('turn:a').external_links


def test_external_links_inside_template():
    t = Template('{{t0|urn:0{{t1|urn:1}}}}')
    # Warning: both urn's are treated ast one.
    # But on a live site this depends on the template outcome.
    assert t.external_links[0].string == 'urn:0'


def test_bare_link():
    s = 'text1 HTTP://mediawiki.org text2'
    wt = WikiText(s)
    assert 'HTTP://mediawiki.org' == str(wt.external_links[0])


def test_with_lable():
    s = 'text1 [http://mediawiki.org MediaWiki] text2'
    el = WikiText(s).external_links[0]
    assert 'http://mediawiki.org' == el.url
    assert 'MediaWiki' == el.text


def test_external_link_match_is_not_in_spans():
    wt = WikiText('t [http://b.b b] t [http://c.c c] t')
    # calculate the links
    links1 = wt.external_links
    wt.insert(0, 't [http://a.a a]')
    links2 = wt.external_links
    assert links1[1].string == '[http://c.c c]'
    assert links2[0].string == '[http://a.a a]'


def test_numbered_link():
    s = 'text1 [http://mediawiki.org] text2'
    wt = WikiText(s)
    assert '[http://mediawiki.org]' == str(wt.external_links[0])


def test_protocol_relative():
    s = 'text1 [//en.wikipedia.org wikipedia] text2'
    wt = WikiText(s)
    assert '[//en.wikipedia.org wikipedia]' == str(wt.external_links[0])


def test_destroy():
    s = 'text1 [//en.wikipedia.org wikipedia] text2'
    wt = WikiText(s)
    del wt.external_links[0].string
    assert 'text1  text2' == str(wt)


def test_wikilink2externallink_fallback():
    p = parse('[[http://example.com foo bar]]')
    assert '[http://example.com foo bar]' == p.external_links[0].string
    assert 0 == len(p.wikilinks)


def test_template_in_link():
    # Note: In reality all assertions depend on the template outcome.
    assert (
        parse('http://example.com{{dead link}}').external_links[0].url
        == 'http://example.com'
    )
    assert (
        parse('http://example.com/foo{{!}}bar').external_links[0].url
        == 'http://example.com/foo'
    )
    assert (
        parse('[http://example.com{{foo}}text]').external_links[0].url
        == 'http://example.com'
    )
    assert (
        parse('[http://example.com{{foo bar}} t]').external_links[0].url
        == 'http://example.com'
    )


def test_comment_in_external_link():
    # This probably can be fixed, but who uses comments within urls?
    el = parse('[http://example.com/foo<!-- comment -->bar]').external_links[0]
    assert el.text is None
    assert el.url == 'http://example.com/foo<!-- comment -->bar'
    assert (
        parse('[http://example<!-- c -->.com t]').external_links[0].url
        == 'http://example<!-- c -->.com'
    )


def test_no_bare_external_link_within_wiki_links():
    """A wikilink's target may not be an external link."""
    p = parse('[[ https://w|b]]')
    assert 'https://w|b' == p.external_links[0].string
    assert 0 == len(p.wikilinks)


def test_external_link_containing_wikilink():
    s = '[http://a.b [[c]] d]'
    assert parse(s).external_links[0].string == s


def test_wikilinks_and_ext_tags_can_be_part_of_text_but_not_url():  # 109
    assert not parse('[//<ref></ref>]').external_links
    assert not parse('[//[[a]]]').external_links


def test_bare_external_link_must_have_scheme():
    """Bare external links must have scheme."""
    assert len(parse('//mediawiki.org').external_links) == 0


def test_external_link_with_template():
    """External links may contain templates."""
    assert len(parse('http://example.com/{{text|foo}}').external_links) == 1


def test_external_link_containing_extension_tags():
    s = '[https://www.google.<includeonly>com </includeonly>a]'
    el = parse(s).external_links[0]
    assert str(el) == s
    # Warning: This depends on context and/or requires evaluation.
    assert el.url != 'https://www.google.a'
    s = '[https://www.google.<noinclude>com </noinclude>a]'
    el = parse(s).external_links[0]
    assert str(el) == s
    # Warning: This depends on context and/or requires evaluation.
    assert el.url != 'https://www.google.com'


def test_parser_function_in_external_link():
    assert (
        parse('[urn:u {{<!--c-->#if:a|a}}]')
        .external_links[0]
        .parser_functions[0]
        .string
        == '{{<!--c-->#if:a|a}}'
    )
    # Note: Depends on the parser function outcome.
    assert len(parse('[urn:{{#if:a|a|}} t]').external_links) == 0


def test_equal_span_ids():
    p = parse('lead\n== 1 ==\nhttp://wikipedia.org/')
    # noinspection PyProtectedMember
    assert id(p.external_links[0]._span_data) == id(
        p.sections[1].external_links[0]._span_data
    )


def test_external_link_should_not_span_over_tags():
    (els,) = parse('<ref>[https://a.b/ </ref>]').external_links
    assert els.string == 'https://a.b/'


def test_external_link_in_pf_in_tl():  # 110
    (els,) = parse('{{text|<ref>[https://a.b a]</ref>}}').external_links
    assert els.string == '[https://a.b a]'


def test_ext_link_overwriting_template():  # 74
    p = parse('{{test}}')
    t = p.templates[0]
    # It is could be considered unintuitive for p.templates to still return
    # [Template('[https://link]')]. As it stands, the user who is overwriting
    # the template should keep track of such changes and skip edited templates
    # that have become invalid.
    t.string = '[https://link]'
    assert p.external_links[0].string == '[https://link]'


def test_ext_links_inside_ref_containing_pipe():  # 139
    (el,) = parse(
        '<ref>{{t|url=http://www.kismac.de|titre=Germany says: Good-bye KisMAC!|auteur=Michael Rossberg}}</ref>'
    ).external_links
    assert el.string == 'http://www.kismac.de'
