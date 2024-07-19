..
    Unreleased
    ----------
    * 

v0.56.1
-------
* Fixed a bug in ``get_sections`` when ``top_levels_only`` was ``True``.

v0.56.0
-------
* Drop Python 3.7 support.

v0.55.14
--------
* Fixed a bug in detecting the text of an external link. (#137)

v0.55.13
--------
*  Fixed a bug in ``Section.level`` resulting in malformed section titles when multiple levels are added (#135)

v0.55.12
--------
* Performance improvements in extracting bold and italic nodes. (#133)

v0.55.11
--------
* Performance improvements in ``__setitem__``/``__delitem__`` and ``pformat``/``plain_text`` methods. (#131)

v0.55.10
--------
* Fixed a bug in ``plain_text`` causing ``IndexError`` when using a custom function to replace ``templates``/``parser_functions``.

v0.55.9
-------
- Fixed a bug in ``plain_text`` not detecting images with multiple dots correctly. (#129)

v0.55.8
-------
- Fixed: Equal signs in extension tag attributes are no longer confused with name-value separator in arguments. (#128)

v0.55.7
-------
- Fixed a bug in ``plain_text``. (#126)
- Fixed another bug in parsing tables that end without a ``|}`` mark. (#125)

v0.55.6
-------
- Fixed bug in parsing tables that end without a ``|}`` mark. (#124)

v0.55.5
-------
- Fixed: regression in ``plain_text`` not being  able to handle wikilinks only containing fragment/anchor, not title.

v0.55.4
-------
- ``plain_text`` method now uses a more accurate image-detection algorithm.

v0.55.3
-------
- Fixed and improved handling of tables and images in ``plain_text`` (#122)

v0.55.0
-------
- Added:  ``top_levels_only`` argument to ``get_sections``.
- Deprecated: Calling ``get_sections`` with positional arguments is now deprecated.

v0.54.1
-------
- Fixed some bugs in ``plain_text`` method. (#119, #120)
- Fixed bug in ``get_tags``. (#121)

v0.54.0
-------
- Fixed a bug in ``WikiText.external_links`` not detecting external links inserted via overwriting a template string. (#74)
- The following already deprecated functions/parameters are removed:

  - Setting ``Parameter.default`` to ``None`` is not possible anymore. Use ``del Parameter.default`` instead.
  - The default value for ``preserve_spacing`` parameter of ``Template.set_arg`` is now ``False``. (It was deprecated to call this method without providing a value for ``preserve_spacing``)
  - The ``pattern`` parameter of ``WikiList.sublists``, ``WikiList.get_lists`` and ``WikiText.get_lists`` cannot be ``None`` anymore. Use the default value instead.
  - ``WikiText.lists``` and ``WikiText.tags`` are removed. Use ``get_lists``` or ``get_tags`` instead.

v0.53.0
-------
- Fixed a bug in ``plain_text()``/``remove_markup``, not being able to handle table with row/colspan. (#116)
- ``plain_text()`` will now include table captions.

v0.52.1
-------
- Fixed a syntax error for Python < 3.10.

v0.52.0
-------
- BREAKING CHANGE: dropping Python 3.6 support.
- Fixed error in getting ``plain_text()`` of emptied-out wikitext (#113)
- Deprecated: Calling ``Template.set_arg()`` without specifying a value  for ``preserve_spacing`` parameter is deprecated.
  This is a temporary warning in preparation for changing the default value of this parameter from ``True`` to ``False``. (#111)
- Fixed the ``stacklevel`` of warnings.
- New feature: ``plain_text()`` replaces wiki-tables with a TSV string. (#115)

v0.51.2
-------
- Fixed a bug in detecting `reverse pipe tricks <https://en.wikipedia.org/wiki/Help:Pipe_trick#Reverse_pipe_trick>`_ as wikilinks.

v0.51.1
-------
- Fixed a bug in ``WikiText.external_links`` causing external links within extension tags (e.g. ref tag) not to be detected when tag is inside a template/parser function/parameter. (#110)

v0.51.0
-------
- ``WikiText.get_lists`` now correctly detects lists with a missing level (#70)
- ``WikiList.sublists`` are now returned in sorted order.

v0.50.2
-------
- Fixed a bug in ``WikiText.pformat`` which used to cause ``IndexError`` on a parser function which had no argument, e.g. for ``{{FULLPAGENAMEE}}``.

v0.50.0
-------
- Feat: ``Table`` objects now have ``row_attrs`` property.
- Fixed: Infinite loop on parsing tables containing ``\r``. (this is just to prevent infinite loop, CRLF line endings are not supported)

v0.49.4
-------
- Fixed: Handle empty tables instead of raising IndexError. (#107)

v0.49.3
-------
- Fixed an issue in handling of / in tags. (#108)
- Fixed a false-positive detection of invalid external links. (#109)

v0.49.2
-------
- Fixed an issue in ``Template.normal_name()`` causing IndexError on empty/invalid template names, e.g. ``{{Template:}}``. (#105)

v0.49.1
-------
- Fixed a bug in ``plain_text``/``remove_markup`` causing duplicate values when replacing nested templates.

v0.49.0
-------
- Feature: ``replace_templates`` and ``replace_parser_functions`` parameters of ``plain_text``/``remove_markup`` now accept a function mapping ``Template`` or ``ParserFuction`` objects to desired replacement string. (#103)

v0.48.3
-------
- Fixed a bug in ``Tag.parsed_contents`` method. (#102)

v0.48.2
-------
- Fixed a bug in ``plain_text`` method. (#101)

v0.48.1
-------
- Fixed a bug in ``pformat`` and ``plain_text`` methods. (#100)

v0.48.0
-------
- BREAKING: dropped support for Python 3.5
- Fixed: bug in handling of external links with uppercase scheme. (#99)

v0.47.9
-------
- Fix missing tables rows after comments (#98)

v0.47.8
-------
- Fixed: Templates titles cannot include wikilinks
- Fixed: Detection of tags withing WikiLinks (#96)

v0.47.7
-------
- Fixed a bug in ``Template.set_arg`` causing duplicate values. (#97)

v0.47.6
-------
- Fixed problem in detecting extension tags with uppercase letters in their names (#95)

v0.47.5
-------
- Fixed regex requirement for Python 3.5 on Windows platform.

v0.47.4
-------
- Fixed handling of external links within definition lists. (#91)

v0.47.3
-------
- Fixed a bug in ``plain_text`` method, not handling self-closing tags correctly.

v0.47.2
-------
- Fixed a bug that was causing the parser to hang when parsing complicated nested tags.

v0.47.1
-------
- Fixed the order of items in ``WikiList.fullitems``. (#72)
- Fixed and improved a few edge cases in ``Table.caption``. (pr #81)
- Fixed handling of external links within definition lists. (pr #83)
- Fixed a bug in parsing extension tags. (#90)

v0.47.0
-------
- MW variables are now recognized recognized as parser functions, not templates. (#69)
- Fixed a bug in mutation of root element when a child was mutated. (#66)
- Fixed a bug that was causing templates like ``{{NAMESPACE|2}}`` to be detected as a parser function. It is a template if the first argument starts with a ``:``.
- Fixed bugs in detecting attributes of table cells. (#71, #73)
- Fixed a bug in detecting header cells in tables. (#77)
- Fixed a bug in ``get_tags`` where extension tags without attributes were not returned. (#84)
- Fixed a bug in ``get_tables`` method where tables within tag extensions were not recognized (#85)

v0.46.0
-------
- Fixed a bug in detection parser functions without parameters. ``{{NAMESPACE}}`` used to be detected as template, but ``{{NAMESPACE:MediaWiki}}`` a parser function. Now both of them will be detected parser functions.

v0.45.3
-------
- Fix a bug in detecting external links within extension tags. (#65)
- Fix a few bugs ``plain_text``/``remove_markup``. (#65)

v0.45.2
-------
- Detect unclosed comments, e.g. ``<!== a``.
- Fix parsing priority of tag extensions and comments. For example the comment in ``<ref>b<!--c</ref>d-->`` used to be parsed as with ``<!--c</ref>d-->`` as comment which was incorrect.

v0.45.1
-------
- Fixed a catastrophic backtracking issue in parsing nested extension tags. (#60)
- Fixed a bug in ``Bold.text`` and ``Italic.text``, failing to parse objects containing ``\n``. (#61)

v0.45.0
-------
- Fixed a bug in parsing tags containing the ``<`` character. (#58)
- Updated the list of known extension tags.
- Improved detection of nested tag extensions, e.g. a ``<ref>`` tag within ``<references>``.

v0.44.1
-------
- Fixed a bug in ``get_bolds_and_italics`` causing it to return duplicate items in some situations. This was also causing an error in ``plain_text`` method. (#57)

v0.44.0
-------
- Fixed bug in matching header cells in ``Table.cells``. (#53)
- Add ``Cell.is_header`` property.

v0.43.2
-------
- Fixed a bug in detection of ``Table.caption`` and ``Table.caption_attrs``.

v0.43.1
-------
- Improve the performance of ``get_bolds_and_italics(recursive=True, filter_cls=None)``.
- Fix a bug in ``get_bolds_and_italics(recursive=False, filter_cls=None)`` which was causing it to return recursive Bold items.

v0.43.0
-------
- Remove the deprecated parameters of ``Template.normal_name()``.
- Fix a bug in  ``get_bolds_and_italics()`` which was causing it to return only ``Bold`` items.

v0.42.3
-------
- Fix a bug in handling of comments in template names. (#54)

v0.42.2
-------
- Improve the handling of weird ``colspan`` and ``rowspan`` values in tables. (#53)

v0.42.1
-------
- Fix a syntax error in Python 3.5.

v0.42.0
-------
- BREAKING CHANGE:
    Remove ``replace_bolds``/``replace_italics`` params from ``remove_markup``/``plain_text`` methods.
    Users can use the new ``replace_bolds_and_italics`` parameter. Removing only bolds or only italics is no longer possible.
- Add ``get_bolds_and_italics`` as a new method.
- Fixed bugs and rewrote the algorithm for finding ``Bold`` and ``Italic`` objects. (#51)

v0.41.0
-------
- Trying to mutate an overwritten/detached object will now raise ``DeadIndexError`` (a subclass of ``TypeError``). Hopefully this will prevent some subtle late-appearing bugs.

v0.38.2
-------
- Fix a bug in ``plaintext`` method.

v0.38.1
-------
- Fix a bug in detection of external links in parsable tag extensions. (#50)

v0.38.0
-------
- Fix a bug in handling of half-marked bold/italic, e.g. ``'''bold\n``.

v0.37.13
--------
- Fix a bug handling of half-marked bold/italic items e.g. ``'''bold text\n``.

v0.37.12
--------
- Improve handling of extension tags inside external links. (#49)
- Ignore invalid attributes that do not start with space characters. (#48)

v0.37.11
--------
- Improved how invalid attributes (in html tags, tables, etc.) are handled. (#47)

v0.37.10
--------
- Fixed a bug in handling ``<pre>`` tags. (#46)

v0.37.9
-------
- Fixed a bug in parsing tag attributes. (#44)

v0.37.8
-------
- Fixed handling of tags having different casings in start and end name, e.g. ``<s></S>``.
- Fix handling of extension tags.
- Fixed a bug in ``get_bolds``/``get_italics`` resulting in duplicate items in returned values. It also was causing a subtle issue in ``plain_text``/``remove_markup``, too. (#42)
- Fixed detection of parameters containing single braces.

v0.37.7
-------
- Fix handling of external links containing wikilinks.

v0.37.6
-------
- Fixed a bug in ``plain_text``/``remove_markup`` causing unexpectedly empty objects. (#40)

v0.37.5
-------
- Fixed some other bugs in ``plain_text``/``remove_markup`` functions for:

   - images containing wikitext
   - tags containing bold/italic items
   - nested tags

- Fixed a bug in extracting sub-tags.

v0.37.4
-------
- Fixed a bug in Tag objects causing strange behaviour upon mutating a tag.
- Fixed a bug in ``plain_text``/``remove_markup`` functions, causing some objects that are expected to be removed, remain in the result. (#39)

v0.37.3
-------
- Fix syntax errors for python 3.5, 3.6, and 3.7.

v0.37.2
-------
- Fix a bug in getting the parser functions of a Template object.

v0.37.1
-------
- Fix a catastrophic backtracking issue for wikitexts containing html tags. (#37)

v0.37.0
-------
- Add ``wikitextparser.remove_markup`` function and ``WikiText.plain_text`` method.
- Improve detection of parameters and wikilinks.
- Add ``get_bolds`` and ``get_italics`` methods.
- ``WikiLink.wikilinks``, ``WikiList.get_lists()``, ``Template.templates``, ``Tag.get_tags()``, ``ParserFunction.parser_functions``, and ``Parameter.parameters`` won't return objects equal to ``self`` anymore, only sub-elements will be returned.
- Improve handling of comments within wikilinks.
- ``WikiLink.text.setter`` no longer accepts None values. This was marked as deprecated since v0.25.0.
- Drop support for Python 3.4.
- Remove the deprecated ``pprint`` method. Users should use ``pformat`` instead.
- Allow a tuple of patterns in ``get_list`` and ``sublists`` method. The default ``None`` is now deprecated and a tuple is used instead.

v0.36.0
-------
- Add a new parameter, ``level``, for the ``get_sections`` method.

v0.35.0
-------
- Fixed a rare bug in handling lists and template arguments when there is newline or a pipe inside a starting or closing tag.
- ``Section.title`` will return None instead of ``''`` when the section does not have any title.

v0.34.0
-------
- Invoking the deleter of ``Section.title`` won't raise a RuntimeError anymore if the section does not have a title already.

v0.33.0
-------
- Add a deleter for ``Section.title`` property. (#32)

v0.32.0
-------
- Fixed a bug in ``WikiText.get_lists()`` which was causing it to sometimes return items in an unordered fashion. (#31)

v0.31.0
-------
- Rename ``WikiText.lists()`` method to ``WikiText.get_lists()`` and deprecate the old name.
- Add ``get_sections()`` method with ``include_subsections`` parameter which allows getting section without including subsections. (#23)

v0.30.0
-------
- Fixed a bug in parsing wikilinks contianing ``[.*]`` (#29)
- Fixed: wikilinks are not allowed to be preceded by ``[`` anymore.
- Rename ``WikiText.tags()`` method to ``WikiText.get_tags()`` and deprecate the old name.

v0.29.2
-------
- Fix a bug in detecting the end-tag of two consecutive same-name tags. (#27)

v0.29.1
-------
- Properly exclude the ``test`` package from the source distribution.

v0.29.0
-------
- Fix a regression in parsing some corner cases of nested templates. (#26)
- The previously deprecated ``WikiText.__getitem__`` now raises NotImplementedError.
- WikiText.__call__: Remove the deprecated support for start is None.
- Optimize a little and use more robust algorithms.

v0.28.1
-------
- Implemented a workaround for a catastrophic backtracking condition when parsing tables. (#22)

v0.28.0
-------
- Add ``get_tables`` as a new method to ``WikiText`` objects. It allows extracting tables in a non-recursive manner.
- The ``nesting_level`` property was only meaningful for tables, templates, and parser functions, remove it from other types.

v0.27.0
-------
- Fix a bug in detecting nested tables. (#21)
- Fix a few bug in detecting tables and template arguments.
- Changed the ``comments`` property of ``Comment`` objects to return an empty list.
- Changed the ``external_links`` property of ``ExternalLink`` objects to return an empty list.

v0.26.1
-------
- Fix a bug in setting ``Section.contents`` which only occurred when the title had trailing whitespace.
- Setting ``Section.level`` will not overwrite ``Section.title`` anymore.

v0.26.0
-------
* Define ``WikiLink.title`` property. It is similar to ``WikiLink.target`` but will not include the ``#fragment``.

v0.25.1
-------
- Deprecate using None as the start value of ``__call__``.

v0.25.0
-------
- Added fragment property to ``WikiLink`` class (#18)
- Added deleter method for ``WikiLink.text`` property.
- Deprecated: Setting ``WikiLink.text`` to ``None``. Use ``del WikiLink.text`` instead.
- Added deleter method for ``WikiLink.target`` property.
- Added deleter method for ``ExternalLink.text`` property.
- Added deleter method for ``Parameter.default`` property.
- Deprecated: Setting ``Parameter.default`` to ``None``. Use ``del Parameter.default`` instead.
- Defined ``WikiText.__call__`` to get a slice of wikitext as string.
- Deprecated ``WikiText.__getitem__``. Use ``WikiText.__call__`` or ``WikiText.string`` instead.

v0.24.4
-------
- Fixed a bug in ``Tag.parsed_contents``. (#19)

v0.24.3
-------
- Fixed a rarely occurring bug in detecting parameters with names consisting only of whitespace or underscores.

v0.24.2
-------
- Fixed a bug in detecting parser functions containing parameters.

v0.24.1
-------
- Fixed a bug in detecting table header cells that start with +, -, or }. (#17)

v0.24.0
-------
- Define deleter method for ``WikiText.string`` property and add ``Template.del_arg`` method. (#14)
- Improve the ``lists`` method of ``Template`` and ``ParserFunction`` classes. (#15)
- Fixed a bug in detection of multiline arguments. (#13)
- Deprecated ``capital_links`` parameter of ``Template.normal_name``. Use
  ``capitalize`` instead (keyword-only argument).
- Deprecated the ``code`` parameter of ``Template.normal_name`` as a positional argument deprecate. It's now a keyword-only argument.

v0.23.0
-------
- Fixed a bug in ``Section`` objects that was causing them to return the properties of the whole page (#15).
- Removed the deprecated attribute access methods.
  The following deprecated methods accessible on ``Table`` and ``Tag`` objects, have been removed: ``.has``, ``.get``, ``.set`` .
  Use ``.has_attr``, ``.get_attr``, ``.set_attr`` instead.
- Fixed a bug in ``set_attr`` method.
- Removed the deprecated ``Table.getdata`` method. Use ``Table.data`` instead.
- Removed the deprecated ``Table.getrdata(row_num)`` method. Use ``Table.data(row=row_num)`` instead.
- Removed the deprecated ``Table.getcdata(col_num)`` method. Use ``Table.data(col=col_num)`` instead.
- Removed the deprecated ``Table.table_attrs`` property. Use ``Table.attrs`` or other attribute-related methods instead.

v0.22.1
-------
- Fixed MemoryError caused by very long or unclosed comment tags (issue #12)

v0.22.0
-------
- Change the behaviour of external_links property to never return Templates or parser functions as part of the external link.
- Add support for literal IPv6 external links, e.g. https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443/.
- Fixed: Do not mistake the equal signs of section titles for template keyword arguments.

v0.21.5
-------
- Fixed Invalid escape sequences for Python 3.6.
- Added ``msg``, ``msgnw``, ``raw``, ``safesubst``, and ``subst`` to known parser function identifiers.

v0.21.4
-------
- Fixed a bug in Table.data (issue #9)

v0.21.3
-------
- Fixed: A bug in processing ``Section`` objects.

v0.21.2
-------
- Fixed: A bug in ``external_links`` (the starting position must now be a word boundary; previously this condition was not checked)

v0.21.1
-------
- Fixed: A bug in ``external_links`` (external links withing sub-templates are now detected correctly; previously they were ignored)

v0.21.0
-------
- Changed: The order of results, now everything is sorted by its starting position.
- Fixed: Bug in ``ancestors`` and ``parent`` methods

v0.20.0
-------
- Added: ``parent`` and ``ancestors`` methods
- Added: ``__version__`` to ``__init__.py``

v0.19.0
-------
- Removed: Support for Python 3.3
- Fixed: Handling of comments and tags in section titles

v0.18.0
-------
- Changed: Add an underscore prefix to private internal modules names
- Changed: Moved test modules to a different directory
- Changed: Templates adjacent to external links are now treated as part of the link
- Fixed: A bug in handling tag extensions withing parser functions
- Fixed: A minor bug in Template.set_arg
- Changed: ExternalLink.text: Return None if the link is not within brackets
- Fixed: Handling of comments and templates in external links
