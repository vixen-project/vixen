ViXeN: View eXtract and aNnotate media
=======================================

[![Build Status](https://travis-ci.org/vixen-project/vixen.svg?branch=master)](https://travis-ci.org/vixen-project/vixen)
[![Build status](https://ci.appveyor.com/api/projects/status/9smsybrpx04bmh22?svg=true)](https://ci.appveyor.com/project/prabhuramachandran/vixen)
[![codecov](https://codecov.io/gh/vixen-project/vixen/branch/master/graph/badge.svg)](https://codecov.io/gh/vixen-project/vixen)
[![Documentation Status](https://readthedocs.org/projects/vixen/badge/?version=latest)](http://vixen.readthedocs.io/en/latest/?badge=latest)


![ViXeN logo](https://github.com/vixen-project/vixen/tree/master/docs/source/images/logo_small.png)

ViXeN is a simple tool to facilitate easily viewing, adding, and annotating
metadata associated with media.  ViXeN has been designed primarily to assist
field biologists with managing the large amount of media they collect in
a minimally intrusive manner.

One may think of ViXeN as a special, customizable file browser with which
one may view and edit metadata associated with media files like videos, images,
and audio.

Features
--------

- Works with different types of media, videos, images, audio, text, and PDF.
- Supports any number of used-defined metadata fields per project.
- Does not modify the original media but keeps its metadata separately.
- Powerful searching through metadata.
- Lightweight and easy to install.  No server setup required.
- Cross-platform: works on Linux, OS X, and Windows.
- Simple browser-based UI.
- Support to export metadata to a CSV file and import tags from a CSV file.
- Ability to add metadata for media through an external program or a Python
  script.
- Support to allow user-defined conversions of media to supported versions.
- Open source.

ViXeN has currently been tested with about 350k files in a single project. It
will work fine for larger projects but will be progressively slower the larger
the number of files. The speed does not however depend on the nature of the
media. ViXeN does not currently support multiple people working on the same
project at the same time.


Download
---------

To try out ViXeN please download a binary installer from here:

  https://github.com/vixen-project/vixen/releases

These are very easy to install, basically just download, unzip, and run.


History
--------

ViXeN was envisaged as a 'no-fuss' means to manage videos from 32 camera traps
that were set up in the Banni grasslands in north-west India to survey species
occurrence and interaction patterns, with a focus on carnivores. The research
project began in 2013 and as of 2015 has resulted in 6000+ videos. When
confronted with the daunting task of viewing and managing such volumes of
media files, we realized that there was a dearth for tools to aid in the
processing of such data. There were data managers for images but nothing suitable
for video (and to a certain extent, audio) files.

Support
-------

If you have any questions or are having any problems with ViXeN, please email
or post your questions on the vixen-users mailing list here:
https://groups.google.com/d/forum/vixen


Credits
-------

Designed and Developed by Prabhu Ramachandran and Kadambari Devarajan
