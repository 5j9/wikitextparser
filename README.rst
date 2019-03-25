.. image:: https://travis-ci.org/5j9/wikitextparser.svg?branch=master
    :target: https://travis-ci.org/5j9/wikitextparser
.. image:: https://codecov.io/github/5j9/wikitextparser/coverage.svg?branch=master
    :target: https://codecov.io/github/5j9/wikitextparser
.. image:: https://readthedocs.org/projects/wikitextparser/badge/?version=latest
    :target: http://wikitextparser.readthedocs.io/en/latest/?badge=latest

==============
WikiTextParser
==============
.. Quick Start Guid

A simple to use WikiText parsing library for `MediaWiki <https://www.mediawiki.org/wiki/MediaWiki>`_.

The purpose is to allow users easily extract and/or manipulate templates, template parameters, parser functions, tables, external links, wikilinks, lists, etc. found in wikitexts.

.. contents:: Table of Contents

Installation
============

- Python 3.4+ is required
- ``pip install 'setuptools>=36.2.1'``
- ``pip install wikitextparser``

Usage
=====

.. code:: python

    >>> import wikitextparser as wtp

WikiTextParser can detect sections, parser functions, templates, wiki links, external links, arguments, tables, wiki lists, and comments in your wikitext. The following sections are quick of some of these functionalities.

You may also want to have a look at the test modules for more examples and probable pitfalls (expected failures).

Templates
---------

.. code:: python

    >>> parsed = wtp.parse("{{text|value1{{text|value2}}}}")
    >>> parsed.templates
    [Template('{{text|value1{{text|value2}}}}'), Template('{{text|value2}}')]
    >>> parsed.templates[0].arguments
    [Argument("|value1{{text|value2}}")]
    >>> parsed.templates[0].arguments[0].value = 'value3'
    >>> print(parsed)
    {{text|value3}}

The ``pformat`` method returns a pretty-print formatted string for templates:

.. code:: python

    >>> parsed = wtp.parse('{{t1 |b=b|c=c| d={{t2|e=e|f=f}} }}')
    >>> t1, t2 = parsed.templates
    >>> print(t2.pformat())
    {{t2
        | e = e
        | f = f
    }}
    >>> print(t1.pformat())
    {{t1
        | b = b
        | c = c
        | d = {{t2
            | e = e
            | f = f
        }}
    }}

``Template.rm_dup_args_safe`` and ``Template.rm_first_of_dup_args`` methods can be used to clean-up `pages using duplicate arguments in template calls <https://en.wikipedia.org/wiki/Category:Pages_using_duplicate_arguments_in_template_calls>`_:

.. code:: python

    >>> t = wtp.Template('{{t|a=a|a=b|a=a}}')
    >>> t.rm_dup_args_safe()
    >>> t
    Template('{{t|a=b|a=a}}')
    >>> t = wtp.Template('{{t|a=a|a=b|a=a}}')
    >>> t.rm_first_of_dup_args()
    >>> t
    Template('{{t|a=a}}')

Template parameters:

.. code:: python

    >>> param = wtp.parse('{{{a|b}}}').parameters[0]
    >>> param.name
    'a'
    >>> param.default
    'b'
    >>> param.default = 'c'
    >>> param
    Parameter('{{{a|c}}}')
    >>> param.append_default('d')
    >>> param
    Parameter('{{{a|{{{d|c}}}}}}')


WikiLinks
---------

.. code:: python

    >>> parsed = wtp.parse('text [[A|B]] text')
    >>> wl = parsed.wikilinks[0]
    >>> wl
    WikiLink('[[A|B]]')
    >>> wl.target = 'Z'
    >>> wl.text = 'X'
    >>> parsed
    WikiText('text [[Z|X]] text')

Sections
--------

.. code:: python

    >>> parsed = wtp.parse("""
    ... == h2 ==
    ... t2
    ... === h3 ===
    ... t3
    ... === h3 ===
    ... t3
    ... == h22 ==
    ... t22
    ... {{text|value3}}
    ... [[Z|X]]
    ... """)
    >>> parsed.sections
    [Section('\n'),
     Section('== h2 ==\nt2\n=== h3 ===\nt3\n=== h3 ===\nt3\n'),
     Section('=== h3 ===\nt3\n'),
     Section('=== h3 ===\nt3\n'),
     Section('== h22 ==\nt22\n{{text|value3}}\n[[Z|X]]\n')]
    >>> parsed.sections[1].title = 'newtitle'
    >>> print(parsed)

    ==newtitle==
    t2
    === h3 ===
    t3
    === h3 ===
    t3
    == h22 ==
    t22
    {{text|value3}}
    [[Z|X]]

