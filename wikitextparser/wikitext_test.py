﻿"""Test the functions of wikitext.py module."""


import unittest

from wikitextparser import WikiText, parse, Template, ParserFunction


class TestWikiText(unittest.TestCase):

    """Test basic functionalities of the WikiText class."""

    def test_len(self):
        t2, t1 = WikiText('{{t1|{{t2}}}}').templates
        self.assertEqual(len(t2), 6)
        self.assertEqual(len(t1), 13)

    def test_repr(self):
        self.assertEqual(repr(parse('')), "WikiText('')")

    def test_getitem(self):
        s = '{{t1|{{t2}}}}'
        t2, t1 = WikiText(s).templates
        self.assertEqual(t2[2], 't')
        self.assertEqual(t2[2:4], 't2')
        self.assertEqual(t2[-4:-2], 't2')
        self.assertEqual(t2[-3], '2')

    def test_setitem(self):
        s = '{{t1|{{t2}}}}'
        wt = WikiText(s)
        t2, t1 = wt.templates
        t2[2] = 'a'
        self.assertEqual(t2.string, '{{a2}}')
        self.assertEqual(t1.string, '{{t1|{{a2}}}}')
        t2[2] = 'bb'
        self.assertEqual(t2.string, '{{bb2}}')
        self.assertEqual(t1.string, '{{t1|{{bb2}}}}')
        t2[2:5] = 'ccc'
        self.assertEqual(t2.string, '{{ccc}}')
        self.assertEqual(t1.string, '{{t1|{{ccc}}}}')
        t2[-5:-2] = 'd'
        self.assertEqual(wt.string, '{{t1|{{d}}}}')
        t2[-3] = 'e'
        self.assertEqual(wt.string, '{{t1|{{e}}}}')

    def test_setitem_errors(self):
        w = WikiText('a')
        self.assertRaises(IndexError, w.__setitem__, -2, 'b')
        self.assertEqual('a', w[-9:9])
        self.assertRaises(IndexError, w.__setitem__, 1, 'c')
        self.assertRaises(
            NotImplementedError, w.__setitem__, slice(0, 1, 1), 'd'
        )
        self.assertEqual('a', w[-1:])
        self.assertRaises(IndexError, w.__setitem__, slice(-2, None), 'e')
        # stop is out of range
        self.assertRaises(IndexError, w.__setitem__, slice(0, -2), 'f')
        w[0] = 'gg'
        w[1] = 'hh'
        self.assertEqual(w.string, 'ghh')
        # stop and start in range but stop is before start
        self.assertRaises(IndexError, w.__setitem__, slice(1, 0), 'h')

    def test_insert(self):
        w = WikiText('c')
        w.insert(0, 'a')
        self.assertEqual(w.string, 'ac')
        # Just to show that ``w.insert(i, s)`` is the same as ``w[i:i] = s``:
        v = WikiText('c')
        v[0:0] = 'a'
        self.assertEqual(w.string, v.string)
        w.insert(-1, 'b')
        self.assertEqual(w.string, 'abc')
        # Like list.insert, w.insert accepts out of range indexes.
        w.insert(5, 'd')
        self.assertEqual(w.string, 'abcd')
        w.insert(-5, 'z')
        self.assertEqual(w.string, 'zabcd')

    def test_overwriting_template_args(self):
        t = Template('{{t|a|b|c}}')
        c = t.arguments[-1]
        self.assertEqual('|c', c.string)
        t.string = '{{t|0|a|b|c}}'
        self.assertEqual('', c.string)
        self.assertEqual('0', t.get_arg('1').value)
        self.assertEqual('c', t.get_arg('4').value)

    def test_delitem(self):
        s = '{{t1|{{t2}}}}'
        wt = WikiText(s)
        t2, t1 = wt.templates
        del t2[3]
        self.assertEqual(wt.string, '{{t1|{{t}}}}')
        del wt[5:10]
        self.assertEqual(t1.string, '{{t1|}}')
        self.assertEqual(t2.string, '')


