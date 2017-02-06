import unittest
import tempfile
import os

from vixen.media import get_media_data, find_type, MediaData, Media


class TestMedia(unittest.TestCase):
    def setUp(self):
        fname = tempfile.mktemp(suffix='.txt')
        with open(fname, 'w') as fp:
            fp.write('Hello world\n')

        self.fname = fname

    def tearDown(self):
        os.remove(self.fname)

    def test_find_type(self):
        # Given
        cases = [
            ('test.gif', 'image'), ('test.TIFF', 'image'),
            ('test.avi', 'video'), ('test.MPEG', 'video'),
            ('test.mpg', 'video'), ('test.webm', 'video'),
            ('test.ogg', 'audio'), ('test.aiff', 'audio'),
            ('test.HTML', 'html'), ('test.htm', 'html'),
            ('test.c', 'text'), ('test.md', 'text'),
            ('test.py', 'text'), ('test.rst', 'text'),
            ('test.pdf', 'pdf'),
            ('test.xxx', 'unknown'),
        ]
        # When/then
        for fname, expected in cases:
            self.assertEqual(find_type(fname), expected)

    def test_get_media_data(self):
        # Given
        fname = self.fname

        # When
        relpath = os.path.basename(fname)
        data = get_media_data(fname, relpath)

        # Then
        self.assertTrue(isinstance(data, MediaData))
        self.assertEqual(data.type, 'text')
        self.assertTrue(data.size > 0)
        self.assertEqual(data.relpath, relpath)
        self.assertEqual(data.path, fname)
        self.assertEqual(data.file_name, relpath)

    def test_media_from_path(self):
        # Given
        fname = self.fname
        relpath = os.path.basename(fname)

        # When
        m = Media.from_path(fname, relpath)

        # Then
        self.assertEqual(m.type, 'text')
        self.assertTrue(m.size > 0)
        self.assertEqual(m.relpath, relpath)
        self.assertEqual(m.path, fname)
        self.assertEqual(m.file_name, relpath)


if __name__ == '__main__':
    unittest.main()