Tables
------

Extracting cell values of a table:

.. code:: python

    >>> p = wtp.parse("""{|
    ... |  Orange    ||   Apple   ||   more
    ... |-
    ... |   Bread    ||   Pie     ||   more
    ... |-
    ... |   Butter   || Ice cream ||  and more
    ... |}""")
    >>> p.tables[0].data()
    [['Orange', 'Apple', 'more'],
     ['Bread', 'Pie', 'more'],
     ['Butter', 'Ice cream', 'and more']]

By default, values are arranged according to ``colspan`` and ``rowspan`` attributes:

.. code:: python

    >>> t = wtp.Table("""{| class="wikitable sortable"
    ... |-
    ... ! a !! b !! c
    ... |-
    ... !colspan = "2" | d || e
    ... |-
    ... |}""")
    >>> t.data()
    [['a', 'b', 'c'], ['d', 'd', 'e']]
    >>> t.data(span=False)
    [['a', 'b', 'c'], ['d', 'e']]

Calling the ``cells`` method of a ``Table`` returns table cells as ``Cell`` objects. Cell objects provide methods for getting or setting each cell's attributes or values individually:

.. code:: python

    >>> cell = t.cells(row=1, column=1)
    >>> cell.attrs
    {'colspan': '2'}
    >>> cell.set('colspan', '3')
    >>> print(t)
    {| class="wikitable sortable"
    |-
    ! a !! b !! c
    |-
    !colspan = "3" | d || e
    |-
    |}

HTML attributes of Table, Cell, and Tag objects are accessible via
`get_attr`, `set_attr`, `has_attr`, and  `del_attr` methods.

Lists
-----

The `lists` method provides access to lists within the wikitext.

.. code:: python

    >>> parsed = wtp.parse(
    ...     'text\n'
    ...     '* list item a\n'
    ...     '* list item b\n'
    ...     '** sub-list of b\n'
    ...     '* list item c\n'
    ...     '** sub-list of b\n'
    ...     'text'
    ... )
    >>> wikilist = parsed.lists()[0]
    >>> wikilist.items
    [' list item a', ' list item b', ' list item c']

The `sublists` method can be used to get all sub-lists of the current list or just sub-lists of specific items:

.. code:: python

    >>> wikilist.sublists()
    [WikiList('** sub-list of b\n'), WikiList('** sub-list of b\n')]
    >>> wikilist.sublists(1)[0].items
    [' sub-list of b']

It also has an optional `pattern` argument that works similar to `lists`, except that the current list pattern will be automatically added to it as a prefix:

.. code:: python

    >>> wikilist = wtp.WikiList('#a\n#b\n##ba\n#*bb\n#:bc\n#c', '\#')
    >>> wikilist.sublists()
    [WikiList('##ba\n'), WikiList('#*bb\n'), WikiList('#:bc\n')]
    >>> wikilist.sublists(pattern='\*')
    [WikiList('#*bb\n')]


Convert one type of list to another using the convert method. Specifying the starting pattern of the desired lists can facilitate finding them and improves the performance:

.. code:: python

        >>> wl = wtp.WikiList(
        ...     ':*A1\n:*#B1\n:*#B2\n:*:continuing A1\n:*A2',
        ...     pattern=':\*'
        ... )
        >>> print(wl)
        :*A1
        :*#B1
        :*#B2
        :*:continuing A1
        :*A2
        >>> wl.convert('#')
        >>> print(wl)
        #A1
        ##B1
        ##B2
        #:continuing A1
        #A2

Tags
----

Accessing HTML tags:

.. code:: python

        >>> p = wtp.parse('text<ref name="c">citation</ref>\n<references/>')
        >>> ref, references = p.tags()
        >>> ref.name = 'X'
        >>> ref
        Tag('<X name="c">citation</X>')
        >>> references
        Tag('<references/>')

WikiTextParser is able to handle common usages of HTML and extension tags. However it is not a fully-fledged HTML parser and may fail on edge cases or malformed HTML input. Please open an issue on github if you encounter bugs.

Miscellaneous
-------------
``parent`` and ``ancestors`` methods can be used to access a node's parent or ancestors respectively:

