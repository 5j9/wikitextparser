v0.21.0
-------
- Changed: Results are now sorted by their span.
- Fixed: Bug in ``ancestors`` and ``parent`` methods.

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
