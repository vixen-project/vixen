import logging
import os
import mock
import unittest

import vixen
from vixen.processor import PythonFunctionFactory
from vixen.project import Project, TagInfo
from vixen.vixen import VixenUI, Vixen, UIErrorHandler, is_valid_tag
from vixen.vixen_ui import get_html, get_html_file

from vixen.tests.test_project import TestProjectBase


def test_is_valid_tag():
    assert is_valid_tag('hello_world') == (True, 'OK')
    assert is_valid_tag('for') == (True, 'OK')
    assert is_valid_tag('hello;world') == (True, 'OK')
    assert is_valid_tag('hello-world') == (True, 'OK')
    assert is_valid_tag('hello+world') == (True, 'OK')
    assert is_valid_tag('hello*world') == (True, 'OK')
    assert is_valid_tag('hello:world') == (True, 'OK')
    assert (is_valid_tag('hello world') ==
            (False, 'Names cannot contain spaces'))
    assert (is_valid_tag('_world') ==
            (False, 'Names cannot start with _'))


class MockRecord():
    def __init__(self, name, message):
        self.name = name
        self.message = message


class TestUIErrorHandler(unittest.TestCase):
    def setUp(self):
        self.mock_ui = mock.MagicMock()
        self.h = UIErrorHandler(self.mock_ui)

    def test_emit_catches_general_error(self):
        # Given
        record = MockRecord(name='name', message='favicon.ico')
        # When
        self.h.emit(record)

        # Then
        self.assertTrue(self.mock_ui.notify_user.call_count, 1)

    def test_emit_catches_access_error_non_favicon(self):
        # Given
        record = MockRecord(name='tornado.access', message='hello')
        # When
        self.h.emit(record)

        # Then
        self.assertTrue(self.mock_ui.notify_user.call_count, 1)

    def test_emit_skips_favicon_errors(self):
        # Given
        record = MockRecord(name='tornado.access',
                            message='hello I have favicon.ico')
        # When
        self.h.emit(record)

        # Then
        self.mock_ui.notify_user.assert_not_called()

        # Given
        record = MockRecord(name='tornado.application',
                            message='hello I have favicon.ico')
        # When
        self.h.emit(record)

        # Then
        self.mock_ui.notify_user.assert_not_called()


class TestVixenBase(TestProjectBase):
    def setUp(self):
        super(TestVixenBase, self).setUp()
        patch_proj = mock.patch(
            'vixen.project.get_project_dir',
            mock.Mock(return_value=self._temp)
        )
        patch_proj.start()
        self.addCleanup(patch_proj.stop)
        patcher1 = mock.patch(
            'vixen.vixen.get_project_dir',
            mock.Mock(return_value=self._temp)
        )
        patcher1.start()
        self.addCleanup(patcher1.stop)


class TestVixen(TestVixenBase):

    def test_load(self):
        # Given
        vixen = Vixen()

        # When
        vixen.load()

        # Then
        self.assertEqual(len(vixen.projects), 1)
        self.assertEqual(vixen.projects[0].name, '__hidden__')

        # When
        p = Project(
            name='test', path=self.root,
            description='desc', extensions=['.py', '.txt']
        )
        p.scan()
        p.save()
        vixen.add(p)

        # Then
        self.assertEqual(len(vixen.projects), 1)
        self.assertEqual(vixen.projects[0].name, 'test')

        # Given
        vixen.save()
        vixen = Vixen()
        vixen.load()

        # Then
        self.assertEqual(len(vixen.projects), 1)
        p = vixen.projects[0]
        self.assertEqual(p.name, 'test')
        self.assertEqual(p.number_of_files, 0)

        # When
        p.load()

        # Then
        self.assertEqual(p.number_of_files, 5)
        m = p.get('root.txt')
        self.assertEqual(m.relpath, 'root.txt')
        self.assertEqual(m.type, 'text')
        self.assertEqual(len(m.tags), 1)


