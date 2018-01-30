"""Test the Argument class."""


import unittest

import wikitextparser as wtp


class Comment(unittest.TestCase):

    """Argument test class."""

    def test_basic(self):
        c = wtp.Comment('<!-- c -->')
        self.assertEqual(repr(c), "Comment('<!-- c -->')")


if __name__ == '__main__':
    unittest.main()
