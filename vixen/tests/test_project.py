import csv
import os
from os.path import basename, dirname, join
import tempfile
import shutil

import unittest

from vixen.tests.test_directory import make_data, create_dummy_file
from vixen.project import Project, TagInfo


class TestProject(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.mkdtemp()
        self.root = join(self._temp, 'test')
        make_data(self._temp)

    def tearDown(self):
        shutil.rmtree(self._temp)

    def test_simple_project(self):
        # Given, When
        p = Project(name='test', path=self.root)
        # We do not scan at this point.

        # Then
        self.assertEqual(p.name, 'test')
        self.assertEqual(p.root, None)
        self.assertEqual(len(p.tags), 1)
        self.assertEqual(p.tags[0].name, 'processed')
        self.assertEqual(p.tags[0].type, 'bool')
        self.assertEqual(len(p.media), 0)

    def test_project_scan_works(self):
        # Given
        p = Project(name='test', path=self.root)
        # When
        p.scan()
        # Then
        self.assertEqual(len(p.media), 4)
        m = p.media['root.txt']
        self.assertEqual(len(m.tags), 1)
        self.assertIn('processed', m.tags)
        m = p.media['sub/sub.txt']
        self.assertEqual(m.file_name, 'sub.txt')
        self.assertEqual(len(m.tags), 1)
        self.assertIn('processed', m.tags)

    def test_load_should_restore_saved_state(self):
        # Given
        p = Project(name='test', description='Test', path=self.root)
        p.scan()
        out_fname = tempfile.mktemp(dir=self.root)
        out = open(out_fname, 'w')

        # When
        p.save_as(out)
        p1 = Project()
        p1.load(out_fname)

        # Then
        self.assertEqual(p.name, 'test')
        self.assertEqual(p.description, 'Test')
        self.assertEqual(p.root.name, 'test')
        self.assertEqual(len(p.root.directories), 2)
        self.assertEqual(len(p.root.files), 1)
        self.assertEqual(len(p.tags), 1)
        self.assertEqual(p.tags[0].name, 'processed')
        self.assertEqual(p.tags[0].type, 'bool')

        self.assertEqual(len(p.media), 4)
        m = p.media['root.txt']
        self.assertEqual(len(m.tags), 1)
        self.assertIn('processed', m.tags)
        m = p.media['sub/sub.txt']
        self.assertEqual(m.file_name, 'sub.txt')
        self.assertEqual(len(m.tags), 1)
        self.assertIn('processed', m.tags)

    def test_export_to_csv(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()
        m = p.media['root.txt']
        m.tags['processed'] = True
        out_fname = tempfile.mktemp(dir=self.root, suffix='.csv')
        out = open(out_fname, 'w')

        # When
        p.export_csv(out_fname)

        # Then
        reader = csv.reader(open(out_fname))
        cols = reader.next()
        expected = ['date', 'path', 'processed', 'size', 'time']
        self.assertEqual(cols, expected)
        row = reader.next()
        self.assertEqual(basename(row[1]), 'root.txt')
        self.assertEqual(row[2], 'True')
        row = reader.next()
        self.assertEqual(basename(row[1]), 'sub.txt')
        self.assertEqual(row[2], 'False')
        row = reader.next()
        self.assertEqual(basename(row[1]), 'subsub.txt')
        self.assertEqual(row[2], 'False')

    def test_scan_updates_new_media(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()
        self.assertEqual(len(p.media), 4)
        m = p.media['root.txt']
        # Change this.
        m.tags['processed'] = True
        create_dummy_file(join(self.root, 'sub', 'sub1.txt'))

        # When
        p.refresh()

        # Then
        m = p.media['root.txt']
        self.assertEqual(m.tags['processed'], True)
        self.assertEqual(len(p.media), 5)
        m = p.media['sub/sub1.txt']
        self.assertEqual(m.tags['processed'], False)

    def test_update_tags_updates_existing_media(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()
        # When
        new_tags = [
            TagInfo(name='foo', type='string')
        ]
        p.update_tags(new_tags)

        # Then
        self.assertEqual(p.tags, new_tags)
        for m in p.media.values():
            self.assertEqual(m.tags['foo'], '')
            self.assertTrue('processed' not in m.tags)

    def test_update_tags_handles_type_changes_for_existing_tag(self):
        # Given
        tags = [TagInfo(name='processed', type='bool'),
                TagInfo(name='foo', type='string')]

        p = Project(name='test', path=self.root, tags=tags)
        p.scan()
        p.media.values()[0].tags['processed'] = True
        p.media.values()[0].tags['foo'] = 'hello world'
        # When
        new_tags = [
            TagInfo(name='foo', type='int'),
            TagInfo(name='processed', type='bool')
        ]
        p.update_tags(new_tags)

        # Then
        self.assertEqual(p.tags, new_tags)
        self.assertEqual(p.media.values()[0].tags['processed'], True)
        self.assertEqual(p.media.values()[0].tags['foo'], 0)
        for m in p.media.values():
             self.assertEqual(type(m.tags['processed']), bool)
             self.assertEqual(m.tags['foo'], 0)

if __name__ == '__main__':
    unittest.main()
