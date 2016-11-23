import csv
from os.path import basename, join, exists
import tempfile
import shutil

import unittest

from vixen.tests.test_directory import make_data, create_dummy_file
from vixen.project import Project, TagInfo, get_non_existing_filename, INT


class TestProjectBase(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.mkdtemp()
        self.root = join(self._temp, 'test')
        make_data(self._temp)

    def tearDown(self):
        shutil.rmtree(self._temp)


class TestProject(TestProjectBase):

    def test_simple_project(self):
        # Given, When
        p = Project(name='test', path=self.root)
        # We do not scan at this point.

        # Then
        self.assertEqual(p.name, 'test')
        self.assertEqual(p.root, None)
        self.assertEqual(len(p.tags), 1)
        self.assertEqual(p.tags[0].name, 'completed')
        self.assertEqual(p.tags[0].type, 'bool')
        self.assertEqual(len(p.media), 0)

    def test_project_scan_works(self):
        # Given
        p = Project(name='test', path=self.root)
        # When
        p.scan()
        # Then
        self.assertEqual(len(p.media), 5)
        m = p.media['root.txt']
        self.assertEqual(len(m.tags), 1)
        self.assertIn('completed', m.tags)
        m = p.media['sub/sub.txt']
        self.assertEqual(m.file_name, 'sub.txt')
        self.assertEqual(len(m.tags), 1)
        self.assertIn('completed', m.tags)

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
        self.assertEqual(len(p.root.files), 2)
        self.assertEqual(len(p.tags), 1)
        self.assertEqual(p.tags[0].name, 'completed')
        self.assertEqual(p.tags[0].type, 'bool')

        self.assertEqual(len(p.media), 5)
        m = p.media['root.txt']
        self.assertEqual(len(m.tags), 1)
        self.assertIn('completed', m.tags)
        m = p.media['sub/sub.txt']
        self.assertEqual(m.file_name, 'sub.txt')
        self.assertEqual(len(m.tags), 1)
        self.assertIn('completed', m.tags)

        # Ensure that the ctime and mtimes are saved.
        self.assertEqual(p.media['root.txt']._ctime,
                         p1.media['root.txt']._ctime)
        self.assertEqual(p.media['root.txt']._mtime,
                         p1.media['root.txt']._mtime)

    def test_export_to_csv(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()
        m = p.media['root.txt']
        m.tags['completed'] = True
        out_fname = tempfile.mktemp(dir=self.root, suffix='.csv')

        # When
        p.export_csv(out_fname)

        # Then
        reader = csv.reader(open(out_fname))
        cols = next(reader)
        expected = ['completed', 'ctime', 'mtime', 'path', 'size', 'type']
        self.assertEqual(cols, expected)
        row = next(reader)
        self.assertEqual(basename(row[3]), 'hello.py')
        self.assertEqual(row[0], 'False')
        row = next(reader)
        self.assertEqual(basename(row[3]), 'root.txt')
        self.assertEqual(row[0], 'True')
        row = next(reader)
        self.assertEqual(basename(row[3]), 'sub.txt')
        self.assertEqual(row[0], 'False')
        row = next(reader)
        self.assertEqual(basename(row[3]), 'subsub.txt')
        self.assertEqual(row[0], 'False')

    def test_refresh_updates_new_media(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()
        self.assertEqual(len(p.media), 5)
        m = p.media['root.txt']
        orig_size = m.size
        # Change this.
        m.tags['completed'] = True
        create_dummy_file(join(self.root, 'sub', 'sub1.txt'))
        with open(m.path, 'w') as fp:
            fp.write('hello world\n')

        # When
        p.refresh()

        # Then
        m = p.media['root.txt']
        self.assertEqual(m.tags['completed'], True)
        self.assertEqual(len(p.media), 6)
        self.assertTrue(m.size > orig_size)
        m = p.media['sub/sub1.txt']
        self.assertEqual(m.tags['completed'], False)

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
            self.assertTrue('completed' not in m.tags)

    def test_update_tags_handles_type_changes_for_existing_tag(self):
        # Given
        tags = [TagInfo(name='completed', type='bool'),
                TagInfo(name='foo', type='string')]

        p = Project(name='test', path=self.root, tags=tags)
        p.scan()
        list(p.media.values())[0].tags['completed'] = True
        list(p.media.values())[0].tags['foo'] = 'hello world'
        # When
        new_tags = [
            TagInfo(name='foo', type='int'),
            TagInfo(name='completed', type='bool')
        ]
        p.update_tags(new_tags)

        # Then
        self.assertEqual(p.tags, new_tags)
        self.assertEqual(list(p.media.values())[0].tags['completed'], True)
        self.assertEqual(list(p.media.values())[0].tags['foo'], 0)
        for m in p.media.values():
            self.assertEqual(type(m.tags['completed']), bool)
            self.assertEqual(m.tags['foo'], 0)

    def test_get_non_existing_filename(self):
        # Given
        f = join(self.root, 'root.txt')

        # When
        fname = get_non_existing_filename(f)

        # Then
        self.assertEqual(fname, join(self.root, 'root_a.txt'))

    def test_changing_name_updates_save_file(self):
        # Given
        save_file = join(self.root, 'test_save.vxn')
        p = Project(name='test', path=self.root, save_file=save_file)
        p.scan()
        p.save()

        # When
        p.name = 'new name'

        # Then
        new_save_file = join(self.root, 'new_name.vxn')
        self.assertEqual(p.save_file, new_save_file)
        self.assertTrue(exists(p.save_file))

    def test_setting_root_extensions_limits_files(self):
        # Given
        p = Project(name='test', path=self.root, extensions=['.py'])

        # When
        p.scan()

        # Then
        self.assertEqual(len(p.media), 1)
        self.assertEqual(list(p.media.keys())[0], 'hello.py')


class TestSearchMedia(TestProjectBase):
    def test_query_schema_is_setup_correctly(self):
        # Given
        p = Project(name='test', path=self.root)

        # When
        p.scan()

        # Then
        schema = p._query_parser.schema
        items = schema.items()
        from whoosh import fields
        self.assertIn(('path', fields.TEXT()), items)
        self.assertIn(('ctime', fields.DATETIME()), items)
        self.assertIn(('completed', fields.BOOLEAN()), items)
        self.assertIn(('size', INT), items)

    def test_query_schema_is_updated_when_tags_are_added(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()

        # When
        p.add_tags([TagInfo(name='new_tag', type='int')])

        # Then
        schema = p._query_parser.schema
        items = schema.items()
        self.assertIn(('new_tag', INT), items)

    def test_simple_search_works(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()

        # When
        result = list(p.search("hello"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].file_name, "hello.py")

    def test_logical_operations_in_search(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()

        # When
        result = list(p.search("hello subsub"))

        # Then
        self.assertEqual(len(result), 0)

        # When
        result = list(p.search("hello AND subsub"))

        # Then
        self.assertEqual(len(result), 0)

        # When
        result = list(p.search("hello OR subsub"))

        # Then
        self.assertEqual(len(result), 2)
        names = sorted(x.file_name for x in result)
        self.assertEqual(names, ["hello.py", "subsub.txt"])

        # When
        result = list(p.search("hello AND NOT .py"))

        # Then
        self.assertEqual(len(result), 0)

        # When
        result = list(p.search("NOT .txt"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].file_name, "hello.py")

    def test_tags_in_search_work_correctly(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()

        # When
        result = list(p.search("path:hello.py"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].file_name, "hello.py")

        # When
        result = list(p.search("file_name:test"))

        # Then
        self.assertEqual(len(result), 0)

        # When
        result = list(p.search("path:test"))

        # Then
        # Should get everything since everything is inside the
        # test directory!
        self.assertEqual(len(result), 5)

        # When
        p.media['root.txt'].tags['completed'] = True
        result = list(p.search("completed:1"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].file_name, "root.txt")

        # When
        result = list(p.search("completed:yes"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].file_name, "root.txt")

        # When
        result = list(p.search("completed:0"))

        # Then
        self.assertEqual(len(result), 4)
        self.assertNotIn('root.txt', [x.file_name for x in result])

    def test_numeric_tags_and_ranges_are_searchable(self):
        # Given
        tags = [
            TagInfo(name='fox', type='int'),
            TagInfo(name='age', type='float')
        ]
        p = Project(name='test', path=self.root, tags=tags)
        p.scan()
        p.media[join('sub2', 'sub2.txt')].tags['fox'] = 1

        # When
        result = list(p.search("fox:1"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].file_name, 'sub2.txt')

        # When
        result = list(p.search("fox:>=1"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].file_name, 'sub2.txt')

        # When
        result = list(p.search("fox:<1"))

        # Then
        self.assertEqual(len(result), 4)
        self.assertNotIn('sub2.txt', [x.file_name for x in result])

        # When
        p.media['root.txt'].tags['age'] = 50.5
        result = list(p.search("age:50.5"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].file_name, 'root.txt')

        # When
        result = list(p.search("age:>50"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].file_name, 'root.txt')



if __name__ == '__main__':
    unittest.main()
