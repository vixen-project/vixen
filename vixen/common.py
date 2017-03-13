"""Convenience functions that are common to several pieces.

Try to keep this module simple: no non-standard library imports.
"""

import os
from os.path import expanduser, isdir, join


def get_project_dir():
    """Return the project root directory.

    This is where all the project metadata, the logfile etc. are stored.

    The code checks for an environment variable called 'VIXEN_ROOT'. Otherwise
    it defaults to ~/.vixen/.

    """
    default = expanduser(join('~', '.vixen'))
    d = os.environ.get('VIXEN_ROOT', default)
    if not isdir(d):
        os.makedirs(d)
    return d
