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
