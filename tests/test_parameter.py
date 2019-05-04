"""Test the parameters.py module."""


from unittest import TestCase, main

from wikitextparser import Parameter


class ParameterTest(TestCase):

    """The parameters test class."""

    def test_basic(self):
        ae = self.assertEqual
        p = Parameter('{{{P}}}')
        ae('P', p.name)
        ae('', p.pipe)
        ae(None, p.default)
        p.name = 'Q'
        ae('Q', p.name)

        p = Parameter('{{{P|}}}')
        ae('', p.default)
        p.name = ' Q '
        ae('{{{ Q |}}}', p.string)

        p = Parameter('{{{P|D}}}')
        ae('P', p.name)
        ae('|', p.pipe)
        ae('D', p.default)
        p.name = ' Q '
        ae('{{{ Q |D}}}', p.string)
        p.default = ' V '
        ae("Parameter('{{{ Q | V }}}')", repr(p))

    def test_default_setter(self):
        ae = self.assertEqual
        # The default is not None
        p = Parameter('{{{ Q |}}}')
        p.default = ' V '
        ae('{{{ Q | V }}}', p.string)
        # The default is None
        p = Parameter('{{{ Q }}}')
        p.default = ' V '
        ae('{{{ Q | V }}}', p.string)
        p.default = ''
        ae('{{{ Q |}}}', p.string)
        with self.assertWarns(DeprecationWarning):
            p.default = None
        ae('{{{ Q }}}', p.string)
        # Setting default to None when it is already None
        with self.assertWarns(DeprecationWarning):
            p.default = None
        ae('{{{ Q }}}', p.string)

    def test_appending_default(self):
        ae = self.assertEqual
        p = Parameter('{{{p1|{{{p2|}}}}}}')
        p.append_default('p3')
        ae('{{{p1|{{{p2|{{{p3|}}}}}}}}}', p.string)
        # What happens if we try it again
        p.append_default('p4')
        ae('{{{p1|{{{p2|{{{p3|{{{p4|}}}}}}}}}}}}', p.string)
        # Appending to and inner parameter without default
        p = Parameter('{{{p1|{{{p2}}}}}}')
        p.append_default('p3')
        ae('{{{p1|{{{p2|{{{p3}}}}}}}}}', p.string)
        # Don't change and inner parameter which is not a default
        p = Parameter('{{{p1|head {{{p2}}} tail}}}')
        p.append_default('p3')
        ae('{{{p1|{{{p3|head {{{p2}}} tail}}}}}}', p.string)
        # Appending to parameter with no default
        p = Parameter('{{{p1}}}')
        p.append_default('p3')
        ae('{{{p1|{{{p3}}}}}}', p.string)
        # Preserve whitespace
        p = Parameter('{{{ p1 |{{{ p2 | }}}}}}')
        p.append_default(' p3 ')
        ae('{{{ p1 |{{{ p2 |{{{ p3 | }}}}}}}}}', p.string)
        # White space before or after a prameter makes it a value (not default)
        p = Parameter('{{{ p1 | {{{ p2 | }}} }}}')
        p.append_default(' p3 ')
        ae('{{{ p1 |{{{ p3 | {{{ p2 | }}} }}}}}}', p.string)
        # If the parameter already exists among defaults, it won't be added.
        p = Parameter('{{{p1|{{{p2|}}}}}}')
        p.append_default('p1')
        ae('{{{p1|{{{p2|}}}}}}', p.string)
        p.append_default('p2')
        ae('{{{p1|{{{p2|}}}}}}', p.string)

    def test_ignore_comment_pipes(self):
        ae = self.assertEqual
        # name
        p = Parameter('{{{1<!-- |comment| -->|text}}}')
        ae(p.name, '1<!-- |comment| -->')
        # name.setter
        p.name = '2<!-- |comment| -->'
        ae(p.name, '2<!-- |comment| -->')
        # default
        ae(p.default, 'text')
        # default.setter
        p.default = 'default'
        ae(p.string, '{{{2<!-- |comment| -->|default}}}')
        # pipe
        del p.default
        ae(p.string, '{{{2<!-- |comment| -->}}}')
        ae(p.pipe, '')


if __name__ == '__main__':
    main()
