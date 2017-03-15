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


class TestUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        os.environ['VIXEN_ROOT'] = os.path.join(cls.root, 'vixen')
        make_data(cls.root)
        ui = make_ui()
        port = 9876
        main(dev=True, port=port, test=True, **ui.get_context())
        ioloop = IOLoop.instance()
        t = Thread(target=ioloop.start)
        t.setDaemon(True)
        t.start()

        driver = os.environ.get('DRIVER', 'firefox')

        if driver == 'firefox':
            browser = webdriver.Firefox()
        elif driver == 'chrome':
            browser = webdriver.Chrome()

        browser.get('http://localhost:%d' % port)
        cls.browser = browser
        cls.ui = ui
        cls.thread = t

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        IOLoop.instance().stop()
        time.sleep(1)
        cls.thread.join()
        del os.environ['VIXEN_ROOT']
        shutil.rmtree(cls.root)

    def test_edit_view_project(self):
        # Given
        cls = self.__class__
        root = cls.root
        browser = cls.browser
        ui = cls.ui
        data_path = os.path.join(root, 'test')
        wait = WebDriverWait(browser, 5)

        # When
        # Create a new project.
        browser.find_element_by_id('new-project').click()
        # Set the name.
        e = wait.until(EC.presence_of_element_located((By.ID, 'edit-name')))
        e.clear()
        e.send_keys('test1')
        # Set the path.
        e = browser.find_element_by_id('edit-path')
        e.send_keys(data_path)

        # Setup the tags.
        browser.find_element_by_id('remove-tag-0').click()
        e = wait.until(EC.presence_of_element_located((By.ID, 'new-tag')))
        e.send_keys('comments, count, processed')
        browser.find_element_by_id('add-tag').click()

        e = wait.until(EC.presence_of_element_located((By.ID, 'tag-type-1')))
        e = Select(e)
        e.select_by_visible_text('int')
        e = Select(browser.find_element_by_id('tag-type-2'))
        e.select_by_visible_text('bool')

        # Save changes.
        e = wait.until(EC.presence_of_element_located((By.ID, 'apply')))
        e.click()
        time.sleep(0.5)

        # Then
        self.assertEqual(len(ui.vixen.projects), 1)
        p = ui.vixen.projects[0]
        self._wait_while(lambda: p.tags[1].type != 'int')

        self.assertEqual(p.name, 'test1')
        self.assertEqual(p.root.path, data_path)
        self.assertEqual(p.tags[0].name, 'comments')
        self.assertEqual(p.tags[1].name, 'count')
        self.assertEqual(p.tags[2].name, 'processed')
        self.assertEqual(p.tags[1].type, 'int')
        self.assertEqual(p.tags[2].type, 'bool')
        self.assertEqual(p.number_of_files, 5)
        m = p.get('root.txt')
        self.assertEqual(m.relpath, 'root.txt')
        self.assertEqual(m.type, 'text')
        self.assertEqual(len(m.tags), 3)

        # Test control-s
        e = browser.find_element_by_id('edit-name')
        e.clear()
        e.send_keys('Project 1')
        e = browser.find_element_by_id('apply')
        e.send_keys(Keys.CONTROL, "s")
        self._wait_while(lambda: ui.is_busy)

        # Then
        self.assertEqual(p.name, 'Project 1')

        # When
        # Now view the project.
        browser.find_element_by_id('view-0').click()

        # Navigate down a directory.
        e = wait.until(EC.presence_of_element_located((By.ID, 'path-0')))
        e.click()
        viewer = ui.viewer
        self._wait_while(lambda: viewer.current_dir.name == 'test')
        self.assertEqual(viewer.current_dir.name, 'sub')
        self.assertEqual(ui.mode, 'view')

        e = browser.find_element_by_id('go-to-parent')
        e.send_keys('')
        time.sleep(0.25)
        e.click()
        browser.find_element_by_id('go-to-parent').click()

        self._wait_while(lambda: viewer.current_dir.name == 'sub')
        self.assertEqual(viewer.current_dir.name, 'test')
        e = wait.until(EC.presence_of_element_located((By.ID, 'path-2')))
        e.click()
        self._wait_while(lambda: viewer.current_file is None)
        self.assertEqual(viewer.current_file.name, 'hello.py')

        # Change some tag information and save.
        e = wait.until(EC.presence_of_element_located((By.ID, 'tag-0')))
        e.send_keys('test')
        browser.find_element_by_id('tag-1').clear()
        browser.find_element_by_id('tag-1').send_keys('1')
        browser.find_element_by_id('save').send_keys('')
        browser.find_element_by_id('save').click()

        self._wait_while(lambda: ui.is_busy)

        # Then
        m = p.get('hello.py')
        self._wait_while(lambda: m.tags['count'] == 0, 20)
        self.assertEqual(m.tags['comments'], 'test')
        self.assertEqual(m.tags['count'], 1)

        # Change some tag information and save using ctrl+s
        browser.find_element_by_id('tag-0').send_keys('2')

        browser.find_element_by_id('tag-1').send_keys('')
        browser.find_element_by_id('tag-1').send_keys('2')
        browser.find_element_by_id('go-to-parent').send_keys(Keys.CONTROL, "s")

        self._wait_while(lambda: ui.is_busy)
        self.assertEqual(m.tags['comments'], 'test2')
        self.assertEqual(m.tags['count'], 12)

        # Now check if search works.
        browser.find_element_by_id('search-text').send_keys('count:12')
        browser.find_element_by_id('search').click()

        self._wait_while(lambda: ui.is_busy)

        # Then
        e = wait.until(EC.presence_of_element_located((By.ID, 'search-item-0')))
        e.click()
        self._wait_while(lambda: viewer.media is None)
        self.assertEqual(viewer.media.file_name, 'hello.py')
        self.assertEqual(ui.viewer.is_searching, True)
        self.assertEqual(ui.viewer.search_completed, True)

        browser.find_element_by_id('clear-search').click()

        e = wait.until(EC.presence_of_element_located((By.ID, 'path-3')))
        self.assertEqual(ui.viewer.is_searching, False)

        # When
        # Now edit the project.
        browser.find_element_by_link_text('Home').click()
        e = wait.until(EC.presence_of_element_located((By.ID, 'edit-0')))
        e.click()

        # Then
        self.assertEqual(ui.mode, 'edit')
        self._wait_while(lambda: ui.editor.project is None)
        self.assertEqual(ui.editor.project, ui.vixen.projects[-1])

        # When
        # Finally remove the projects.
        done = False
        count = 0
        while not done and count < 3:
            try:
                e = wait.until(EC.presence_of_element_located((By.ID, 'remove-0')))
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

    def _wait_while(self, cond, count=10, sleep=0.05):
        i = 0
        time.sleep(sleep)
        while cond() and i < count:
            time.sleep(sleep)
            i += 1

if __name__ == '__main__':
    unittest.main()