class Contains(unittest.TestCase):

    """Test the __contains__ method of the WikiText class."""

    def test_a_is_actually_in_b(self):
        s = '{{b|{{a}}}}'
        a, b = WikiText(s).templates
        self.assertTrue(a in b)
        self.assertFalse(b in a)

    def test_a_seems_to_be_in_b_but_in_another_span(self):
        s = '{{b|{{a}}}}{{a}}'
        a1, a2, b = WikiText(s).templates
        self.assertTrue(a1 in b)
        self.assertFalse(a2 in b)
        self.assertFalse(a2 in a1)
        self.assertFalse(a1 in a2)

    def test_a_b_from_different_objects(self):
        s = '{{b|{{a}}}}'
        a1, b1 = WikiText(s).templates
        a2, b2 = WikiText(s).templates
        self.assertTrue(a1 in b1)
        self.assertTrue(a2 in b2)
        self.assertFalse(a2 in b1)
        self.assertFalse(a1 in b2)
        self.assertTrue('{{a}}' in b1)
        self.assertFalse('{{c}}' in b2)


class ShrinkSpanUpdate(unittest.TestCase):

    """Test the _shrink_span_update method."""

    def test_stripping_template_name_should_update_its_arg_spans(self):
        t = Template('{{ t\n |1=2}}')
        a = t.arguments[0]
        t.name = t.name.strip()
        self.assertEqual('|1=2', a.string)

    def test_opcodes_in_spans_should_be_referenced_based_on_self_lststr0(self):
        wt = WikiText('{{a}}{{ b\n|d=}}')
        template = wt.templates[1]
        arg = template.arguments[0]
        template.name = template.name.strip()
        self.assertEqual('|d=', arg.string)

    def test_rmstart_s__rmstop__e(self):
        wt = WikiText('{{t|<!--c-->}}')
        c = wt.comments[0]
        t = wt.templates[0]
        t[3:8] = ''
        self.assertEqual(c.string, 'c-->')


class ExpandSpanUpdate(unittest.TestCase):

    """Test the _expand_span_update method."""

    def test_extending_template_name_should_not_effect_arg_string(self):
        t = Template('{{t|1=2}}')
        a = t.arguments[0]
        t.name = 't\n    '
        self.assertEqual('|1=2', a.string)

    def test_overwriting_or_extending_selfspan_will_cause_data_loss(self):
        wt = WikiText('{{t|{{#if:a|b|c}}}}')
        a = wt.templates[0].arguments[0]
        pf = wt.parser_functions[0]
        a.value += ''
        self.assertEqual('|{{#if:a|b|c}}', a.string)
        # Note that the old parser function is overwritten
        self.assertEqual('', pf.string)
        pf = a.parser_functions[0]
        a.value = 'a'
        self.assertEqual('', pf.string)


class Templates(unittest.TestCase):

    """Test WikiText.templates."""

    def test_template_inside_wikilink(self):
        wt = WikiText("{{text |  [[ A | {{text|b}} ]] }}")
        self.assertEqual(2, len(wt.templates))

    def test_wikilink_in_template(self):
        s1 = "{{text |[[A|}}]]}}"
        wt = WikiText(s1)
        self.assertEqual(s1, str(wt.templates[0]))

    def test_wikilink_containing_closing_braces_in_template(self):
        s = '{{text|[[  A   |\n|}}[]<>]]\n}}'
        wt = WikiText(s)
        self.assertEqual(s, str(wt.templates[0]))

    def test_ignore_comments(self):
        s1 = "{{text |<!-- }} -->}}"
        wt = WikiText(s1)
        self.assertEqual(s1, str(wt.templates[0]))

    def test_ignore_nowiki(self):
        wt = WikiText("{{text |<nowiki>}} A </nowiki> }} B")
        self.assertEqual(
            "{{text |<nowiki>}} A </nowiki> }}",
            str(wt.templates[0])
        )

    def test_template_inside_extension_tags(self):
        s = "<includeonly>{{t}}</includeonly>"
        wt = WikiText(s)
        self.assertEqual('{{t}}', str(wt.templates[0]))

    def test_dont_parse_source_tag(self):
        s = "<source>{{t}}</source>"
        wt = WikiText(s)
        self.assertEqual(0, len(wt.templates))


