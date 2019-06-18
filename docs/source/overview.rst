========================================
ViXeN: View eXtract aNnotate media data
========================================

ViXeN is a simple tool to facilitate easily viewing, adding, and annotating
metadata associated with media. ViXeN has been designed primarily to assist
field biologists with managing the large amount of media they collect in a
minimally intrusive manner.

One may think of ViXeN as a special, customizable file browser with which one
may view and edit metadata associated with media files like videos, images,
and audio.

ViXeN is open source and distributed under the liberal `BSD license
<https://opensource.org/licenses/BSD-3-Clause>`_.

--------
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


--------
History
--------

ViXeN was envisaged as a 'no-fuss' means to manage videos from 32 camera traps
that were set up in the Banni grasslands in north-west India to survey species
occurrence and interaction patterns, with a focus on carnivores. The research
project began in 2013 and as of 2015 has resulted in 6000+ videos. When
confronted with the daunting task of viewing and managing such volumes of
media files, we realized that there was a dearth for tools to aid in the
processing of such data. There were data managers for images but nothing
suitable for video (and to a certain extent, audio) files.

-------
Support
-------

If you have any questions or are having any problems with ViXeN, please email
or post your questions on the vixen-users mailing list here:
https://groups.google.com/d/forum/vixen

If you should have specific problems with ViXeN, you may eitiher email us on
the list mentioned above or file an issue on github here:
https://github.com/vixen-project/vixen/issues/new

If you do not mind, you can consider sending along the vixen log as discussed
in :ref:`troubleshooting`.

We welcome any contributions to this project. Please submit a pull-request on
github and we will be happy to consider any suggestions and improvements.

One useful, and perhaps underutilized feature of github is that if you want to
make a change to the software or documentation, you may do so directly on
github and submit that as a pull-request for us to consider without having to
learn git, forking the project, and manually submitting a pull-request.


-------------
Citing ViXeN
-------------

You may use the following article to formally cite ViXeN if you wish:

- Prabhu Ramachandran and Kadambari Devarajan, `ViXeN: An open-source package
  for managing multimedia data <http://dx.doi.org/10.1111/2041-210X.12892>`_,
  *Methods in Ecology and Evolution*, 2041-210X, 2017.


--------
Credits
--------

Designed and developed by `Prabhu Ramachandran
<https://www.aero.iitb.ac.in/~prabhu>`_ and `Kadambari Devarajan
<http://kadambarid.in/>`_.

Many thanks to `Kamal Morjal <https://github.com/kamalx>`_ for the CSS layout
of the UI and Khushalsingh Rajput  who implemented the ViXeN logo based on
Kadambari's concept and design.


---------
Changelog
---------

.. include:: ../../CHANGES.rst
