import unittest

import list_parser


@unittest.expectedFailure
class Spans(unittest.TestCase):
    """Test the spans."""

    def test_common_cases(self):
        """A few basic examples from [[mw:Help:Lists]]."""
        o = p.do_block_levels(
            '* Lists are easy to do:\n'
            '** start every line\n'
            '* with a star\n'
            '** more stars mean\n'
            '*** deeper levels',
            True
        )
        self.assertEqual(
            '<ul><li> Lists are easy to do:\n<ul><li> start every line</li></ul></li>\n<li> with a star\n<ul><li> more stars mean\n<ul><li> deeper levels</li></ul></li></ul></li></ul>\n',
            o
        )
        o = p.do_block_levels(
            '#list item A1\n'
            '##list item B1\n'
            '##list item B2\n'
            '#:continuing list item A1\n'
            '#list item A2',
            True
        )
        self.assertEqual(
            '<ol><li>list item A1\n<ol><li>list item B1</li>\n<li>list item B2</li></ol>\n<dl><dd>continuing list item A1</dd></dl></li>\n<li>list item A2</li></ol>\n',
            o
        )

    def test_commented_list_item(self):
        """One of the list items is commented through the wikitext."""
        o = p.do_block_levels(
            '#one\n'
            '##one-one\n'
            '##one-two<!-- \n'
            '##one-three\n'
            ' -->\n'
            '#two',
            True
        )
        self.assertEqual(
            '<ol>\n<li>one\n<ol>\n<li>one-one</li>\n'
            '<li>one-two</li>\n</ol>\n</li>\n<li>two</li>\n</ol>',
            o
        )


if __name__ == '__main__':
    p = list_parser.ListParser()
    unittest.main()