class ParserFunctions(unittest.TestCase):

    """Test WikiText.parser_functions."""

    def test_comment_in_parserfunction_name(self):
        s = "{{<!--c\n}}-->#if:|a}}"
        wt = WikiText(s)
        self.assertEqual(1, len(wt.parser_functions))


class WikiLinks(unittest.TestCase):

    """Test WikiText.wikilinks."""

    def test_wikilink_inside_parser_function(self):
        wt = WikiText("{{ #if: {{{3|}}} | [[u:{{{3}}}|{{{3}}}]] }}")
        self.assertEqual("[[u:{{{3}}}|{{{3}}}]]", wt.wikilinks[0].string)

    def test_template_in_wikilink(self):
        s = '[[A|{{text|text}}]]'
        wt = WikiText(s)
        self.assertEqual(s, str(wt.wikilinks[0]))

    def test_wikilink_target_may_contain_newline(self):
        s = '[[A | faf a\n\nfads]]'
        wt = WikiText(s)
        self.assertEqual(s, str(wt.wikilinks[0]))


class Comments(unittest.TestCase):

    """Test the WikiText.commonts."""

    def test_getting_comment(self):
        wt = WikiText('text1 <!--\n\ncomment\n{{A}}\n-->text2')
        self.assertEqual(
            "\n\ncomment\n{{A}}\n",
            wt.comments[0].contents
        )


class ExternalLinks(unittest.TestCase):

    """Test the WikiText.external_links."""

    def test_bare_link(self):
        s = 'text1 HTTP://mediawiki.org text2'
        wt = WikiText(s)
        self.assertEqual(
            'HTTP://mediawiki.org',
            str(wt.external_links[0]),
        )

    def test_with_lable(self):
        s = 'text1 [http://mediawiki.org MediaWiki] text2'
        wt = WikiText(s)
        self.assertEqual(
            'http://mediawiki.org',
            wt.external_links[0].url
        )
        self.assertEqual(
            'MediaWiki',
            wt.external_links[0].text
        )

    def test_external_link_match_is_not_in_spans(self):
        wt = WikiText('t [http://b.b b] t [http://c.c c] t')
        # calculate the links
        links1 = wt.external_links
        wt.insert(0, 't [http://a.a a]')
        links2 = wt.external_links
        self.assertEqual(links1[1].string, '[http://c.c c]')
        self.assertEqual(links2[0].string, '[http://a.a a]')

    def test_numbered_link(self):
        s = 'text1 [http://mediawiki.org] text2'
        wt = WikiText(s)
        self.assertEqual(
            '[http://mediawiki.org]',
            str(wt.external_links[0]),
        )

    def test_protocol_relative(self):
        s = 'text1 [//en.wikipedia.org wikipedia] text2'
        wt = WikiText(s)
        self.assertEqual(
            '[//en.wikipedia.org wikipedia]',
            str(wt.external_links[0]),
        )

    def test_destroy(self):
        s = 'text1 [//en.wikipedia.org wikipedia] text2'
        wt = WikiText(s)
        wt.external_links[0].string = ''
        self.assertEqual(
            'text1  text2',
            str(wt),
        )

    def test_wikilink2externallink_fallback(self):
        p = parse('[[http://example.com foo bar]]')
        self.assertEqual(
            '[http://example.com foo bar]',
            p.external_links[0].string
        )
        self.assertEqual(0, len(p.wikilinks))

    @unittest.expectedFailure
    def test_no_bare_externallink_within_wikilinks(self):
        """Based on how Mediawiki behaves.

        There is a rather simple solution for this (move the detection of
        external links to spans.py) but maybe the current implementation
        is even more useful? Also it should be faster.
        """
        p = parse('[[ https://en.wikipedia.org/]]')
        self.assertEqual(1, len(p.wikilinks))
        self.assertEqual(0, len(p.external_links))

    def test_bare_extlink_must_have_scheme(self):
        """Bare external links must have scheme."""
        self.assertEqual(len(parse('//mediawiki.org').external_links), 0)

    def test_external_link_with_template(self):
        """External links may contain templates."""
        self.assertEqual(
            len(parse('http://example.com/{{text|foo}}').external_links),
            1,
        )

    @unittest.expectedFailure
    def test_external_link_may_not_contain_any_template(self):
        """Some templates won't be parsed as part of the external link."""
        self.assertEqual(
            str(parse('http://example.com/{{dead link}}').external_links),
            'http://example.com/'
        )


