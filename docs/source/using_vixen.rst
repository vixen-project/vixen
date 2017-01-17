.. _using-vixen:

=============
Using ViXeN
=============

This is a simple tutorial on how to get started using ViXeN and its features.

When you first start the application it should open a new page on your default
browser. If this is not a supported browser, you can simply copy the URL on
the location bar onto a supported browser such as Chrome or Firefox and the UI
should load correctly.

When you first start you will have a rather empty page with an button on the
left panel to create a new project.


Setting up a project
--------------------

Create a new project by clicking on "New project". Fill in the fields of the
project on the right side.  The important fields to fill are:

- Name: set this to a suitable name for your project.

- Path: this is the path to the root of your media files that you wish to
  index. Click on "Browse..." to choose the directory from a file browser. You
  may also directly type the directory path on the text box. All files inside
  this directory can be "indexed". You may choose to index only specific
  extensions by adding specific extensions on the field below the "Tags" field.

- Tags: this is a very important field. These define the various metadata tags
  associated with your media. You may add as many fields as you desire. A tag
  can be either a string, integer, float, or boolean. For each media file, you
  will be able to change/edit these fields when viewing the project. You can
  add multiple tags in one go by separating them with commas, for example:
  fox, jackal, dog. Once added you can change the type of the tag on the UI.
  You can add and remove tags later on also. One default tag is always added
  called "completed" you may remove it without any loss of functionality if
  you do not need it.

- File extensions to index: this defaults to all extensions, you may specify
  any extensions you specifically wish to index. For example specifying ".png,
  .jpg" and clicking on the "Add extension" will index only the png and jpg
  files. The button, "Find available extensions" will show you a list of all
  extensions inside the specified path.

- Processors: You may add a variety of processors that allow you to either
  convert your media, copy your media, add tags using Python scripts, or use
  an external program to add tags. This is discussed in greater detail in the
  section :ref:`processing-media` below.  Processors are entirely optional.

Once you have setup the project, simply click on "Apply changes" for ViXeN to
quickly scan all the files and make its internal database. Depending on the
size of your directory, this should take a few seconds. Once this is done, you
can click on the "View" button on the left pane to view the media.

If you do not want a project, you may simply click on the "Remove" button
remove the project. This will remove only the internal metadata, your media
will be untouched.

Note that when the files are indexed the following tags are always available:

- ctime: date: creation date/time of the file.
- mtime: date: modified date/time of the file.
- path: string: the full path of the file.
- relpath: string: the relative path to the file with respect to the project root.
- size: int: the file size in bytes.
- type: string: the type of the file (video, audio, image, html, pdf, etc.)


Viewing media
--------------

The view interface is very simple and divided into two parts. On the left side
you will see a simple directory browser. Clicking on a directory (shown
typically in bold with a trailing '/') will navigate into this directory and
clicking on a file will display the media on the right side of the page. Below
the directory browser, the metadata tags of the media file are shown. One may
edit the tags as one sees fit.

On the right side, the media file is shown. Any file format that the browser
can render is typically shown currently this works for videos (webm, ogg
theora video), image files ('.png', '.jpg', '.gif', '.svg' etc.), audio files
('.mp3', '.m4a', '.ogg', etc.), HTML, text, and PDF. The rendering is really
dependent on the browser and your platform.

ViXeN thus makes it easy to view the data on the right and update the metadata
for each file.

.. note::

   It is important to remember to save the project after changing the
   metadata. This can be done by pressing the "Save" button or pressing
   "Command+S" or "Control+S".

While navigating the directory browser, there are a few useful keyboard
shortcuts:

- Pressing "h" or the left arrow key will go to the parent directory.
- "k", "n", or the "down" arrow key will go to the next file,
- "j", "p", or "up" arrow will go to the previous file/directory,
- "l", "enter", or the right arrow key will either select/view the file or
  navigate into a sub-directory.


Searching
-----------

One powerful feature with ViXeN is the ability to search through the metadata.

By default searching for a string in the search box and pressing return/enter
or pressing the search button will search for the occurrence of the string in
the full path of the media file.

To search for specific tags, let us consider an example project with the
metadata tags "fox" (an integer), "jackal" (an integer), and "others"
(string).

- To find all the media which have a single fox, one types: ``fox:1``
- To find all the media which greater than one fox, one types: ``fox:>1``
- To find all the media which greater than one fox or one jackal, one types:
  ``fox:>1 OR jackal:1``
- To find all the media where the "others" tag has a gerbil one types:
  ``others:gerbil``.
- To find all the media where there is a gerbil and a single jackal one types:
  ``jackal:1 AND others:gerbil``

In addition, one may also search by the time of the media. Each media file's
creation time (``ctime``) and modified time (``mtime``) are also indexed
automatically.  One can search for the time as follows:

- for all images modified in 2015: ``mtime:2015``,
- for all images modified in 2015 January: ``mtime:201501`` or ``mtime:'jan
  2015'``

ViXeN uses whoosh_ to parse the query string. For more details on the query
language see the `date parsing documentation
<https://whoosh.readthedocs.io/en/latest/dates.html>`_.


.. _whoosh: http://whoosh.readthedocs.io



Exporting the tag information to a CSV file
--------------------------------------------

Once the tags have been entered one can export the metadata to a CSV file.
Simply click on the "Export CSV" button and you will be prompted for a file.
This file will contain all the tags for the data.


Importing tag information from a CSV file
------------------------------------------

One may also import tag information from a CSV file. Click on the "Import CSV"
button, supply a file and it will import the tags. The CSV file must have a
"path" column which should be exactly the same path as the corresponding media
file. If there is a doubt as to what path is stored by Vixen, export the
project data to CSV and look at the path column.

It is important to note that only tags that have already been defined in the
project will be imported. The column name of the CSV file should match the tag
name exactly. Any columns which do not have corresponding tags will not be
imported.

Finally, after importing the tags, one must save the project to have the
changes be stored to disk.


.. _processing-media:

Processing media files
----------------------

TBW.

Advanced scripting
-------------------

TBW.
