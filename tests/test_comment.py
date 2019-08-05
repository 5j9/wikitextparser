"""Test the Argument class."""


from unittest import TestCase, main

from wikitextparser import Comment


class CommentTest(TestCase):

    """Argument test class."""

    def test_basic(self):
        ae = self.assertEqual
        c = Comment('<!-- c -->')
        ae(repr(c), "Comment('<!-- c -->')")
        ae(c.comments, [])


if __name__ == '__main__':
    main()
