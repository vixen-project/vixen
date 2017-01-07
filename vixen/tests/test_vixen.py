import os
import mock

from vixen.processor import PythonFunctionFactory
from vixen.vixen import VixenUI
from vixen.tests.test_project import TestProjectBase


class TestVixenUI(TestProjectBase):

    def setUp(self):
        super(TestVixenUI, self).setUp()
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

    def test_add_remove_project_works(self):
        # Given
        ui = VixenUI()
        vixen = ui.vixen
        self.assertEqual(len(vixen.projects), 0)

        # When
        ui.add_project()

        # Then
        self.assertEqual(len(vixen.projects), 1)
        p = vixen.projects[0]
        self.assertEqual(p.name, 'Project1')
        self.assertEqual(
            vixen.save_file, os.path.join(self._temp, 'projects.json')
        )

        # When
        ui.remove(p)

        # Then
        self.assertEqual(len(vixen.projects), 0)

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
        self.assertEqual(p.media['root.txt'].tags['completed'], True)
        self.assertEqual(p.media['hello.py'].tags['completed'], False)

        # When
        ui.viewer.clear_search()
        ui.process(p)

        # Then
        for m in p.media.values():
            self.assertEqual(m.tags['completed'], True)
