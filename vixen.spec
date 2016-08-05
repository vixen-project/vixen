# -*- mode: python -*-

block_cipher = None

import datetime
import os
import jigna

import vixen

version = vixen.__version__
if version.endswith('.dev0'):
    today = datetime.datetime.now().strftime('%Y%m%d')
    version += '-' + today
app_dir_name = 'vixen-{version}'.format(version=version)


JIGNA_DIR = os.path.join(os.path.dirname(jigna.__file__), 'js', 'dist')
added_files = [
    ('vixen/html', 'vixen_data/html'),
    (JIGNA_DIR, 'jigna/js/dist'),
]

a = Analysis(['vixen/cli.py'],
             pathex=[os.path.abspath(os.getcwd())],
             binaries=None,
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['PySide', 'wx', 'PyQt4'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='vixen',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name=app_dir_name)
