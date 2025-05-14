from wikitextparser import ParserFunction, Template, WikiText, parse


def test_template_with_multi_args():
    wt = WikiText('{{a|b=b|c=c|d=d|e=e}}')
    assert (
        '{{a\n    | b = b\n    | c = c\n    | d = d\n    | e = e\n}}'
        == wt.pformat()
    )


def test_double_space_indent():
    s = '{{a|b=b|c=c|d=d|e=e}}'
    wt = WikiText(s)
    assert '{{a\n  | b = b\n  | c = c\n  | d = d\n  | e = e\n}}' == wt.pformat(
        '  '
    )


def test_remove_comments():
    assert '{{a\n  | e = e\n}}' == WikiText(
        '{{a|<!--b=b|c=c|d=d|-->e=e}}'
    ).pformat('  ', True)


def test_first_arg_of_tag_is_whitespace_sensitive():
    """The second argument of #tag is an exception.

    See the last warning on [[mw:Help:Magic_words#Miscellaneous]]:
    You must write {{#tag:tagname||attribute1=value1|attribute2=value2}}
    to pass an empty content. No space is permitted in the area reserved
    for content between the pipe characters || before attribute1.
    """
    s = '{{#tag:ref||name="n1"}}'
    wt = WikiText(s)
    assert s == wt.pformat()
    s = '{{#tag:foo| }}'
    wt = WikiText(s)
    assert s == wt.pformat()


def test_invoke():
    """#invoke args are also whitespace-sensitive."""
    s = '{{#invoke:module|func|arg}}'
    wt = WikiText(s)
    assert s == wt.pformat()


def test_on_parserfunction():
    s = '{{#if:c|abcde = f| g=h}}'
    wt = parse(s)
    assert ('{{#if:\n    c\n    | abcde = f\n    | g=h\n}}') == wt.pformat()


def test_parserfunction_with_no_pos_arg():
    s = '{{#switch:case|a|b}}'
    wt = parse(s)
    assert ('{{#switch:\n    case\n    | a\n    | b\n}}') == wt.pformat()


def test_convert_positional_to_keyword_if_possible():
    assert (
        '{{t\n    | 1 = a\n    | 2 = b\n    | 3 = c\n}}'
        == parse('{{t|a|b|c}}').pformat()
    )


def test_inconvertible_positionals():
    """Otherwise the second positional arg will also be passed as 1.

    Because of T24555 we can't use "<nowiki/>" to preserve the
    whitespace of positional arguments. On the other hand we can't just
    convert the initial arguments to keyword and keep the rest as
    positional, because that would produce duplicate args as stated above.

    What we *can* do is to either convert all the arguments to keyword
    args if possible, or we should only convert the longest part of
    the tail of arguments that is convertible.

    Use <!--comments--> to align positional arguments where necessary.

    """
    assert ('{{t\n    |a<!--\n -->| b <!--\n-->}}') == parse(
        '{{t|a| b }}'
    ).pformat()
    assert ('{{t\n    | a <!--\n -->| 2 = b\n    | 3 = c\n}}') == parse(
        '{{t| a |b|c}}'
    ).pformat()


def test_commented_repformat():
    s = '{{t\n    | a <!--\n -->| 2 = b\n    | 3 = c\n}}'
    assert s == parse(s).pformat()


def test_dont_treat_parser_function_arguments_as_kwargs():
    """The `=` is usually just a part of parameter value.

    Another example: {{fullurl:Category:Top level|action=edit}}.
    """
    assert (
        '{{#if:\n    true\n    | <span style="color:Blue;">text</span>\n}}'
    ) == parse('{{#if:true|<span style="color:Blue;">text</span>}}').pformat()


def test_ignore_zwnj_for_alignment():
    assert (
        '{{ا\n    | نیم\u200cفاصله       = ۱\n    | بدون نیم فاصله = ۲\n}}'
    ) == parse('{{ا|نیم‌فاصله=۱|بدون نیم فاصله=۲}}').pformat()