.. code:: python

    >>> template_d = parse("{{a|{{b|{{c|{{d}}}}}}}}").templates[3]
    >>> template_d.ancestors()
    [Template('{{c|{{d}}}}'),
     Template('{{b|{{c|{{d}}}}}}'),
     Template('{{a|{{b|{{c|{{d}}}}}}}}')]
    >>> template_d.parent()
    Template('{{c|{{d}}}}')
    >>> _.parent()
    Template('{{b|{{c|{{d}}}}}}')
    >>> _.parent()
    Template('{{a|{{b|{{c|{{d}}}}}}}}')
    >>> _.parent()  # Returns None

Use the optional ``type_`` argument if looking for ancestors of a specific type:

.. code:: python

    >>> parsed = parse('{{a|{{#if:{{b{{c<!---->}}}}}}}}')
    >>> comment = parsed.comments[0]
    >>> comment.ancestors(type_='ParserFunction')
    [ParserFunction('{{#if:{{b{{c<!---->}}}}}}')]


To delete any object from the its parent objects use ``del object[:]`` or ``object.string = ''``.


Compared with mwparserfromhell
==============================

`mwparserfromhell <https://github.com/earwig/mwparserfromhell>`_ is a mature and widely used library with nearly the same purposes as `wikitextparser`. The main reason leading me to create `wikitextparser` was that `mwparserfromhell` could not parse wikitext in certain situations that I needed it for. See mwparserfromhell's issues `40 <https://github.com/earwig/mwparserfromhell/issues/40>`_, `42 <https://github.com/earwig/mwparserfromhell/issues/42>`_, `88 <https://github.com/earwig/mwparserfromhell/issues/88>`_, and other related issues. In many of those situation `wikitextparser` may be able to give you more acceptable results.

But if you need to

* use Python 2
* parse style tags like `'''bold'''` and ''italics'' (with some `limitations <https://github.com/earwig/mwparserfromhell#caveats>`_ of-course)
* extract `HTML entities <https://mwparserfromhell.readthedocs.io/en/latest/api/mwparserfromhell.nodes.html#module-mwparserfromhell.nodes.html_entity>`_

then `mwparserfromhell` or maybe other libraries will be the way to go. Also note that `wikitextparser` is still under heavy development and the API may change drastically in the future versions.

Of-course `wikitextparser` has its own unique features, too: Providing access to individual cells of each table, pretty-printing templates, and a few other advanced functions.

The tokenizer in `mwparserfromhell` is written in C. Tokenization in `wikitextparser` is mostly done using the `regex` library which is also in C.
I have not rigorously compared the two libraries in terms of performance, i.e. execution time and memory usage. In my limited experience, `wikitextparser` has a decent performance and should able to compete and may even have little performance benefits in many situations. However if you are working with on-line data, any difference is usually negligible as the main bottleneck will be the network latency.

If you have had a chance to compare these libraries in terms of performance please share your experience by opening an issue on github.


Known issues and limitations
============================

* Syntax elements produced by a template transclusion cannot be detected by offline parsers.
* Localized namespace names are unknown, so for example `[[File:...]]` links are treated as normal wikilinks. `mwparserfromhell` has similar issue, see `#87 <https://github.com/earwig/mwparserfromhell/issues/87>`_ and `#136 <https://github.com/earwig/mwparserfromhell/issues/136>`_. As a workaround, `Pywikibot <https://www.mediawiki.org/wiki/Manual:Pywikibot>`_ can be used for determining the namespace.
* `Linktrails <https://www.mediawiki.org/wiki/Help:Links>`_ are language dependant and are not supported. `Also not supported by mwparserfromhell <https://github.com/earwig/mwparserfromhell/issues/82>`_. However given the trail pattern and knowing that ``wikilink.span[1]`` is the ending position of a wikilink, it should be trivial to compute a WikiLink's linktrail.
* Templates adjacent to external links, are never considered part of the link. In reality, this depends on the contents of the template. Example: ``parse('http://example.com{{dead link}}').external_links[0].url == 'http://example.com'``
* While MediaWiki recognizes only a finite number of tags and they are extension-dependent, the ``tags`` method returns anything that looks like an HTML tag. A configuration option might be added in the future to address this issue.


Credits
=======
* `python <https://www.python.org/>`_
* `regex <https://bitbucket.org/mrabarnett/mrab-regex/>`_
* `wcwidth <https://github.com/jquast/wcwidth>`_
