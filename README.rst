.. image:: https://travis-ci.org/5j9/wikitextparser.svg?branch=master
    :target: https://travis-ci.org/5j9/wikitextparser
.. image:: https://codecov.io/github/5j9/wikitextparser/coverage.svg?branch=master
    :target: https://codecov.io/github/5j9/wikitextparser

==============
WikiTextParser
==============

A simple to use WikiText parsing library for `MediaWiki <https://www.mediawiki.org/wiki/MediaWiki>`_.

The purpose is to allow users easily extract and/or manipulate templates, template parameters, parser functions, tables, external links, wikilinks, etc. found in wikitexts.

WikiTextParser currently only supports Python 3.3+

Installation
============

``pip install wikitextparser``

Usage
=====

Here is a short demo of some of the functionalities:

.. code:: python

    >>> import wikitextparser as wtp

WikiTextParser can detect sections, parserfunctions, templates, wikilinks, external links, arguments, tables, and HTML comments in your wikitext:

.. code:: python

    >>> wt = wtp.parse("""
    == h2 ==
    t2

    === h3 ===
    t3

    == h22 ==
    t22

    {{text|value1{{text|value2}}}}

    [[A|B]]""")
    >>> 
    >>> wt.templates
    [Template('{{text|value2}}'), Template('{{text|value1{{text|value2}}}}')]
    >>> wt.templates[1].arguments
    [Argument("|value1{{text|value2}}")]
    >>> wt.templates[1].arguments[0].value = 'value3'
    >>> print(wt)

    == h2 ==
    t2

    === h3 ===
    t3

    == h22 ==
    t22

    {{text|value3}}

    [[A|B]]

It provides easy-to-use properties so you can get or set names or values of templates, arguments, wikilinks, etc.:

.. code:: python

    >>> wt.wikilinks
    [WikiLink("[[A|B]]")]
    >>> wt.wikilinks[0].target = 'Z'
    >>> wt.wikilinks[0].text = 'X'
    >>> wt.wikilinks[0]
    WikiLink('[[Z|X]]')
    >>> 
    >>> from pprint import pprint
    >>> pprint(wt.sections)
    [Section('\n'),
     Section('== h2 ==\nt2\n\n=== h3 ===\nt3\n\n'),
     Section('=== h3 ===\nt3\n\n'),
     Section('== h22 ==\nt22\n\n{{text|value3}}\n\n[[Z|X]]')]
    >>> 
    >>> wt.sections[1].title = 'newtitle'
    >>> print(wt)

    ==newtitle==
    t2

    === h3 ===
    t3

    == h22 ==
    t22

    {{text|value3}}

    [[Z|X]]


There is a pprint function that pretty-prints templates:

.. code:: python

    >>> p = wtp.parse('{{t1 |b=b|c=c| d={{t2|e=e|f=f}} }}')
    >>> t2, t1 = p.templates
    >>> print(t2.pprint())
    {{t2
        | e = e
        | f = f
    }}
    >>> print(t1.pprint())
    {{t1
        | b = b
        | c = c
        | d = {{t2
            | e = e
            | f = f
        }}
    }}
    
If you are dealing with `[[Category:Pages using duplicate arguments in template calls]] <https://en.wikipedia.org/wiki/Category:Pages_using_duplicate_arguments_in_template_calls>`_ there are two functions that may be helpful:

.. code:: python

    >>> t = wtp.Template('{{t|a=a|a=b|a=a}}')
    >>> t.rm_dup_args_safe()
    >>> t
    Template('{{t|a=b|a=a}}')
    >>> t = wtp.Template('{{t|a=a|a=b|a=a}}')
    >>> t.rm_first_of_dup_args()
    >>> t
    Template('{{t|a=a}}')

Extracting cell values of a table is easy:

.. code:: python

    >>> p = wtp.parse("""{|
    |  Orange    ||   Apple   ||   more
    |-
    |   Bread    ||   Pie     ||   more
    |-
    |   Butter   || Ice cream ||  and more
    |}""")
    >>> pprint(p.tables[0].data())
    [['Orange', 'Apple', 'more'],
     ['Bread', 'Pie', 'more'],
     ['Butter', 'Ice cream', 'and more']]

And values are rearranged according to colspan and rowspan attributes (by default):

.. code:: python

    >>> t = wtp.Table("""{| class="wikitable sortable"
    |-
    ! a !! b !! c
    |-
    !colspan = "2" | d || e
    |-
    |}""")
    >>> t.data(span=True)
    [['a', 'b', 'c'], ['d', 'd', 'e']]

By calling the ``cells`` method of a ``Table``, you can access table cells as ``Cell`` objects which provide methods for getting or setting each cell's attributes and values individually.

.. code:: python

    >>> cell = t.cells(row=1, column=1)
    >>> cell.attrs
    {'colspan': '2'}
    >>> cell.set('colspan', '3')
    >>> print(t.string)
    {| class="wikitable sortable"
    |-
    ! a !! b !! c
    |-
    !colspan = "3" | d || e
    |-
    |}

You can access HTML attributes of Tag, Table, and Cell instances using
`get_attr`, `set_attr`, `has_attr`, and  `del_atrr` methods.



Have a look at the test modules for more examples and probable pitfalls.

Compared with mwparserfromhell
==============================
`mwparserfromhell <https://github.com/earwig/mwparserfromhell>`_ is a mature and widely used library with nearly the same purposes as `wikitextparser`. The main reason leading me to create `wikitextparser` was that `mwparserfromhell` could not parse wikitext in certain situations that I needed it for. See mwparserfromhell's issues `40 <https://github.com/earwig/mwparserfromhell/issues/40>`_, `42 <https://github.com/earwig/mwparserfromhell/issues/42>`_, `88 <https://github.com/earwig/mwparserfromhell/issues/88>`_, and other related issues. In many of those situation `wikitextparser` may be able to give you more acceptable results.

But if you need to

* use Python 2
* parse style tags like `'''bold'''` and ''italics'' (with some `limitations <https://github.com/earwig/mwparserfromhell#caveats>`_ of-course)
* extract `HTML tags <https://mwparserfromhell.readthedocs.io/en/latest/api/mwparserfromhell.nodes.html#module-mwparserfromhell.nodes.tag>`_ or `entities <https://mwparserfromhell.readthedocs.io/en/latest/api/mwparserfromhell.nodes.html#module-mwparserfromhell.nodes.html_entity>`_

then `mwparserfromhell` or maybe other libraries will be the way to go. Also note that `wikitextparser` is still under heavy development and the API may change drastically in the future versions.

Adding some of the features above is planned for the future...

Of-course `wikitextparser` has its own unique features, too: Providing access to individual cells of each table, pretty-printing templates, and a few other advanced functions.

I have not rigorously compared the two libraries in terms of performance, i.e. execution time and memory usage, but in my limited experience, `wikitextparser` has a decent performance even though some critical parts of `mwparserfromhell` (the tokenizer) are written in C. I guess `wikitextparser` should be able to compete and even have some performance benefits in many situations. Note that `wikitextparser` does not try to create a complete parse tree, instead tries to figure things out as the user requests for them.
However if you are working with on-line data, any difference is usually negligible as the main bottleneck will be the network latency.