class TestProjectEditor(TestVixenBase):

    def setUp(self):
        super(TestProjectEditor, self).setUp()
        ui = VixenUI()
        p = Project(
            name='test', path=self.root,
            description='desc', extensions=['.py', '.txt']
        )
        p.scan()
        ui.vixen.projects.append(p)
        self.ui = ui
        self.p = p

    def test_ui_edit(self):
        # Given
        ui, p = self.ui, self.p
        editor = ui.editor

        # When
        ui.edit(p)

        # Then
        self.assertEqual(editor.project, p)
        self.assertEqual(editor.name, p.name)
        self.assertEqual(editor.description, p.description)
        result = [x.__dict__ for x in editor.tags]
        expected = [x.__dict__ for x in p.tags]
        self.assertEqual(result, expected)
        self.assertEqual(editor.extensions, p.extensions)

    def test_add_remove_tag(self):
        # Given
        ui = self.ui
        editor = ui.editor

        # When
        ui.edit(self.p)
        nt = len(editor.tags)
        editor.add_tag('tag1, tag2')

        # Then
        result = [x.name for x in editor.tags[nt:]]
        self.assertEqual(result, ['tag1', 'tag2'])

        # When
        editor.remove_tag(nt)
        self.assertEqual(editor.tags[-1].name, 'tag2')
        self.assertEqual(editor.tags[-2].name, 'completed')

    def test_add_bad_tag_shows_error(self):
        # Given
        ui = self.ui
        editor = ui.editor

        # When
        ui.edit(self.p)
        nt = len(editor.tags)
        n_msg = ui.message[-1] if ui.message else 0
        editor.add_tag('hello world, _hello')

        # Then
        self.assertEqual(len(editor.tags), nt)
        msg = ui.message
        self.assertEqual(msg[1:], ('error', n_msg + 1))
        self.assertTrue('Error in the following tag names' in msg[0])
        self.assertTrue('"hello world":' in msg[0])
        self.assertTrue('"_hello":' in msg[0])
        self.assertTrue('spaces' in msg[0].lower())
        self.assertTrue('cannot start with _' in msg[0].lower())

    def test_move_tag(self):
        # Given
        ui = self.ui
        editor = ui.editor

        def _get_tags():
            return [x.name for x in editor.tags]

        ui.edit(self.p)
        editor.add_tag('tag1, tag2')
        assert _get_tags() == ['completed', 'tag1', 'tag2']

        # When
        editor.move_tag_up(0)
        # Then
        assert _get_tags() == ['completed', 'tag1', 'tag2']
        # When
        editor.move_tag_up(1)
        # Then
        assert _get_tags() == ['tag1', 'completed', 'tag2']
        # When
        editor.move_tag_up(2)
        # Then
        assert _get_tags() == ['tag1', 'tag2', 'completed']
        # When
        editor.move_tag_down(2)
        # Then
        assert _get_tags() == ['tag1', 'tag2', 'completed']
        # When
        editor.move_tag_down(1)
        # Then
        assert _get_tags() == ['tag1', 'completed', 'tag2']
        # When
        editor.move_tag_down(0)
        # Then
        assert _get_tags() == ['completed', 'tag1', 'tag2']

    def test_add_remove_extension(self):
        # Given
        ui = self.ui
        editor = ui.editor

        # When
        ui.edit(self.p)
        editor.add_extension('.c, .h')

        # Then
        self.assertEqual(
            sorted(editor.extensions), ['.c', '.h', '.py', '.txt']
        )

        # When
        editor.remove_extension(3)
        self.assertEqual(
            sorted(editor.extensions), ['.c', '.py', '.txt']
        )

    def test_find_extensions(self):
        # Given
        ui = self.ui
        editor = ui.editor

        # When
        ui.edit(self.p)
        editor.find_extensions()

        # Then
        self.assertSequenceEqual(
            sorted(editor.available_exts), ['.py', '.txt']
        )

    def test_apply(self):
        # Given
        ui = self.ui
        editor = ui.editor
        p = self.p

        # When
        ui.edit(p)
        editor.name = 'xxx'
        editor.description = 'xxx'
        editor.extensions = ['.txt']
        editor.add_tag('tag1')
        editor.apply()

        # Then
        self.assertEqual(p.name, 'xxx')
        self.assertEqual(p.description, 'xxx')
        self.assertEqual(p.extensions, ['.txt'])
        self.assertEqual(p.tags[-1].name, 'tag1')

    def test_check_processor(self):
        # Given
        ui = self.ui
        editor = ui.editor
        p = self.p

        # When
        ui.edit(p)
        editor.add_processor('python')

        # Then
        self.assertEqual(editor.processors[-1].name,
                         'PythonFunctionFactory')

        # When
        proc = editor.processors[-1]
        from textwrap import dedent
        code = dedent("""
        def process(relpath, media, dest):
            media.tags['completed'] = True
        """)
        proc.code = code
        editor.check_processor(proc)
        editor.test_job[0].thread.join()

        # Then
        key = list(p.keys())[0]
        m = p.get(key)
        self.assertEqual(m.tags['completed'], True)

        # When
        editor.remove_processor(0)

        # Then
        self.assertEqual(len(editor.processors), 0)


