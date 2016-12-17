.. _installation:

=================================
Installation and getting started
=================================

To install ViXeN, you first need to know the platform you will be running it on.
ViXeN is available for Linux (64 bit), Mac (64 bit), and Windows (32 and 64 bit).

Since there is a lot of information here, we suggest that you skim the section
on :ref:`dependencies` and then directly jump to one of the "Installing the
dependencies on xxx" sections below depending on your operating system.
Depending on your chosen operating system, simply follow the instructions
and links referred therein.

.. contents::
    :local:
    :depth: 1

.. _quick-install:

-------------------
Quick installation
-------------------

You may do this in a virtualenv_ if you chose to.  The
important examples are packaged with the sources, you should be able to run
those immediately. If you wish to download the sources and explore them, you
can download the sources either using the tarball/ZIP or from git, see
:ref:`downloading-vixen`.

The following instructions are more detailed and also show how optional
dependencies can be installed.  Instructions on how to set things up on Windows
is also available below.


.. _dependencies:

------------------
Dependencies
------------------

^^^^^^^^^^^^^^^^^^
Core dependencies
^^^^^^^^^^^^^^^^^^

Please make sure you have a good, functional browser such as:
- Mozilla Firefox (any recent version)
- Google Chrome (any recent version)
- Internet Explorer (IE 9 and above)

  
^^^^^^^^^^^^^^^^^^^^^^
Optional dependencies
^^^^^^^^^^^^^^^^^^^^^^

The optional dependencies are:
- ffmpeg

If you want to do some cool stuff involving video files, this is essential..

-----------------------------------------
Installing the dependencies on GNU/Linux
-----------------------------------------

GNU/Linux is probably the easiest platform to install ViXeN. On Ubuntu one may
install the dependencies by following three very simple steps:
- Download the ViXeN source file 
- Unpack the sources locally 
- Run the application

.. _using-nautilus:

^^^^^^^^^^^^^^^^^^^
Using Nautilus
^^^^^^^^^^^^^^^^^^^
1. Download the ViXen source file (say vixen-v0.2.tgz) from Github_ to your preferred 
directory

.. _Github: https://github.com/prabhuramachandran/vixen/tree/master/vixen

2. Right click and select 'Extract Here' or 'Open With Archive Manager'. A ViXeN folder 
will appear in the directory you have selected (in this case the folder will be vixen-v0.2)

3. Open the directory and double click the 'vixen' file. The ViXeN application will open on 
the browser, **if** Nautilus supports running executables. If it does not, run the command
shown in :ref:`using-cli`

.. _using-cli:

^^^^^^^^^^^^^^^^^^^^^^^
Using the Command Line
^^^^^^^^^^^^^^^^^^^^^^^

After downloading and unpacking ViXen either :ref:`using-nautilus`, run the following commands on the terminal:

	$ cd <folder path>

Suppose you downloaded and unpacked the vixen-v0.2.tgz file in a folder named 'Software' in 
your 'home' directory, then this command will be:
	
	$ cd Software/vixen-v0.2

Then run the application using:

	$ ./vixen

.. _installing-deps-osx:

------------------------------------------
Installing the dependencies on Mac OS X
------------------------------------------

---------------------------------------
Installing the dependencies on Windows
---------------------------------------



.. _using-virtualenv:

-------------------------------
Using a virtualenv for ViXeN
-------------------------------


A virtualenv_ allows you to create an isolated environment for ViXen and its
related packages.  This is useful in a variety of situations.

You can either install virtualenv_ (or ask your system administrator to) or
just download the `virtualenv.py
<http://github.com/pypa/virtualenv/tree/master/virtualenv.py>`_ script and use
it (run ``python virtualenv.py`` after you download the script).

.. _virtualenv: http://www.virtualenv.org



^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Using Virtualenv on Canopy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you are using `Enthought Canopy`_, it already bundles virtualenv for you but
you should use the ``venv`` script.  For example::

    $ venv --help
    $ venv --system-site-packages myenv
    $ source myenv/bin/activate

The rest of the steps are the same as above.


.. _downloading-vixen:

------------------
Downloading ViXeN
------------------

One way to install 

Once you have downloaded ViXeN you should be ready to build and install it,
see :ref:`building-vixen`.


.. _building-vixen:

-------------------------------
Building and Installing ViXeN
-------------------------------


You should be all set now and should next consider :ref:`running-the-tests`.



.. _running-the-tests:

------------------
Running the tests
------------------


.. _running-the-examples:

---------------------
Running the examples
---------------------


--------------------------------------
Organization of the ``ViXeN`` package
--------------------------------------

ViXeN is organized into several sub-packages.  These are:


