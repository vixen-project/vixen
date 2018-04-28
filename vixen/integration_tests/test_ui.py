import os
import shutil
import tempfile
from threading import Thread
import time
import unittest

from tornado.ioloop import IOLoop
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from vixen.cli import make_ui
from vixen.vixen_ui import main
from vixen.tests.test_directory import make_data


def stop_io_loop():
    IOLoop.instance().stop()


class TestUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        os.environ['VIXEN_ROOT'] = os.path.join(cls.root, 'vixen')
        make_data(cls.root)
        ui = make_ui()
        port = 9876
        ioloop = main(dev=True, port=port, test=True, **ui.get_context())
        t = Thread(target=ioloop.start)
        t.setDaemon(True)
        t.start()

        driver = os.environ.get('DRIVER', 'firefox')

        if driver == 'firefox':
            browser = webdriver.Firefox()
        elif driver == 'chrome':
            browser = webdriver.Chrome()

        browser.implicitly_wait(20)
        browser.get('http://localhost:%d' % port)
        time.sleep(2)
        cls.driver = driver
        cls.browser = browser
        cls.ui = ui
        cls.thread = t

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        IOLoop.instance().add_callback(stop_io_loop)
        thread = cls.thread
        count = 0
        while thread.is_alive() and count < 50:
            time.sleep(0.1)
        cls.thread.join()
        del os.environ['VIXEN_ROOT']
        shutil.rmtree(cls.root)

    def _get(self, name, kind=By.ID):
        return self.wait.until(EC.presence_of_element_located((kind, name)))

    def test_edit_view_project(self):
        # Given
        cls = self.__class__
        root = cls.root
        browser = cls.browser
        ui = cls.ui
        data_path = os.path.join(root, 'test')
        self.wait = WebDriverWait(browser, 20)

        # When
        # Create a new project.
        self._get('new-project').click()

        # Set the name.
        e = self._get('edit-name')
        e.clear()
        e.send_keys('test1')
        # Set the path.
        self._get('edit-path').send_keys(data_path)

        # Setup the tags.
        self._get('remove-tag-0').click()
        e = self._get('new-tag')
        e.send_keys('comments, count, processed')
        self._get('add-tag').click()

        e = self._get('tag-type-1')
        e = Select(e)
        e.select_by_visible_text('int')
        e = Select(browser.find_element_by_id('tag-type-2'))
        e.select_by_visible_text('bool')

        self._get('new-extension').send_keys('.txt')
        self._get('add-extension').click()

        self._wait_while(lambda: len(ui.editor.extensions) == 0)

        # Save changes.
        self._get('apply').click()

        p = ui.vixen.projects[0]
        self._wait_while(lambda: len(p.last_save_time) == 0)

        # Then
        self.assertEqual(len(ui.vixen.projects), 1)
        self.assertEqual(p.name, 'test1')
        self.assertEqual(p.root.path, data_path)
        self.assertEqual(p.tags[0].name, 'comments')
        self.assertEqual(p.tags[1].name, 'count')
        self.assertEqual(p.tags[2].name, 'processed')
        self.assertEqual(p.tags[1].type, 'int')
        self.assertEqual(p.tags[2].type, 'bool')
        self.assertEqual(p.number_of_files, 4)
        m = p.get('root.txt')
        self.assertEqual(m.relpath, 'root.txt')
        self.assertEqual(m.type, 'text')
        self.assertEqual(len(m.tags), 3)

        # Test control-s
        last_save = p.last_save_time
        e = self._get('edit-name')
        e.clear()
        e.send_keys('Project 1')
        e = browser.find_element_by_id('apply')
        e.send_keys(Keys.CONTROL, "s")
        self._wait_while(lambda: p.last_save_time == last_save)

        # Then
        self.assertEqual(p.name, 'Project 1')

        # When
        # Now view the project.
        self._get('view-0').click()

        # Navigate down a directory.
        e = self._get('path-0').click()
        viewer = ui.viewer
        self._wait_while(lambda: viewer.current_dir.name == 'test')
        self.assertTrue('sub' in viewer.current_dir.name)
        self.assertEqual(ui.mode, 'view')

        e = self._get('go-to-parent')
        e.send_keys('')
        time.sleep(0.2)
        e.click()
        browser.find_element_by_id('go-to-parent').click()

        self._wait_while(lambda: viewer.current_dir.name == 'sub')
        self.assertEqual(viewer.current_dir.name, 'test')
        e = self._get('path-2')
        e.click()
        self._wait_while(lambda: viewer.current_file is None)
        self.assertEqual(viewer.current_file.name, 'root.txt')

        # Change some tag information and save.
        last_save = p.last_save_time
        e = self._get('tag-0')
        e.send_keys('')
        e.send_keys('test')
        self._get('tag-1').clear()
        self._get('tag-1').clear()
        self._get('tag-1').send_keys('1')
        self._get('save').send_keys('')
        self._get('save').click()
        if cls.driver == 'firefox':
            self._get('save').click()

        self._wait_while(lambda: p.last_save_time == last_save)

        # Then
        m = p.get('root.txt')
        self._wait_while(lambda: m.tags['count'] == 0)
        self.assertEqual(m.tags['comments'], 'test')
        self.assertEqual(m.tags['count'], 1)

        # Change some tag information and save using ctrl+s
        last_save = p.last_save_time
        self._get('tag-0').send_keys('2')

        self._get('tag-1').clear()
        self._get('tag-1').send_keys('12')
        self._get('tag-1').clear()
        self._get('tag-1').send_keys('12')

        self._get('go-to-parent').send_keys(Keys.CONTROL, "s")

        self._wait_while(lambda: p.last_save_time == last_save)

        self.assertEqual(m.tags['comments'], 'test2')
        self.assertEqual(m.tags['count'], 12)

        # Now check if search works.
        self._get('search-text').send_keys('count:12')
        self._get('search').click()

        self._wait_while(lambda: not ui.viewer.search_completed)

        # Then
        e = self._get('search-item-0')
        e.click()
        self._wait_while(lambda: viewer.media is None)
        self.assertTrue(viewer.media.file_name, 'root.txt')
        self.assertEqual(ui.viewer.is_searching, True)
        self.assertEqual(ui.viewer.search_completed, True)

        self._get('clear-search').click()
        self._wait_while(lambda: ui.viewer.search_completed)

        e = self._get('path-2')
        self.assertEqual(ui.viewer.is_searching, False)

        # When
        # Now edit the project.
        browser.find_element_by_link_text('Home').click()
        e = self._get('edit-0')
        e.click()
        self._wait_while(lambda: ui.editor.project is None)

        # Then
        self.assertEqual(ui.mode, 'edit')
        self.assertEqual(ui.editor.project, ui.vixen.projects[-1])

        # When
        # Finally remove the projects.
        done = False
        count = 0
        while not done and count < 3:
            try:
                e = self._get('remove-0')
                e.send_keys('')
                e.click()

                confirm = browser.switch_to_alert()
                confirm.accept()
                done = True
            except NoAlertPresentException:
                count += 1
                time.sleep(0.1)

        self._wait_while(lambda: len(ui.vixen.projects) > 0)
        self.assertEqual(len(ui.vixen.projects), 0)

    def _wait_while(self, cond, count=20, sleep=0.1):
        i = 0
        time.sleep(sleep)
        while cond() and i < count:
            time.sleep(sleep)
            i += 1


if __name__ == '__main__':
    unittest.main()