class Table(unittest.TestCase):

    """Test the tables property."""

    def test_table_extraction(self):
        s = '{|class=wikitable\n|a \n|}'
        p = parse(s)
        self.assertEqual(s, p.tables[0].string)

    def test_table_start_after_space(self):
        s = '   {|class=wikitable\n|a \n|}'
        p = parse(s)
        self.assertEqual(s.strip(), p.tables[0].string)

    def test_ignore_comments_before_extracting_tables(self):
        s = '{|class=wikitable\n|a \n<!-- \n|} \n-->\n|b\n|}'
        p = parse(s)
        self.assertEqual(s, p.tables[0].string)

    def test_two_tables(self):
        s = 'text1\n {|\n|a \n|}\ntext2\n{|\n|b\n|}\ntext3\n'
        p = parse(s)
        tables = p.tables
        self.assertEqual(2, len(tables))
        self.assertEqual('{|\n|a \n|}', tables[0].string)
        self.assertEqual('{|\n|b\n|}', tables[1].string)

    def test_nested_tables(self):
        s = (
            'text1\n{|class=wikitable\n|a\n|\n'
            '{|class=wikitable\n|b\n|}\n|}\ntext2'
        )
        p = parse(s)
        self.assertEqual(2, len(p.tables))
        self.assertEqual(s[6:-6], p.tables[1].string)
        self.assertEqual('{|class=wikitable\n|b\n|}', p.tables[0].string)

    def test_tables_in_different_sections(self):
        s = '{|\n| a\n|}\n\n= s =\n{|\n| b\n|}\n'
        p = parse(s).sections[1]
        self.assertEqual('{|\n| b\n|}', p.tables[0].string)

    def test_match_index_is_none(self):
        s = '{|\n| b\n|}\n'
        wt = parse(s)
        assert len(wt.tables) == 1
        wt.insert(0, '{|\n| a\n|}\n')
        tables = wt.tables
        self.assertEqual(tables[0].string, '{|\n| a\n|}')
        self.assertEqual(tables[1].string, '{|\n| b\n|}')

    def test_tables_may_be_indented(self):
        s = ' ::{|class=wikitable\n|a\n|}'
        wt = parse(s)
        self.assertEqual(wt.tables[0].string, '{|class=wikitable\n|a\n|}')

    def test_comments_before_table_start(self):
        s = ' <!-- c -->::{|class=wikitable\n|a\n|}'
        wt = parse(s)
        self.assertEqual(wt.tables[0].string, '{|class=wikitable\n|a\n|}')

    def test_comments_between_indentation(self):
        s = ':<!-- c -->:{|class=wikitable\n|a\n|}'
        wt = parse(s)
        self.assertEqual(wt.tables[0].string, '{|class=wikitable\n|a\n|}')

    def test_comments_between_indentation_after_them(self):
        s = ':<!-- c -->: <!-- c -->{|class=wikitable\n|a\n|}'
        wt = parse(s)
        self.assertEqual(wt.tables[0].string, '{|class=wikitable\n|a\n|}')

    def test_indentation_cannot_be_inside_nowiki(self):
        """A very unusual case. It would be OK to have false positives here.

        Also false positive for tables are pretty much harmless here.

        The same thing may happen for tables which start right after a
        templates, parser functions, wiki links, comments, or
        other extension tags.

        """
        s = '<nowiki>:</nowiki>{|class=wikitable\n|a\n|}'
        wt = parse(s)
        self.assertEqual(len(wt.tables), 0)

    def test_template_before_or_after_table(self):
        # This tests self._shadow function.
        s = '{{t|1}}\n{|class=wikitable\n|a\n|}\n{{t|1}}'
        p = parse(s)
        self.assertEqual([['a']], p.tables[0].data())


