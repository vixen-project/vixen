import os
from os.path import basename, dirname, join
import tempfile
import shutil

import unittest

from vixen.directory import Directory

def create_dummy_file(path):
    with open(path, 'w') as fp:
        fp.write("hello\n")

def make_data(root):
    base = join(root, 'test')
    os.makedirs(join(base, 'sub', 'subsub'))
    os.makedirs(join(base, 'sub2'))
    create_dummy_file(join(base, 'root.txt'))
    create_dummy_file(join(base, 'sub', 'sub.txt'))
    create_dummy_file(join(base, 'sub', 'subsub', 'subsub.txt'))
    create_dummy_file(join(base, 'sub2', 'sub2.txt'))


class TestDirectory(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.mkdtemp()
        self.root = join(self._temp, 'test')
        make_data(self._temp)

    def tearDown(self):
        shutil.rmtree(self._temp)

    def test_simple_directory(self):
        # Given
        # when
        d = Directory(path=self.root)

        # Then
        self.assertEqual(d.name, 'test')
        self.assertEqual(d.parent, None)
        self.assertEqual(d.relpath, '')
        self.assertEqual(len(d.files), 1)
        file_obj = d.files[0]
        self.assertEqual(file_obj.name, 'root.txt')
        self.assertEqual(file_obj.parent, d)
        self.assertEqual(file_obj.relpath, 'root.txt')

        self.assertEqual(len(d.directories), 2)
        sub_dir = d.directories[0]
        self.assertEqual(sub_dir.name, 'sub')
        self.assertEqual(sub_dir.parent, d)
        self.assertEqual(sub_dir.relpath, 'sub')
        file_obj = sub_dir.files[0]
        self.assertEqual(file_obj.name, 'sub.txt')
        self.assertEqual(file_obj.parent, sub_dir)
        self.assertEqual(file_obj.relpath, join('sub', 'sub.txt'))

        self.assertEqual(len(sub_dir.directories), 1)
        subsub_dir = sub_dir.directories[0]
        self.assertEqual(subsub_dir.relpath, join('sub', subsub_dir.name))


if __name__ == '__main__':
    unittest.main()
