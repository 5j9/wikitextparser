from wikitextparser import ParserFunction


def test_normal_name_comment_before_hash():
    # Comment before the leading '#' is removed; '#' is preserved.
    assert '#if' == ParserFunction('{{<!---->#if:a}}').normal_name()
    assert '#t' == ParserFunction('{{<!---->\n #T<!---->:}}').normal_name()


def test_normal_name_comment_after_name():
    # Comment immediately after the name is removed.
    assert '#if' == ParserFunction('{{#if<!---->:a}}').normal_name()


def test_normal_name_preserves_hash_and_internal_chars():
    # '#' is part of the name and must survive normalization.
    assert '#t#a' == ParserFunction('{{#t#a:a}}').normal_name()
    assert '#a___b' == ParserFunction('{{#A___B:}}').normal_name()


def test_normal_name_strips_only_leading_whitespace():
    # Leading WS stripped; internal/trailing WS kept (only lstrip, not strip).
    assert '#u ' == ParserFunction('{{ #u :a}}').normal_name()
    assert '#u ' == ParserFunction('{{ #U :a}}').normal_name()


def test_normal_name_preserves_template_in_name():
    pf = ParserFunction('{{#pf {{{p1|d1}}} : {{{p2|d2}}} }}')
    assert '#pf {{{p1|d1}}} ' == pf.normal_name()


def test_normal_name_preserves_internal_newline():
    # A newline inside the name is internal, not leading, so it survives.
    assert '#pf\na' == ParserFunction('{{#pf\na}}').normal_name()
    assert '#pf\r' == ParserFunction('{{#pf\r:a}}').normal_name()


def test_normal_name_empty_name():
    assert '' == ParserFunction('{{:a}}').normal_name()
    assert '#' == ParserFunction('{{#:a}}').normal_name()
