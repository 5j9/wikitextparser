# wikitextparser
A simple, purely python, WikiText parsing tool.
The project is still in early development stages and I'm not sure if it
will ever succeed... Use at your own risk!

It sure can't parse a page the same way the MediaWiki does 
(because for example it's complete offline and can't expand templates and
also has not implemented many details of MediaWiki parser), but my guess
is that for most usual uses it will be enough.

Here is a short demo of some of the functionalities:

```python
>>> ================================ RESTART ================================
>>> 
>>> wt = WikiText("""== h2 ==
t2

=== h3 ===
t3

== h22 ==
t22

{{text|value1{{text|value2}}}}

[[A|B]]""")
>>> wt.templates
[Template("{{text|value2}}"), Template("{{text|value1{{text|value2}}}}")]
>>> _[1].arguments
[Argument("|value1{{text|value2}}")]
>>> _[0].value = 'value3'
>>> wt.wikilinks
[WikiLink("[[A|B]]")]
>>> wt.wikilinks[0].target = 'Z'
>>> wt.wikilinks[0].text = 'X'
>>> wt.sections
[Argument(""), Argument("== h2 ==
t2

=== h3 ===
t3

"), Argument("=== h3 ===
t3

"), Argument("== h22 ==
t22

{{text|value3}}

[[Z|X]]")]
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
>>> 
```
See also: 
* [mwparserfromhell](https://github.com/earwig/mwparserfromhell)
