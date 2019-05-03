v0.24.4
-------
- Fixed a bug in ``Tag.parsed_contents``. (#19)

v0.24.3
-------
- Fixed a rarely occuring bug in detecting parameters with names consisting only of whitespace or underscores.

v0.24.2
-------
- Fixed a bug in detecting parser functions containing parameters.

v0.24.1
-------
- Fixed a bug in detecting table header cells that start with +, -, or }. (#17)

v0.24.0
-------
- Define a deleter for ``WikiText.string`` property and add ``Template.del_arg`` method. (#14)
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
