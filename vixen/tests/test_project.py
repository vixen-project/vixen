# -*- coding: utf-8 -*-
import datetime
import io
import os
from os.path import basename, join, exists
import tempfile
from textwrap import dedent
import time
import shutil
import sys

import unittest
from whoosh.fields import TEXT

from vixen.tests.test_directory import make_data, create_dummy_file
from vixen.project import Project, TagInfo, get_non_existing_filename, INT
from vixen.processor import CommandFactory

if sys.version_info >= (3, 0):
    import csv
else:
    import backports.csv as csv


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
        self.assertEqual(p.number_of_files, 0)

    def test_version_1_loads_correctly(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()
        fname = join(self.root, 'test.vxn')
        p._save_as_v1(fname)

        # When
        p = Project()
        p.load(fname)

        # Then
        self.assertEqual(p.number_of_files, 5)
        m = p.get('root.txt')
        self.assertEqual(m.relpath, 'root.txt')
        self.assertEqual(m.type, 'text')
        self.assertEqual(len(m.tags), 1)
        self.assertIn('completed', m.tags)
        relpath = join('sub', 'sub.txt')
        m = p.get(relpath)
        self.assertEqual(m.file_name, 'sub.txt')
        self.assertEqual(m.relpath, relpath)
        self.assertEqual(len(m.tags), 1)
        self.assertIn('completed', m.tags)
        d = p.root.directories[0]
        self.assertEqual(d.relpath, d.name)

    def test_project_scan_works(self):
        # Given
        p = Project(name='test', path=self.root)
        # When
        p.scan()
        # Then
        self.assertEqual(p.number_of_files, 5)
        m = p.get('root.txt')
        self.assertEqual(m.relpath, 'root.txt')
        self.assertEqual(m.type, 'text')
        self.assertEqual(len(m.tags), 1)
        self.assertIn('completed', m.tags)
        m = p.get(join('sub', 'sub.txt'))
        self.assertEqual(m.file_name, 'sub.txt')
        self.assertEqual(len(m.tags), 1)
        self.assertIn('completed', m.tags)

    def test_project_copy_does_not_copy_data(self):
        # Given
        tags = [TagInfo(name='completed', type='bool'),
                TagInfo(name='comment', type='string')]
        p = Project(name='test', path=self.root,
                    extensions=['.txt', '.py'], tags=tags)
        cf = CommandFactory(dest=self.root,
                            input_extension='.py',
                            output_extension='.rst',
                            command='echo $input $output')
        p.processors = [cf]
        p.scan()
        # Update the _done trait the processors to check if it is copied.
        m = p.get('root.txt')
        cf._done[m.path] = True

        # When
        p1 = p.copy()

        # Then
        self.assertEqual(p.number_of_files, 5)
        self.assertEqual(p1.number_of_files, 0)
        self.assertEqual(p1.name, p.name + ' copy')
        self.assertEqual(p1.path, p.path)
        tag_info = [(x.name, x.type) for x in p.tags]
        tag_info1 = [(x.name, x.type) for x in p1.tags]
        self.assertEqual(tag_info, tag_info1)
        self.assertEqual(p1.extensions, p.extensions)
        self.assertEqual(len(p1._relpath2index), 0)
        self.assertEqual(len(p1.processors), len(p.processors))
        p1_proc_traits = p1.processors[0].trait_get()
        p1_proc_traits.pop('_done')
        p_proc_traits = p.processors[0].trait_get()
        p_proc_traits.pop('_done')
        self.assertEqual(p1_proc_traits, p_proc_traits)
        self.assertEqual(len(p.processors[0]._done), 1)
        self.assertEqual(len(p1.processors[0]._done), 0)

        # When
        p.tags[0].type = 'int'

        # Then
        # This just checks that p1's tags are not a reference to p's.
        self.assertEqual(p1.tags[0].type, 'bool')

    def test_load_should_restore_saved_state(self):
        # Given
        p = Project(name='test', description='Test', path=self.root)
        p.scan()
        out_fname = tempfile.mktemp(dir=self.root)
        out = open(out_fname, 'wb')

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

        self.assertEqual(p.number_of_files, 5)
        m = p.get('root.txt')
        self.assertEqual(len(m.tags), 1)
        self.assertIn('completed', m.tags)
        m = p.get(join('sub', 'sub.txt'))
        self.assertEqual(m.file_name, 'sub.txt')
        self.assertEqual(len(m.tags), 1)
        self.assertIn('completed', m.tags)

        # Ensure that the ctime and mtimes are saved.
        self.assertEqual(p.get('root.txt')._ctime,
                         p1.get('root.txt')._ctime)
        self.assertEqual(p.get('root.txt')._mtime,
                         p1.get('root.txt')._mtime)

    def test_refresh_removes_non_existing_file_entries(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()
        # When
        relpath = 'hello.py'
        m = p.get(relpath)
        os.remove(m.path)
        p.refresh()

        # Then
        #self.assertEqual(p.number_of_files, 4)
        self.assertFalse(p.has_media(relpath))
        self.assertFalse(relpath in p._media)
        self.assertFalse(relpath in p._relpath2index)
        for key in p._data:
            self.assertEqual(len(p._data[key]), 4)
        for key in p._tag_data:
            self.assertEqual(len(p._tag_data[key]), 4)
        files = [x.name for x in p.root.files]
        self.assertTrue(relpath not in files)
        # Check if the database is consistent.
        for rp in p._relpath2index.keys():
            m = p.get(rp)
            self.assertEqual(m.relpath, rp)

    def test_export_to_csv_with_unicode(self):
        # Given
        tags = [TagInfo(name='completed', type='bool'),
                TagInfo(name='comment', type='string')]

        p = Project(name='test', path=self.root, tags=tags)
        p.scan()
        m = p.get('root.txt')
        m.tags['completed'] = True
        m.tags['comment'] = u'hello, world; न Kévin'
        out_fname = tempfile.mktemp(dir=self.root, suffix='.csv')

        # When
        p.export_csv(out_fname)

        # Then
        with io.open(out_fname, newline='', encoding='utf-8') as fp:
            reader = csv.reader(fp)
            cols = next(reader)
            expected = [
                'comment', 'completed', 'ctime', 'file_name', 'mtime', 'path',
                'relpath', 'size', 'type'
            ]
            self.assertEqual(cols, expected)
            expected = {'hello.py': 'False', 'root.txt': 'True'}
            data = [next(reader), next(reader), next(reader), next(reader)]
            data = sorted(data, key=lambda x: x[6])
            row = data[0]
            self.assertEqual(basename(row[5]), u'hello.py')
            self.assertEqual(row[1], u'False')
            self.assertEqual(row[0], u'')
            row = data[1]
            self.assertEqual(basename(row[5]), u'root.txt')
            self.assertEqual(row[1], u'True')
            self.assertEqual(row[0], u'hello, world; न Kévin')
            row = data[2]
            self.assertTrue(basename(row[5]).startswith(u'sub'))
            self.assertEqual(row[1], u'False')
            self.assertEqual(row[0], u'')
            row = data[3]
            self.assertTrue(basename(row[5]).startswith(u'sub'))
            self.assertEqual(row[1], u'False')
            self.assertEqual(row[0], u'')

    def test_refresh_updates_new_media(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()
        self.assertEqual(p.number_of_files, 5)
        m = p.get('root.txt')
        orig_size = m.size
        # Change this.
        m.tags['completed'] = True
        create_dummy_file(join(self.root, 'sub', 'sub1.txt'))
        with open(m.path, 'w') as fp:
            fp.write('hello world\n')

        # When
        p.refresh()

        # Then
        m = p.get('root.txt')
        self.assertEqual(m.tags['completed'], True)
        self.assertEqual(p.number_of_files, 6)
        self.assertTrue(m.size > orig_size)
        m = p.get(join('sub', 'sub1.txt'))
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
        for key in p.keys():
            m = p.get(key)
            self.assertEqual(m.tags['foo'], '')
            self.assertTrue('completed' not in m.tags)

    def test_update_tags_works_without_scan(self):
        # Given
        p = Project(name='test', path=self.root)
        # When
        new_tags = [
            TagInfo(name='foo', type='string')
        ]
        p.update_tags(new_tags)

        # Then
        self.assertEqual(p.tags, new_tags)
        self.assertEqual(
            sorted(x.name for x in new_tags),
            sorted(p._tag_data.keys())
        )

    def test_update_tags_handles_type_changes_for_existing_tag(self):
        # Given
        tags = [TagInfo(name='completed', type='bool'),
                TagInfo(name='foo', type='string')]

        p = Project(name='test', path=self.root, tags=tags)
        p.scan()
        key = 'root.txt'
        m = p.get(key)
        m.tags['completed'] = True
        m.tags['foo'] = 'hello world'

        # When
        new_tags = [
            TagInfo(name='foo', type='int'),
            TagInfo(name='completed', type='bool')
        ]
        p.update_tags(new_tags)

        # Then
        self.assertEqual(p.tags, new_tags)
        self.assertEqual(m.tags['completed'], True)
        self.assertEqual(m.tags['foo'], 0)
        for key in p.keys():
            m = p.get(key)
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
        self.assertEqual(p.number_of_files, 1)
        self.assertEqual(list(p.keys())[0], 'hello.py')

    def _write_csv(self, data):
        fname = join(self._temp, 'data.csv')
        with io.open(fname, 'w', encoding='utf-8') as fp:
            fp.write(data)
        return fname

    def test_import_csv_fails_with_bad_csv_header(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()
        data = dedent(u"""\
        /blah/blah,1
        """)
        csv = self._write_csv(data)

        # When
        success, err = p.import_csv(csv)

        # Then
        self.assertFalse(success)

        # Given
        data = dedent(u"""\
        relpath,fox
        root.txt,1
        """)
        csv = self._write_csv(data)

        # When
        success, err = p.import_csv(csv)

        # Then
        self.assertFalse(success)

    def test_import_csv_works(self):
        # Given
        p = Project(name='test', path=self.root)
        p.add_tags([TagInfo(name='fox', type='int')])
        p.scan()
        data = dedent(u"""\
        path,fox,junk
        %s,2,hello
        %s,1,bye
        """ % (join(self.root, 'root.txt'), join(self.root, 'hello.py')))
        csv = self._write_csv(data)

        # Get one of the paths to see if cached media are handled correctly.
        self.assertEqual(p.get('root.txt').tags['fox'], 0)

        # When
        success, err = p.import_csv(csv)

        # Then
        self.assertTrue(success)
        self.assertEqual(p.get('root.txt').tags['fox'], 2)
        self.assertEqual(p.get('hello.py').tags['fox'], 1)


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

        # When
        p.add_tags([TagInfo(name='tag1', type='text')])

        # Then
        schema = p._query_parser.schema
        items = schema.items()
        self.assertIn(('tag1', TEXT()), items)

    def test_simple_search_works(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()

        # When
        result = list(p.search("hello"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "hello.py")
        self.assertEqual(result[0][1], "hello.py")

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
        names = sorted(x[0] for x in result)
        self.assertEqual(names, ["hello.py", "subsub.txt"])

        # When
        result = list(p.search("hello AND NOT .py"))

        # Then
        self.assertEqual(len(result), 0)

        # When
        result = list(p.search("NOT .txt"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "hello.py")

    def test_tags_in_search_work_correctly(self):
        # Given
        p = Project(name='test', path=self.root)
        p.scan()

        # When
        result = list(p.search("path:hello.py"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "hello.py")

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
        p.get('root.txt').tags['completed'] = True
        result = list(p.search("completed:1"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "root.txt")

        # When
        result = list(p.search("completed:yes"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "root.txt")

        # When
        result = list(p.search("completed:0"))

        # Then
        self.assertEqual(len(result), 4)
        self.assertNotIn('root.txt', [x[0] for x in result])

    def test_numeric_tags_and_ranges_are_searchable(self):
        # Given
        tags = [
            TagInfo(name='fox', type='int'),
            TagInfo(name='age', type='float')
        ]
        p = Project(name='test', path=self.root, tags=tags)
        p.scan()
        p.get(join('sub2', 'sub2.txt')).tags['fox'] = 1

        # When
        result = list(p.search("fox:1"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'sub2.txt')

        # When
        # This is an exclusive range, i.e. only the value 1 is searched.
        result = list(p.search("fox:{0 TO 2}"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'sub2.txt')

        # When
        # Here we have 1 and 2.
        result = list(p.search("fox:{0 TO 2]"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'sub2.txt')

        # When
        result = list(p.search("fox:>=1"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'sub2.txt')

        # When
        result = list(p.search("fox:<1"))

        # Then
        self.assertEqual(len(result), 4)
        self.assertNotIn('sub2.txt', [x[0] for x in result])

        # When
        p.get('root.txt').tags['age'] = 50.5
        result = list(p.search("age:50.5"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'root.txt')

        # When
        result = list(p.search("age:>50"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'root.txt')

    def test_date_ranges_are_searchable(self):
        # Given
        fname = join(self.root, 'root.txt')
        dt = datetime.datetime(2015, 1, 1)
        ts = time.mktime(dt.timetuple())
        os.utime(fname, (ts, ts))
        p = Project(name='test', path=self.root)
        p.scan()

        # When
        result = list(p.search("mtime:2015"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'root.txt')

        # When
        fname = join(self.root, 'hello.py')
        dt = datetime.datetime(2015, 2, 1)
        ts = time.mktime(dt.timetuple())
        os.utime(fname, (ts, ts))
        p.refresh()

        result = list(p.search("mtime:2015"))

        # Then
        self.assertEqual(len(result), 2)
        names = sorted(x[0] for x in result)
        self.assertEqual(names, ['hello.py', 'root.txt'])

        # When
        result = list(p.search("mtime:201501"))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'root.txt')

        # When
        result = list(p.search("mtime:[jan 2015 TO feb 2015]"))

        # Then
        self.assertEqual(len(result), 2)
        names = sorted(x[0] for x in result)
        self.assertEqual(names, ['hello.py', 'root.txt'])

        # When
        result = list(p.search("mtime:>20150202"))

        # Then
        self.assertEqual(len(result), 3)
        names = sorted(x[0] for x in result)
        self.assertNotIn('hello.py', names)
        self.assertNotIn('root.txt', names)

    def test_phrases_are_searchable(self):
        # Given
        tags = [
            TagInfo(name='comment', type='string'),
        ]
        p = Project(name='test', path=self.root, tags=tags)
        p.scan()
        p.get('root.txt').tags['comment'] = 'Hola how are you?'

        # When
        result = list(p.search('comment:"hola how"'))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'root.txt')


if __name__ == '__main__':
    unittest.main()