class TestVixenUI(TestVixenBase):

    def test_miscellaneous(self):
        # Given/When
        ui = VixenUI()

        # Then
        self.assertEqual(ui.version, vixen.__version__)
        fname = ui.docs
        self.assertTrue(
            os.path.basename(fname) in ['index.html', 'vixen.readthedocs.io']
        )

        # When
        ui.mode = 'view'
        ui.home()

        # Then
        self.assertEqual(ui.mode, 'edit')

        # When
        ctx = ui.get_context()

        # Then
        self.assertEqual(sorted(ctx.keys()),
                         ['editor', 'ui', 'viewer', 'vixen'])

    def test_messages(self):
        # Given.
        ui = VixenUI()

        # When
        ui.error('ERROR')

        # Then
        self.assertEqual(ui.message, ('ERROR', 'error', 0))

        # When
        ui.info('INFO')

        # Then
        self.assertEqual(ui.message, ('INFO', 'info', 1))

        # When
        ui.success('SUCCESS')

        # Then
        self.assertEqual(ui.message, ('SUCCESS', 'success', 2))

    @mock.patch('vixen.vixen.logger')
    def test_vixen_ui_log(self, logger):
        # Given
        ui = VixenUI()

        # When
        ui.log('msg', 'info')

        # Then
        logger.info.assert_called_with('msg')

        # When
        ui.log('err', 'error')

        # Then
        logger.error.assert_called_with('err')

        # When
        ui.log('err', 'blah')

        # Then
        logger.error.assert_called_with('Unknown message kind: %s', 'blah')
        logger.info.assert_called_with('err')

    def test_logging_handler_is_setup_correctly(self):
        # Given
        ui = VixenUI()

        # When
        m = mock.MagicMock()
        with mock.patch('vixen.vixen.logging.getLogger', return_value=m) as p:
            ui.setup_logging_handler()

        # Then
        p.assert_called_once_with()
        self.assertEqual(m.addHandler.call_count, 1)
        args = m.addHandler.call_args[0]
        obj = args[0]
        self.assertTrue(isinstance(obj, UIErrorHandler))
        self.assertEqual(obj.level, logging.ERROR)
        self.assertEqual(obj.ui, ui)

    def test_add_remove_project_works(self):
        # Given
        ui = VixenUI()
        vixen = ui.vixen
        self.assertEqual(len(vixen.projects), 1)

        # When
        ui.add_project()

        # Then
        self.assertEqual(len(vixen.projects), 1)
        p = vixen.projects[-1]
        self.assertEqual(p.name, 'Project1')
        self.assertEqual(
            vixen.save_file, os.path.join(self._temp, 'projects.json')
        )

        # When
        ui.remove(p)

        # Then
        self.assertEqual(len(vixen.projects), 0)

    def test_copy_project_works(self):
        # Setup

        # Create a new project, scan it, save it and re-load it for the test.
        ui = VixenUI()
        vixen = ui.vixen
        ui.add_project()

        p = vixen.projects[-1]
        p.add_tags([TagInfo(name='sometag', type='text')])
        p.path = self.root
        p.scan()
        p.save()
        vixen.save()
        self.assertEqual(len(vixen.projects), 1)

        # Given
        ui = VixenUI()
        vixen = ui.vixen
        self.assertEqual(len(vixen.projects), 1)

        # When
        ui.copy_project(vixen.projects[0])

        # Then
        self.assertEqual(len(vixen.projects), 2)
        p = vixen.projects[-1]
        self.assertEqual(p.name, 'Project1 copy')
        self.assertEqual(len(p.tags), 2)
        self.assertEqual(p.tags[0].name, 'completed')
        self.assertEqual(p.tags[0].type, 'bool')
        self.assertEqual(p.tags[1].name, 'sometag')
        self.assertEqual(p.tags[1].type, 'text')

    def test_search_string_updates_search_completed(self):
        # Given
        ui = VixenUI()
        vixen = ui.vixen
        ui.add_project()
        p = vixen.projects[0]
        p.path = self.root
        p.scan()

        # When
        ui.view(p)
        self.assertEqual(ui.viewer.active_pager, ui.viewer.pager)
        ui.viewer.search = 'root.txt'

        # Then
        self.assertEqual(ui.viewer.search_completed, False)
        self.assertEqual(ui.viewer.active_pager, ui.viewer.search_pager)

        # When
        ui.viewer.do_search()

        # Then
        self.assertEqual(ui.viewer.search_completed, True)

        # When
        ui.viewer.search = 'xxx'

        # Then
        self.assertEqual(ui.viewer.search_completed, False)

    def test_process_uses_search_results(self):
        # Given
        ui = VixenUI()
        vixen = ui.vixen
        ui.add_project()
        p = vixen.projects[0]
        p.path = self.root
        p.scan()

        from textwrap import dedent
        code = dedent("""
        def process(relpath, media, dest):
            media.tags['completed'] = True
        """)
        p.processors = [PythonFunctionFactory(code=code, dest=self.root)]

        # When
        ui.view(p)
        ui.viewer.search = 'root.txt'
        ui.viewer.do_search()
        ui.process(p)

        # Then
        self.assertEqual(p.get('root.txt').tags['completed'], True)
        self.assertEqual(p.get('hello.py').tags['completed'], False)

        # When
        ui.viewer.clear_search()
        ui.process(p)

        # Then
        for m in p.keys():
            self.assertEqual(p.get(m).tags['completed'], True)

    def test_viewer_rescan(self):
        # Given
        ui = VixenUI()
        vixen = ui.vixen
        ui.add_project()
        p = vixen.projects[0]
        p.path = self.root
        p.scan()
        viewer = ui.viewer
        ui.view(p)

        # When
        viewer.rescan()

        # Then
        self.assertEqual(viewer.current_dir, p.root)

