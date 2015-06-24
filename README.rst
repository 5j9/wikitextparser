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
    >>> _[1].arguments
    [Argument("|value1{{text|value2}}")]
    >>> _[0].value = 'value3'
    >>> wt
    WikiText('\n== h2 ==\nt2\n\n=== h3 ===\nt3\n\n== h22 ==\nt22\n\n{{text|value3}}\n\n[[A|B]]')
    >>> # It provides easy-to-use properties so you can get or set
    >>> # name or value of templates, arguments, wikilinks, etc.
    >>> wt.wikilinks
    [WikiLink("[[A|B]]")]
    >>> wt.wikilinks[0].target = 'Z'
    >>> wt.wikilinks[0].text = 'X'
    >>> wt
    WikiText('\n== h2 ==\nt2\n\n=== h3 ===\nt3\n\n== h22 ==\nt22\n\n{{text|value3}}\n\n[[Z|X]]')
    >>> 
    >>> from pprint import pprint
    >>> pprint(wt.sections)
    [Argument('\n'),
     Argument('== h2 ==\nt2\n\n=== h3 ===\nt3\n\n'),
     Argument('=== h3 ===\nt3\n\n'),
     Argument('== h22 ==\nt22\n\n{{text|value3}}\n\n[[Z|X]]')]
    >>> 
    >>> wt.sections[1].title = 'newtitle'
    >>> print(wt.string)

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
    >>> t1, t2 = p.templates
    >>> print(t1.pprint())
    {{t2
        |e=e
        |f=f
    }}
    >>> print(t2.pprint())
    {{t1
        |b=b
        |c=c
        |d={{t2
            |e=e
            |f=f
        }}
    }}
    >>> # If you are dealing with a category like 
    >>> # [[Category:Pages using duplicate arguments in template calls]]
    >>> # There are two functions that may be helpful:
    >>> t = wtp.Template('{{t|a=a|a=b|a=a}}')
    >>> t.rm_dup_args_safe()
    >>> t
    Template('{{t|a=b|a=a}}')
    >>> t = wtp.Template('{{t|a=a|a=b|a=a}}')
    >>> t.rm_first_of_dup_args()
    >>> t
    Template('{{t|a=a}}')
    >>> # Have look at test.py module for more details and probable pitfalls.
    >>> 

See also: 

* `mwparserfromhell <https://github.com/earwig/mwparserfromhell>`_
