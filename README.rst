==============
wikitextparser
==============

A simple, purely python, WikiText parsing tool.

The purpose is to allow users easily extract and/or manipulate templates, template parameters, parser functions, tables, external links, wikilinks, etc. in wikitexts.

Installation
============

Use ``pip install wikitextparser``

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
        |e=e
        |f=f
    }}
    >>> print(t1.pprint())
    {{t1
        |b=b
        |c=c
        |d={{t2
            |e=e
            |f=f
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
    >>> pprint(p.tables[0].getdata())
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
    >>> t.getdata(span=True)
    [['a', 'b', 'c'], ['d', 'd', 'e']]

Have a look at the test modules for more details and probable pitfalls.

See also: 

* `mwparserfromhell <https://github.com/earwig/mwparserfromhell>`_
