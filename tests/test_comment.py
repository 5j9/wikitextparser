"""Test the Argument class."""


from unittest import TestCase, main

import wikitextparser as wtp


class Comment(TestCase):

    """Argument test class."""

    def test_basic(self):
        c = wtp.Comment('<!-- c -->')
        self.assertEqual(repr(c), "Comment('<!-- c -->')")


if __name__ == '__main__':
    main()