def test_equal_sign_alignment():
    assert (
        '{{t\n    | long_argument_name = 1\n    | 2                  = 2\n}}'
    ) == parse('{{t|long_argument_name=1|2=2}}').pformat()


def test_arabic_ligature_lam_with_alef():
    """'ل' + 'ا' creates a ligature with one character width.

    Some terminal emulators do not support this but it's defined in
    Courier New font which is the main (almost only) font used for
    monospaced Persian texts on Windows. Also tested on Arabic Wikipedia.
    """
    assert (
        '{{ا\n    | الف = ۱\n    | لا   = ۲\n}}'
        == parse('{{ا|الف=۱|لا=۲}}').pformat()
    )


def test_pf_inside_t():
    wt = parse('{{t|a= {{#if:I|I}} }}')
    assert (
        '{{t\n    | a = {{#if:\n        I\n        | I\n    }}\n}}'
    ) == wt.pformat()


def test_nested_pf_inside_tl():
    wt = parse('{{t1|{{t2}}{{#pf:a}}}}')
    assert (
        '{{t1\n    | 1 = {{t2}}{{#pf:\n        a\n    }}\n}}'
    ) == wt.pformat()


def test_html_tag_equal():
    wt = parse('{{#iferror:<t a="">|yes|no}}')
    assert (
        '{{#iferror:\n    <t a="">\n    | yes\n    | no\n}}'
    ) == wt.pformat()


def test_pformat_tl_directly():
    assert ('{{t\n    | 1 = a\n}}') == Template('{{t|a}}').pformat()


def test_pformat_pf_directly():
    assert (
        '{{#iferror:\n    <t a="">\n    | yes\n    | no\n}}'
    ) == ParserFunction('{{#iferror:<t a="">|yes|no}}').pformat()


def test_function_inside_template():
    p = parse('{{t|{{#ifeq:||yes}}|a2}}')
    assert (
        '{{t\n'
        '    | 1 = {{#ifeq:\n'
        '        \n'
        '        | \n'
        '        | yes\n'
        '    }}\n'
        '    | 2 = a2\n'
        '}}'
    ) == p.pformat()


def test_parser_template_parser():
    p = parse('{{#f:c|e|{{t|a={{#g:b|c}}}}}}')
    assert (
        '{{#f:\n'
        '    c\n'
        '    | e\n'
        '    | {{t\n'
        '        | a = {{#g:\n'
        '            b\n'
        '            | c\n'
        '        }}\n'
        '    }}\n'
        '}}'
    ) == p.pformat()


def test_pfromat_first_arg_of_functions():
    assert (
        '{{#time:\n    {{#if:\n        1\n        | y\n        | \n    }}\n}}'
    ) == parse('{{#time:{{#if:1|y|}}}}').pformat()


def test_pformat_pf_whitespace():
    assert ('{{#if:\n    a\n}}') == parse('{{#if: a}}').pformat()
    assert ('{{#if:\n    a\n}}') == parse('{{#if:a }}').pformat()
    assert ('{{#if:\n    a\n}}') == parse('{{#if: a }}').pformat()
    assert ('{{#if:\n    a= b\n}}') == parse('{{#if: a= b }}').pformat()
    assert ('{{#if:\n    a = b\n}}') == parse('{{#if:a = b }}').pformat()


def test_pformat_tl_whitespace():
    assert '{{t}}' == parse('{{ t }}').pformat()
    assert ('{{ {{t}} \n    | a = b\n}}') == parse('{{ {{t}}|a=b}}').pformat()


def test_zwnj_is_not_whitespace():
    assert ('{{#if:\n    \u200c\n}}') == parse('{{#if:\u200c}}').pformat()


def test_colon_in_tl_name():
    assert ('{{en:text\n    |text<!--\n-->}}') == parse(
        '{{en:text|text}}'
    ).pformat()
    assert ('{{en:text\n    |1<!--\n -->|2<!--\n-->}}') == parse(
        '{{en:text|1|2}}'
    ).pformat()
    assert ('{{en:text\n    |1<!--\n -->| 2=v <!--\n-->}}') == parse(
        '{{en:text|1|2=v}}'
    ).pformat()


