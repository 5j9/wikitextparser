==============
wikitextparser
==============

A simple, purely python, WikiText parsing tool.

The project is still in early development stages and I'm not sure if it
will ever succeed. It sure can't parse a page the same way the MediaWiki does 
(for example because it's completely offline and can't expand templates and
also has not implemented many details of MediaWiki parser), but my guess
is that for most usual uses it will be enough.

Installation
============

Use ``pip install wikitextparser``

Usage
=====

Here is a short demo of some of the functionalities:

.. code:: python

    >>> import wikitextparser as wtp
    >>> # wikitextparser can detect sections, parserfunctions, templates,
    >>> # wikilinks, external links, arguments, and HTML comments in
    >>> # your wikitext:
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
    >>> # It provides easy-to-use properties so you can get or set
    >>> # name or value of templates, arguments, wikilinks, etc.
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
    >>> # There is a pprint function that you might find useful:
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
    >>> # If you are dealing with 
    >>> # [[Category:Pages using duplicate arguments in template calls]],
    >>> # there are two functions that may be helpful:
    >>> t = wtp.Template('{{t|a=a|a=b|a=a}}')
    >>> t.rm_dup_args_safe()
    >>> t
    Template('{{t|a=b|a=a}}')
    >>> t = wtp.Template('{{t|a=a|a=b|a=a}}')
    >>> t.rm_first_of_dup_args()
    >>> t
    Template('{{t|a=a}}')
    >>> # Have a look at test.py module for more details and probable pitfalls.
    >>> 

See also: 

* `mwparserfromhell <https://github.com/earwig/mwparserfromhell>`_
