"""Test the Argument class."""


from unittest import TestCase, main

from wikitextparser import Comment, Bold, Italic
from tests import ae


class CommentTest(TestCase):

    @staticmethod
    def test_basic():
        c = Comment('<!-- c -->')
        ae(repr(c), "Comment('<!-- c -->')")
        ae(c.comments, [])


class TestBold(TestCase):

    def test_bold(self):
        ae(Bold("'''b'''").text, 'b')
        ae(Bold("'<!---->''b'''").text, 'b')


class TestItalic(TestCase):

    def test_bold(self):
        ae(Italic("'''''i'''''").text, "'''i'''")
        ae(Italic("''i<!---->'<!---->'").text, "i<!---->")


if __name__ == '__main__':
    main()