class IndentLevel(unittest.TestCase):

    """Test the _indent_level method of the WikiText class."""

    def test_a_in_b(self):
        s = '{{b|{{a}}}}'
        a, b = WikiText(s).templates
        self.assertEqual(1, b._indent_level)
        self.assertEqual(2, a._indent_level)


class TestPrettyPrint(unittest.TestCase):

    """Test the pformat method of the WikiText class."""

    def test_template_with_multi_args(self):
        wt = WikiText('{{a|b=b|c=c|d=d|e=e}}')
        self.assertEqual(
            '{{a\n    | b = b\n    | c = c\n    | d = d\n    | e = e\n}}',
            wt.pformat(),
        )

    def test_double_space_indent(self):
        s = "{{a|b=b|c=c|d=d|e=e}}"
        wt = WikiText(s)
        self.assertEqual(
            '{{a\n  | b = b\n  | c = c\n  | d = d\n  | e = e\n}}',
            wt.pformat('  '),
        )

    def test_remove_comments(self):
        self.assertEqual(
            '{{a\n  | e = e\n}}',
            WikiText('{{a|<!--b=b|c=c|d=d|-->e=e}}').pformat('  ', True),
        )

    def test_first_arg_of_tag_is_whitespace_sensitive(self):
        """The second argument of #tag is an exception.

        See the last warning on [[mw:Help:Magic_words#Miscellaneous]]:
        You must write {{#tag:tagname||attribute1=value1|attribute2=value2}}
        to pass an empty content. No space is permitted in the area reserved
        for content between the pipe characters || before attribute1.
        """
        s = '{{#tag:ref||name="n1"}}'
        wt = WikiText(s)
        self.assertEqual(s, wt.pformat())
        s = '{{#tag:foo| }}'
        wt = WikiText(s)
        self.assertEqual(s, wt.pformat())

    def test_invoke(self):
        """#invoke args are also whitespace-sensitive."""
        s = '{{#invoke:module|func|arg}}'
        wt = WikiText(s)
        self.assertEqual(s, wt.pformat())

    def test_on_parserfunction(self):
        s = "{{#if:c|abcde = f| g=h}}"
        wt = parse(s)
        self.assertEqual(
            '{{#if:\n'
            '    c\n'
            '    | abcde = f\n'
            '    | g=h\n'
            '}}',
            wt.pformat(),
        )

    def test_parserfunction_with_no_pos_arg(self):
        s = "{{#switch:case|a|b}}"
        wt = parse(s)
        self.assertEqual(
            '{{#switch:\n'
            '    case\n'
            '    | a\n'
            '    | b\n'
            '}}',
            wt.pformat(),
        )

    def test_convert_positional_to_keyword_if_possible(self):
        self.assertEqual(
            '{{t\n    | 1 = a\n    | 2 = b\n    | 3 = c\n}}',
            parse('{{t|a|b|c}}').pformat(),
        )

    def test_inconvertible_positionals(self):
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
        self.assertEqual(
            '{{t\n'
            '    |a<!--\n'
            ' -->| b <!--\n'
            '-->}}',
            parse('{{t|a| b }}').pformat(),
        )
        self.assertEqual(
            '{{t\n'
            '    | a <!--\n'
            ' -->| 2 = b\n'
            '    | 3 = c\n'
            '}}',
            parse('{{t| a |b|c}}').pformat(),
        )

    def test_commented_repprint(self):
        s = '{{t\n    | a <!--\n -->| 2 = b\n    | 3 = c\n}}'
        self.assertEqual(s, parse(s).pformat())

    def test_dont_treat_parser_function_arguments_as_kwargs(self):
        """The `=` is usually just a part of parameter value.

        Another example: {{fullurl:Category:Top level|action=edit}}.
        """
        self.assertEqual(
            '{{#if:\n'
            '    true\n'
            '    | <span style="color:Blue;">text</span>\n'
            '}}',
            parse(
                '{{#if:true|<span style="color:Blue;">text</span>}}'
            ).pformat(),
        )

    def test_ignore_zwnj_for_alignment(self):
        self.assertEqual(
            '{{ا\n    | نیم\u200cفاصله       = ۱\n    |'
            ' بدون نیم فاصله = ۲\n}}',
            parse('{{ا|نیم‌فاصله=۱|بدون نیم فاصله=۲}}').pformat(),
        )

    def test_equal_sign_alignment(self):
        self.assertEqual(
            '{{t\n'
            '    | long_argument_name = 1\n'
            '    | 2                  = 2\n'
            '}}',
            parse('{{t|long_argument_name=1|2=2}}').pformat(),
        )

    def test_arabic_ligature_lam_with_alef(self):
        """'ل' + 'ا' creates a ligature with one character width.

        Some terminal emulators do not support this but it's defined in
        Courier New font which is the main (almost only) font used for
        monospaced Persian texts on Windows. Also tested on Arabic Wikipedia.
        """
        self.assertEqual(
            '{{ا\n    | الف = ۱\n    | لا   = ۲\n}}',
            parse('{{ا|الف=۱|لا=۲}}').pformat(),
        )

    def test_pf_inside_t(self):
        wt = parse('{{t|a= {{#if:I|I}} }}')
        self.assertEqual(
            '{{t\n'
            '    | a = {{#if:\n'
            '        I\n'
            '        | I\n'
            '    }}\n'
            '}}',
            wt.pformat(),
        )

    def test_nested_pf_inside_tl(self):
        wt = parse('{{t1|{{t2}}{{#pf:a}}}}')
        self.assertEqual(
            '{{t1\n'
            '    | 1 = {{t2}}{{#pf:\n'
            '        a\n'
            '    }}\n'
            '}}',
            wt.pformat(),
        )

    def test_html_tag_equal(self):
        wt = parse('{{#iferror:<t a="">|yes|no}}')
        self.assertEqual(
            '{{#iferror:\n'
            '    <t a="">\n'
            '    | yes\n'
            '    | no\n'
            '}}',
            wt.pformat(),
        )

    def test_pprint_tl_directly(self):
        self.assertEqual(
            '{{t\n'
            '    | 1 = a\n'
            '}}',
            Template('{{t|a}}').pformat(),
        )

    def test_pprint_pf_directly(self):
        self.assertEqual(
            '{{#iferror:\n'
            '    <t a="">\n'
            '    | yes\n'
            '    | no\n'
            '}}',
            ParserFunction('{{#iferror:<t a="">|yes|no}}').pformat(),
        )

    def test_function_inside_template(self):
        p = parse('{{t|{{#ifeq:||yes}}|a2}}')
        self.assertEqual(
            '{{t\n'
            '    | 1 = {{#ifeq:\n'
            '        \n'
            '        | \n'
            '        | yes\n'
            '    }}\n'
            '    | 2 = a2\n'
            '}}',
            p.pformat(),
        )

    def test_parser_template_parser(self):
        p = parse('{{#f:c|e|{{t|a={{#g:b|c}}}}}}')
        self.assertEqual(
            '{{#f:\n'
            '    c\n'
            '    | e\n'
            '    | {{t\n'
            '        | a = {{#g:\n'
            '            b\n'
            '            | c\n'
            '        }}\n'
            '    }}\n'
            '}}',
            p.pformat(),
        )

    def test_pprint_first_arg_of_functions(self):
        self.assertEqual(
            '{{#time:\n'
            '    {{#if:\n'
            '        1\n'
            '        | y\n'
            '        | \n'
            '    }}\n'
            '}}',
            parse('{{#time:{{#if:1|y|}}}}').pformat(),
        )

    def test_colon_in_tl_name(self):
        self.assertEqual(
            '{{en:text\n'
            '    |text<!--\n'
            '-->}}',
            parse('{{en:text|text}}').pformat(),
        )
        self.assertEqual(
            '{{en:text\n'
            '    | n=v <!--\n'
            '-->}}',
            parse('{{en:text|n=v}}').pformat(),
        )

    def test_parser_function_with_an_empty_argument(self):
        """The result might seem a little odd, but this is a very rare case.

        The code could benefit from a little improvement.

        """
        self.assertEqual(
            '{{ #rel2abs:\n'
            '    \n'
            '}}',
            parse('{{ #rel2abs: }}').pformat(),
        )

    def test_pf_one_kw_arg(self):
        self.assertEqual(
            '{{#expr:\n'
            '    2  =   3\n'
            '}}',
            parse('{{#expr: 2  =   3}}').pformat(),
        )

    def test_pprint_inner_template(self):
        c, b, a = WikiText('{{a|{{b|{{c}}}}}}').templates
        self.assertEqual(
            '{{b\n'
            '    | 1 = {{c}}\n'
            '}}',
            b.pformat(),
        )

    def test_repprint(self):
        """Make sure that pformat won't mutate self."""
        s = '{{a|{{b|{{c}}}}}}'
        c, b, a = WikiText(s).templates
        self.assertEqual(
            '{{a\n    | 1 = {{b\n        | 1 = {{c}}\n    }}\n}}',
            a.pformat(),
        )
        # Again:
        self.assertEqual(
            '{{a\n    | 1 = {{b\n        | 1 = {{c}}\n    }}\n}}',
            a.pformat(),
        )

    def test_pprint_keep_separated(self):
        """Test that `{{ {{t}} }}` is not converted to `{{{{t}}}}`.

        `{{{{t}}}}` will be interpreted as a parameter with {} around it.

        """
        self.assertEqual('{{ {{t}} }}', WikiText('{{{{t}} }}').pformat())


