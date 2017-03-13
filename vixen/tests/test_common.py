import os
import shutil
import tempfile
import unittest

from vixen.common import get_project_dir


class TestCommon(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)
        if 'VIXEN_ROOT' in os.environ:
            del os.environ['VIXEN_ROOT']

    def test_get_project_dir_default_makes_dir(self):
        # Given/When
        d = get_project_dir()

        # Then
        self.assertTrue(os.path.exists(d))
        self.assertTrue(os.path.isdir(d))

    def test_get_project_dir_honors_env_var(self):
        # Given
        root = os.path.join(self.root, 'vixen')
        os.environ['VIXEN_ROOT'] = root

        # When
        d = get_project_dir()

        # Then
        self.assertEqual(d, root)
        self.assertTrue(os.path.isdir(d))


if __name__ == '__main__':
    unittest.main()
