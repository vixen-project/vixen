import os
import mock

from vixen.processor import PythonFunctionFactory
from vixen.project import Project
from vixen.vixen import VixenUI

from vixen.tests.test_project import TestProjectBase


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
        key = p.keys()[0]
        m = p.get(key)
        self.assertEqual(m.tags['completed'], True)

        # When
        editor.remove_processor(0)

        # Then
        self.assertEqual(len(editor.processors), 0)


class TestVixenUI(TestVixenBase):

    def test_add_remove_project_works(self):
        # Given
        ui = VixenUI()
        vixen = ui.vixen
        self.assertEqual(len(vixen.projects), 1)

        # When
        ui.add_project()

        # Then
        self.assertEqual(len(vixen.projects), 2)
        p = vixen.projects[-1]
        self.assertEqual(p.name, 'Project1')
        self.assertEqual(
            vixen.save_file, os.path.join(self._temp, 'projects.json')
        )

        # When
        ui.remove(p)

        # Then
        self.assertEqual(len(vixen.projects), 1)

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
        ui.viewer.search = 'root.txt'

        # Then
        self.assertEqual(ui.viewer.search_completed, False)

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
