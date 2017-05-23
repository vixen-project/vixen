import mock
import os
import shutil
import sys
import tempfile
import unittest

from vixen import cli


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.orig_excepthook = sys.excepthook
        self.root = tempfile.mkdtemp()
        os.environ['VIXEN_ROOT'] = os.path.join(self.root, 'vixen')
        patcher = mock.patch('vixen.vixen_ui.main')
        self.mock = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        del os.environ['VIXEN_ROOT']
        if sys.platform.startswith('win'):
            try:
                shutil.rmtree(self.root)
            except WindowsError:
                pass
        else:
            shutil.rmtree(self.root)
        sys.excepthook = self.orig_excepthook

    def test_cli_calls_view_correctly(self):
        # When
        cli.main(args=[])

        # Then
        self.assertEqual(self.mock.call_count, 1)
        args, kw = self.mock.call_args
        self.assertEqual(kw['dev'], False)
        self.assertEqual(kw['port'], None)
        self.assertEqual(
            sorted(kw.keys()),
            ['dev', 'editor', 'port', 'ui', 'viewer', 'vixen']
        )

    def test_cli_parses_args(self):
        # When
        cli.main(args=['--dev', '--port', '8000'])

        # Then
        self.assertEqual(self.mock.call_count, 1)
        args, kw = self.mock.call_args
        self.assertEqual(kw['dev'], True)
        self.assertEqual(kw['port'], 8000)

    def test_cli_sets_sys_excepthook(self):
        # Given
        # When
        cli.main([])

        # Then
        self.assertEqual(sys.excepthook, cli._logging_excepthook)

if __name__ == '__main__':
    unittest.main()