def test_parser_function_with_an_empty_argument():
    """The result might seem a little odd, but this is a very rare case.

    The code could benefit from a little improvement.
    """
    assert ('{{#rel2abs:\n    \n}}') == parse('{{ #rel2abs: }}').pformat()


def test_parser_function_with_no_args():
    assert ParserFunction('{{FULLPAGENAMEE}}').pformat() == '{{FULLPAGENAMEE}}'


def test_pf_one_kw_arg():
    assert ('{{#expr:\n    2  =   3\n}}') == parse(
        '{{#expr: 2  =   3}}'
    ).pformat()


def test_pformat_inner_template():
    a, b, c = WikiText('{{a|{{b|{{c}}}}}}').templates
    assert ('{{b\n    | 1 = {{c}}\n}}') == b.pformat()


def test_repformat():
    """Make sure that pformat won't mutate self."""
    s = '{{a|{{b|{{c}}}}}}'
    a, b, c = WikiText(s).templates
    assert '{{a\n    | 1 = {{b\n        | 1 = {{c}}\n    }}\n}}' == a.pformat()
    # Again:
    assert '{{a\n    | 1 = {{b\n        | 1 = {{c}}\n    }}\n}}' == a.pformat()


def test_pformat_keep_separated():
    """Test that `{{ {{t}} }}` is not converted to `{{{{t}}}}`.

    `{{{{t}}}}` will be interpreted as a parameter with {} around it.

    """
    assert '{{ {{t}} }}' == WikiText('{{{{t}} }}').pformat()


def test_last_arg_last_char_is_newline():
    """Do not add comment_indent when it has no effect."""
    assert (
        '{{text\n    |{{#if:\n        \n    }}\n}}'
        == WikiText('{{text|{{#if:}}\n}}').pformat()
    )
    assert (
        '{{text\n'
        '    |{{text\n'
        '        |{{#if:\n'
        '            \n'
        '        }}\n'
        '<!--\n'
        ' -->}}\n'
        '}}'
    ) == WikiText('{{text|{{text|{{#if:}}\n}}\n}}').pformat()
    assert (
        '{{text\n'
        '    |{{text\n'
        '        |{{#if:\n'
        '            \n'
        '        }}\n'
        '    }}\n'
        '}}'
    ) == WikiText('{{text|{{text|{{#if:}}\n    }}\n}}').pformat()
    assert (
        '{{text\n    |a\n    |b\n}}'
        == WikiText('{{text|a\n    |b\n}}').pformat()
    )
    assert (
        '{{text\n    |a\n    | 2 = b\n}}'
        == WikiText('{{text|a\n    |2=b\n}}').pformat()
    )
    assert ('{{en:text\n    | n=v\n}}') == parse('{{en:text|n=v\n}}').pformat()


def test_no_error():
    # the errors were actually found in shrink/insert/extend
    assert parse('{{#f1:{{#f2:}}{{t|}}}}').pformat() == (
        '{{#f1:\n    {{#f2:\n        \n    }}{{t\n        | 1 = \n    }}\n}}'
    )
    assert parse('{{{{#t2:{{{p1|}}}}}{{#t3:{{{p2|}}}\n}}}}\n').pformat() == (
        '{{ {{#t2:'
        '\n        {{{p1|}}}'
        '\n    }}{{#t3:'
        '\n        {{{p2|}}}'
        '\n    }} }}'
        '\n'
    )


def test_after_section_title_deletion():  # 100
    section = parse('= t =\nc').sections[1]
    del section.title
    assert section.pformat() == 'c'

    section = parse('l\n= t =\nc').sections[1]
    del section.title
    assert section.pformat() == 'c'


def test_mutated_template():
    t = parse('{{t|a}}').templates[0]
    a = t.arguments[0]
    a.string = ''
    assert t.pformat() == '{{t}}'


def test_pprint_after_getting_subsections():  # 101
    s = '\n==a==\n1\n===b===\n2'
    a = parse(s).get_sections(level=2)[0]
    a.get_sections()
    a_string = s[1:]
    assert a.plain_text() == a_string
