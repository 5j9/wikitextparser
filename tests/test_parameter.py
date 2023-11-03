from pytest import warns

from wikitextparser import Parameter


def test_parameters():
    assert (
        repr(Parameter('{{{a|{{{b}}}}}}').parameters[0])
        == "Parameter('{{{b}}}')"
    )


def test_basic():
    p = Parameter('{{{P}}}')
    assert 'P' == p.name
    assert '' == p.pipe
    assert p.default is None
    p.name = 'Q'
    assert 'Q' == p.name

    p = Parameter('{{{P|}}}')
    assert '' == p.default
    p.name = ' Q '
    assert '{{{ Q |}}}' == p.string

    p = Parameter('{{{P|D}}}')
    assert 'P' == p.name
    assert '|' == p.pipe
    assert 'D' == p.default
    p.name = ' Q '
    assert '{{{ Q |D}}}' == p.string
    p.default = ' V '
    assert "Parameter('{{{ Q | V }}}')" == repr(p)


def test_default_setter():
    # The default is not None
    p = Parameter('{{{ Q |}}}')
    p.default = ' V '
    assert '{{{ Q | V }}}' == p.string
    # The default is None
    p = Parameter('{{{ Q }}}')
    p.default = ' V '
    assert '{{{ Q | V }}}' == p.string
    p.default = ''
    assert '{{{ Q |}}}' == p.string
    del p.default
    assert '{{{ Q }}}' == p.string
    # Setting default to None when it is already None
    del p.default
    assert '{{{ Q }}}' == p.string


def test_appending_default():
    p = Parameter('{{{p1|{{{p2|}}}}}}')
    p.append_default('p3')
    assert '{{{p1|{{{p2|{{{p3|}}}}}}}}}' == p.string
    # What happens if we try it again
    p.append_default('p4')
    assert '{{{p1|{{{p2|{{{p3|{{{p4|}}}}}}}}}}}}' == p.string
    # Appending to and inner parameter without default
    p = Parameter('{{{p1|{{{p2}}}}}}')
    p.append_default('p3')
    assert '{{{p1|{{{p2|{{{p3}}}}}}}}}' == p.string
    # Don't change and inner parameter which is not a default
    p = Parameter('{{{p1|head {{{p2}}} tail}}}')
    p.append_default('p3')
    assert '{{{p1|{{{p3|head {{{p2}}} tail}}}}}}' == p.string
    # Appending to parameter with no default
    p = Parameter('{{{p1}}}')
    p.append_default('p3')
    assert '{{{p1|{{{p3}}}}}}' == p.string
    # Preserve whitespace
    p = Parameter('{{{ p1 |{{{ p2 | }}}}}}')
    p.append_default(' p3 ')
    assert '{{{ p1 |{{{ p2 |{{{ p3 | }}}}}}}}}' == p.string
    # White space before or after a prameter makes it a value (not default)
    p = Parameter('{{{ p1 | {{{ p2 | }}} }}}')
    p.append_default(' p3 ')
    assert '{{{ p1 |{{{ p3 | {{{ p2 | }}} }}}}}}' == p.string
    # If the parameter already exists among defaults, it won't be added.
    p = Parameter('{{{p1|{{{p2|}}}}}}')
    p.append_default('p1')
    assert '{{{p1|{{{p2|}}}}}}' == p.string
    p.append_default('p2')
    assert '{{{p1|{{{p2|}}}}}}' == p.string


def test_ignore_comment_pipes():
    # name
    p = Parameter('{{{1<!-- |comment| -->|text}}}')
    assert p.name == '1<!-- |comment| -->'
    # name.setter
    p.name = '2<!-- |comment| -->'
    assert p.name == '2<!-- |comment| -->'
    # default
    assert p.default == 'text'
    # default.setter
    p.default = 'default'
    assert p.string == '{{{2<!-- |comment| -->|default}}}'
    # pipe
    del p.default
    assert p.string == '{{{2<!-- |comment| -->}}}'
    assert p.pipe == ''
