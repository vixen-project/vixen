1.0rc2
-------

* Release date: Soon to be released.
* Prepare for release on PyPI.
* Add pause/stop buttons when processing files and clean up processing UI.
* Fix bug with saving projects which had tagger processors.
* Support to copy a project.
* Awesome new logo for the application and documentation.
* Improved the rescan functionality to warn users about what it does and
  remove dead files from the database.
* Add a new "text" tag type for larger text input.
* Warn user when they add unsupported tag names (names with spaces or those
  starting with an _).
* Add button to re-order the tags.
* Fix UI slowness when editing a lot of text on firefox.
* Fix an issue with CSV export with unicode text.
* Support for Python 3.x.

1.0rc1
------

* Release date: Mar 17, 2017.
* Massive performance improvements (> 10x) for handling many files. This makes
  it possible to comfortably handle many more files than before.
* Documentation improvements.
* Small UI improvements for search and navigation.
* Fix bug when starting vixen for the first time -- if one added a project it
  would not show correctly until vixen was re-launched.
* Fix issue with notifications on firefox.
* Add ability to view the application log, to help with reporting issues.
* Notify users of any unexpected errors so these can be reported.
* Improved test coverage.

0.9
---

* Release data: Jan 18, 2017.
* First public release.
* Easy to install binaries on Linux, OS X, and Windows.
* Basic documentation.