class TestProjectViewer(TestVixenBase):

    def setUp(self):
        super(TestProjectViewer, self).setUp()
        ui = VixenUI()
        p = Project(
            name='test', path=self.root,
            description='desc', extensions=['.py', '.txt']
        )
        p.scan()
        ui.vixen.projects.append(p)
        self.ui = ui
        self.p = p

    def test_rescan_handles_removed_files(self):
        # Given
        ui, p = self.ui, self.p
        viewer = ui.viewer
        ui.view(p)
        self.assertEqual(p.number_of_files, 5)
        self.assertEqual(len(viewer.pager.data), 4)
        os.remove(os.path.join(self.root, 'root.txt'))

        # When
        viewer.rescan()

        # Then
        self.assertEqual(p.number_of_files, 4)
        self.assertEqual(len(viewer.pager.data), 3)
        names = [x.name for x in viewer.pager.data]
        self.assertTrue('root.txt' not in names)


class TestVixenUtils(unittest.TestCase):
    def test_get_html_file(self):
        r = os.path.abspath(get_html_file())
        self.assertTrue(os.path.exists(r))
        self.assertTrue(os.path.isfile(r))

    def test_get_html(self):
        # Given/When
        data = get_html(get_html_file())

        # Then.
        self.assertEqual(data.count('$HTML_ROOT'), 0)
        self.assertEqual(data.count('$ROOT'), 0)