class Sections(unittest.TestCase):

    """Test the sections method of the WikiText class."""

    def test_grab_the_final_newline_for_the_last_section(self):
        wt = WikiText('== s ==\nc\n')
        self.assertEqual('== s ==\nc\n', wt.sections[1].string)

    def test_blank_lead(self):
        wt = WikiText('== s ==\nc\n')
        self.assertEqual('== s ==\nc\n', wt.sections[1].string)

    # Todo: Parser should also work with windows line endings.
    @unittest.expectedFailure
    def test_multiline_with_carriage_return(self):
        s = 'text\r\n= s =\r\n{|\r\n| a \r\n|}\r\ntext'
        p = parse(s)
        self.assertEqual('text\r\n', p.sections[0].string)

    def test_inseting_into_sections(self):
        wt = WikiText('== s1 ==\nc\n')
        s1 = wt.sections[1]
        s1.insert(0, 'c\n== s0 ==\nc\n')
        s0 = wt.sections[1]
        self.assertEqual('c\n== s0 ==\nc\n== s1 ==\nc\n', s1.string)
        self.assertEqual('== s0 ==\nc\n', s0.string)
        self.assertEqual('c\n== s0 ==\nc\n== s1 ==\nc\n', wt.string)
        s1.insert(len(wt.string), '=== s2 ===\nc\n')
        self.assertEqual(
            'c\n'
            '== s0 ==\n'
            'c\n'
            '== s1 ==\n'
            'c\n'
            '=== s2 ===\n'
            'c\n',
            wt.string
        )
        s3 = wt.sections[3]
        self.assertEqual('=== s2 ===\nc\n', s3.string)

    def test_insert_parse(self):
        """Test that insert parses the inserted part."""
        wt = WikiText('')
        wt.insert(0, '{{t}}')
        self.assertEqual(len(wt.templates), 1)


