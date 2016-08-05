#!/usr/bin/env python

import os
import glob
import shutil
import subprocess
import sys

def copy_python_on_osx():
    if hasattr(sys, 'base_prefix'):
        dest_dirs = [x for x in glob.glob('dist/vixen*') if os.path.isdir(x)]
        dest = dest_dirs[0]
        python_lib = os.path.join(sys.base_prefix, 'Python')
        print("Copying %s -> %s"%(python_lib, dest))
        shutil.copy(python_lib, dest)

def main():
    subprocess.call(['pyinstaller', 'vixen.spec'])

    if sys.platform == 'darwin':
        copy_python_on_osx()

if __name__ == '__main__':
    main()
