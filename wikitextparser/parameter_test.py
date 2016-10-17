"""Test the parameters.py module."""


import unittest

import wikitextparser as wtp


class Parameter(unittest.TestCase):

    """The parameters test class."""

    def test_basic(self):
        p = wtp.Parameter('{{{P}}}')
        self.assertEqual('P', p.name)
        self.assertEqual('', p.pipe)
        self.assertEqual(None, p.default)
        p = wtp.Parameter('{{{P|}}}')
        self.assertEqual('', p.default)
        p.name = ' Q '
        self.assertEqual('{{{ Q |}}}', p.string)
        p = wtp.Parameter('{{{P|D}}}')
        self.assertEqual('P', p.name)
        self.assertEqual('|', p.pipe)
        self.assertEqual('D', p.default)
        p.name = ' Q '
        self.assertEqual('{{{ Q |D}}}', p.string)
        p.default = ' V '
        self.assertEqual("Parameter('{{{ Q | V }}}')", repr(p))

    def test_default_setter(self):
        # The default is not None
        p = wtp.Parameter('{{{ Q |}}}')
        p.default = ' V '
        self.assertEqual('{{{ Q | V }}}', p.string)
        # The default is None
        p = wtp.Parameter('{{{ Q }}}')
        p.default = ' V '
        self.assertEqual('{{{ Q | V }}}', p.string)

    def test_appending_default(self):
        p = wtp.Parameter('{{{p1|{{{p2|}}}}}}')
        p.append_default('p3')
        self.assertEqual('{{{p1|{{{p2|{{{p3|}}}}}}}}}', p.string)
        # What happens if we try it again
        p.append_default('p4')
        self.assertEqual('{{{p1|{{{p2|{{{p3|{{{p4|}}}}}}}}}}}}', p.string)
        # Appending to and inner parameter without default
        p = wtp.Parameter('{{{p1|{{{p2}}}}}}')
        p.append_default('p3')
        self.assertEqual('{{{p1|{{{p2|{{{p3}}}}}}}}}', p.string)
        # Don't change and inner parameter which is not a default
        p = wtp.Parameter('{{{p1|head {{{p2}}} tail}}}')
        p.append_default('p3')
        self.assertEqual('{{{p1|{{{p3|head {{{p2}}} tail}}}}}}', p.string)
        # Appending to parameter with no default
        p = wtp.Parameter('{{{p1}}}')
        p.append_default('p3')
        self.assertEqual('{{{p1|{{{p3}}}}}}', p.string)
        # Preserve whitespace
        p = wtp.Parameter('{{{ p1 |{{{ p2 | }}}}}}')
        p.append_default(' p3 ')
        self.assertEqual('{{{ p1 |{{{ p2 |{{{ p3 | }}}}}}}}}', p.string)
        # White space before or after a prameter makes it a value (not default)
        p = wtp.Parameter('{{{ p1 | {{{ p2 | }}} }}}')
        p.append_default(' p3 ')
        self.assertEqual('{{{ p1 |{{{ p3 | {{{ p2 | }}} }}}}}}', p.string)
        # If the parameter already exists among defaults, it won't be added.
        p = wtp.Parameter('{{{p1|{{{p2|}}}}}}')
        p.append_default('p1')
        self.assertEqual('{{{p1|{{{p2|}}}}}}', p.string)
        p.append_default('p2')
        self.assertEqual('{{{p1|{{{p2|}}}}}}', p.string)


if __name__ == '__main__':
    unittest.main()