class WikiList(unittest.TestCase):

    def test_get_lists_with_no_pattern(self):
        wikitext = '*a\n#b\n;c:d'
        parsed = parse(wikitext)
        lists = parsed.lists()
        self.assertEqual(len(lists), 3)
        self.assertEqual(lists[2].items, ['c', 'd'])


class Tags(unittest.TestCase):

    def test_unicode_attr_values(self):
        wikitext = (
            'متن۱<ref name="نام۱" group="گ">یاد۱</ref>\n\n'
            'متن۲<ref name="نام۲" group="گ">یاد۲</ref>\n\n'
            '<references group="گ"/>'
        )
        parsed = parse(wikitext)
        ref1, ref2 = parsed.tags('ref')
        self.assertEqual(ref1.string, '<ref name="نام۱" group="گ">یاد۱</ref>')
        self.assertEqual(ref2.string, '<ref name="نام۲" group="گ">یاد۲</ref>')

    def test_defferent_nested_tags(self):
        parsed = parse('<s><b>strikethrough-bold</b></s>')
        b = parsed.tags('b')[0].string
        self.assertEqual(b, '<b>strikethrough-bold</b>')
        s = parsed.tags('s')[0].string
        self.assertEqual(s, '<s><b>strikethrough-bold</b></s>')
        refs = parsed.tags()
        self.assertEqual(refs[0].string, b)
        self.assertEqual(refs[1].string, s)

    def test_same_nested_tags(self):
        parsed = parse('<b><b>bold</b></b>')
        tags_by_name = parsed.tags('b')
        self.assertEqual(tags_by_name[1].string, '<b><b>bold</b></b>')
        self.assertEqual(tags_by_name[0].string, '<b>bold</b>')
        all_tags = parsed.tags()
        self.assertEqual(all_tags[0].string, tags_by_name[0].string)
        self.assertEqual(all_tags[1].string, tags_by_name[1].string)

    def test_self_closing(self):
        parsed = parse('<references />')
        tags = parsed.tags()
        self.assertEqual(tags[0].string, '<references />')

    def test_start_only(self):
        """Some elements' end tag may be omitted in certain conditions.

        An li element’s end tag may be omitted if the li element is immediately
        followed by another li element or if there is no more content in the
        parent element.

        See: https://www.w3.org/TR/html51/syntax.html#optional-tags

        """
        parsed = parse('<li>')
        tags = parsed.tags()
        self.assertEqual(tags[0].string, '<li>')

    def test_inner_tag(self):
        parsed = parse('<br><s><b>sb</b></s>')
        s = parsed.tags('s')[0]
        self.assertEqual(s.string, '<s><b>sb</b></s>')
        b = s.tags()[0]
        self.assertEqual(b.string, '<b>sb</b>')

    def test_extension_tags_are_not_lost_in_shadows(self):
        parsed = parse(
            'text<ref name="c">citation</ref>\n'
            '<references/>'
        )
        ref, references = parsed.tags()
        ref.set_attr('name', 'z')
        self.assertEqual(ref.string, '<ref name="z">citation</ref>')
        self.assertEqual(references.string, '<references/>')


if __name__ == '__main__':
    unittest.main()
