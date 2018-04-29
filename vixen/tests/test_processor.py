import mock
import os
import shutil
import tempfile
from threading import Thread
import time
import unittest

from vixen.processor import Processor, Job, CommandFactory, \
    PythonFunctionFactory, TaggerFactory, dump, load
from vixen.tests.test_directory import make_data
from vixen.project import Project, TagInfo


class TestJob(unittest.TestCase):
    def test_simple_job(self):
        # Given
        func = mock.Mock(return_value='hello')
        args = [1, 2]
        kw = {'a': 10, 'b': 20}
        j = Job(func=func, args=args, kw=kw)
        self.assertEqual(j.status, 'none')
        self.assertEqual(j.result, None)

        # When
        j.run()
        j.thread.join()

        # Then
        self.assertEqual(j.status, 'success')
        func.assert_called_once_with(*args, **kw)
        self.assertEqual(j.result, 'hello')
        self.assertEqual(j.error, '')

    def test_job_captures_errors(self):
        def bomb():
            assert 1 == 2

        # Given
        j = Job(func=bomb)

        # When
        j.run()
        j.thread.join()

        # Then
        self.assertEqual(j.status, 'error')
        self.assertIn('AssertionError', j.error)
        self.assertIn('assert 1 == 2', j.error)
        self.assertTrue(len(j.error) > 1, "Got: %s" % j.error)


class TestProcessor(unittest.TestCase):
    def test_processor_completes_jobs(self):
        # Given
        jobs = [Job(func=mock.Mock(return_value=x), args=[x])
                for x in range(10)]
        p = Processor(jobs=jobs)
        self.assertEqual(p.status, 'none')

        # When
        p.process()

        # Then
        self.assertEqual(p.status, 'success')
        self.assertEqual(len(p.completed), 10)
        for i, j in enumerate(jobs):
            self.assertEqual(j.status, 'success')
            j.func.assert_called_once_with(i)
            self.assertEqual(j.result, i)

    def test_processor_pauses_correctly(self):
        # Given
        def _sleep(x):
            time.sleep(0.01)
            return x

        jobs = [Job(func=mock.Mock(side_effect=_sleep), args=[x])
                for x in range(10)]
        p = Processor(jobs=jobs)
        self.addCleanup(p.stop)
        self.assertEqual(p.status, 'none')

        # When
        t = Thread(target=p.process)
        t.start()

        # Sleep for a tiny bit and pause
        time.sleep(0.05)
        p.pause()
        time.sleep(0.01)

        # Then
        self.assertEqual(p.status, 'running')
        self.assertTrue(len(p.completed) < 10)

        # When
        p.resume()
        count = 0
        while p.status == 'running' and count < 10:
            time.sleep(0.5)
            count += 1

        self.assertEqual(len(p.completed), 10)
        self.assertEqual(len(p.running), 0)
        for i, j in enumerate(jobs):
            self.assertEqual(j.status, 'success')
            j.func.assert_called_once_with(i)
            self.assertEqual(j.result, i)

    def test_processor_stops_correctly(self):
        # Given
        def _sleep(x):
            time.sleep(0.01)
            return x

        jobs = [Job(func=mock.Mock(side_effect=_sleep), args=[x])
                for x in range(5)]
        p = Processor(jobs=jobs)
        self.addCleanup(p.stop)
        self.assertEqual(p.status, 'none')

        # When
        t = Thread(target=p.process)
        t.start()

        # Sleep for a tiny bit and pause
        time.sleep(0.05)
        p.stop()
        count = 0
        while p.status == 'running' and count < 10:
            time.sleep(0.05)
            count += 1

        # Then
        self.assertEqual(p.status, 'success')
        self.assertTrue(len(p.completed) < 5)
        self.assertEqual(len(p.running), 0)
        for i, j in enumerate(p.completed):
            self.assertEqual(j.status, 'success')
            j.func.assert_called_once_with(i)
            self.assertEqual(j.result, i)

    def test_processor_bails_on_error(self):
        # Given
        f = mock.Mock()

        def bomb():
            f()
            assert 1 == 2

        jobs = [Job(func=bomb)]
        jobs.extend(
            Job(func=mock.Mock(return_value=x), args=[x]) for x in range(10)
        )
        p = Processor(jobs=jobs)

        # When
        p.process()

        # Then
        self.assertEqual(p.status, 'error')
        self.assertTrue(len(p.completed) < 10)
        self.assertEqual(len(p.errored_jobs), 1)
        self.assertEqual(f.call_count, 1)
        self.assertEqual(p.errored_jobs[0].status, 'error')

        # When process is called again it should run the remaining unfinished
        # jobs.
        p.process()

        # Then
        self.assertEqual(p.status, 'error')
        self.assertEqual(len(p.completed), 10)
        for i, j in enumerate(p.completed):
            self.assertEqual(j.status, 'success')
            j.func.assert_called_once_with(i)
            self.assertEqual(j.result, i)
        self.assertEqual(len(p.errored_jobs), 1)
        self.assertEqual(p.errored_jobs[0].status, 'error')
        self.assertEqual(f.call_count, 2)


class TestFactoryBase(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.mkdtemp()
        self.root = os.path.join(self._temp, 'test')
        self.root1 = os.path.join(self._temp, 'test1')
        make_data(self._temp)

    def tearDown(self):
        shutil.rmtree(self._temp)


class TestCommandFactory(TestFactoryBase):

    def test_command_factory_commands(self):
        # Given.
        cf = CommandFactory(dest=self.root1, input_extension='.py',
                            output_extension='.rst',
                            command="echo $input $output")
        p = Project(name='test', path=self.root)
        p.scan()

        # When
        jobs = cf.make_jobs(p.keys(), p)

        # Then.
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        m = p.get('hello.py')
        dest = os.path.join(self.root1, 'hello.rst')
        expect = ('echo %s %s' % (m.path, dest)).replace('\\', '\\\\')
        self.assertEqual(job.args, [expect.split(), m.path, dest])

    def test_command_factory_jobs(self):
        # Given.
        import sys
        command = """\
        %r -c 'import shutil;shutil.copy("$input", "$output")'\
        """ % sys.executable
        cf = CommandFactory(dest=self.root1, input_extension='.py',
                            output_extension='.rst',
                            command=command, copy_timestamps=True)
        p = Project(name='test', path=self.root)
        p.scan()

        # When
        jobs = cf.make_jobs(p.keys(), p)
        job = jobs[0]
        job.run()
        job.thread.join()

        # Then.
        self.assertEqual(len(jobs), 1)
        self.assertEqual(job.status, 'success')

        m = p.get('hello.py')
        dest = os.path.join(self.root1, 'hello.rst')
        self.assertTrue(os.path.exists(dest))
        self.assertEqual(cf._done[dest], True)
        s_stat = os.stat(m.path)
        d_stat = os.stat(dest)
        self.assertTrue(abs(s_stat.st_mtime - d_stat.st_mtime) < 2)
        self.assertTrue(abs(s_stat.st_ctime - d_stat.st_ctime) < 2)

        jobs = cf.make_jobs(p.keys(), p)
        self.assertEqual(len(jobs), 0)

        # When.
        data = dump(cf)
        cf1 = load(data)

        # Then.
        for attr in cf.__dict__.keys():
            self.assertEqual(getattr(cf1, attr), getattr(cf, attr))

    def test_command_factory_ignores_non_existing_paths(self):
        # Given.
        cf = CommandFactory(dest=self.root1, input_extension='.py',
                            output_extension='.rst',
                            command="echo $input $output")
        p = Project(name='test', path=self.root)
        p.scan()
        os.remove(os.path.join(self.root, 'hello.py'))

        # When
        jobs = cf.make_jobs(p.keys(), p)

        # Then.
        self.assertEqual(len(jobs), 0)


class TestPythonFunctionFactory(TestFactoryBase):

    def test_python_function_factory(self):
        # Given.
        from textwrap import dedent
        code = dedent("""
        def process(relpath, media, dest):
            media.tags['completed'] = True
            media.tags['args'] = "%s %s"%(relpath, dest)
        """)
        factory = PythonFunctionFactory(code=code, dest=self.root1)
        p = Project(name='test', path=self.root)
        p.add_tags([TagInfo(name='args', type='string')])
        p.scan()

        # When
        jobs = factory.make_jobs(p.keys(), p)
        for job in jobs:
            job.run()
            job.thread.join()

        # Then.
        self.assertEqual(len(jobs), 5)
        for key in p.keys():
            media = p.get(key)
            self.assertEqual(media.tags['completed'], True)
            expect = "%s %s" % (key, self.root1)
            self.assertEqual(media.tags['args'], expect)

        # When
        jobs = factory.make_jobs(p.keys(), p)

        # Then
        self.assertEqual(len(jobs), 0)

        # When.
        data = dump(factory)
        f1 = load(data)

        # Then.

        # The func should not be dumped.
        self.assertEqual(f1._func, None)
        self.assertNotIn('_func', data[1])
        f = factory
        for attr in ['code', '_done']:
            self.assertEqual(getattr(f1, attr), getattr(f, attr))


class TestTaggerFactory(TestFactoryBase):

    def test_tagger_factory_tags_known_tags(self):
        # Given.
        code = 'import sys; print("args:"+sys.argv[1]'\
               '+"\nlength:10\ncompleted:yes\n")'
        command = "python -c %r" % code

        factory = TaggerFactory(command=command)
        p = Project(name='test', path=self.root)
        p.add_tags(
            [
                TagInfo(name='args', type='string'),
                TagInfo(name='length', type='int')
            ]
        )
        p.scan()

        # When
        jobs = factory.make_jobs(p.keys(), p)
        for job in jobs:
            job.run()
            job.thread.join()

        # Then.
        self.assertEqual(len(jobs), 5)
        for job in jobs:
            self.assertEqual(job.status, 'success')
        for key in p.keys():
            media = p.get(key)
            self.assertEqual(media.tags['completed'], True)
            expect = "%s" % (media.path)
            self.assertEqual(media.tags['args'], expect)
            self.assertEqual(media.tags['length'], 10)

        # When
        jobs = factory.make_jobs(p.keys(), p)

        # Then
        self.assertEqual(len(jobs), 0)

        # When.
        data = dump(factory)
        f1 = load(data)

        # Then.

        # The _tag_types should not be dumped.
        self.assertEqual(f1._tag_types, None)
        self.assertNotIn('_tag_types', data[1])
        f = factory
        for attr in ['command', '_done']:
            self.assertEqual(getattr(f1, attr), getattr(f, attr))

    def test_tagger_factory_skips_unknown_tags(self):
        # Given.
        code = 'import sys; print("\nlength:10\nxxx:yes\n")'
        command = "python -c %r" % code

        factory = TaggerFactory(command=command)
        p = Project(name='test', path=self.root)
        p.scan()

        # When
        jobs = factory.make_jobs(p.keys(), p)
        for job in jobs:
            job.run()
            job.thread.join()

        # Then.
        self.assertEqual(len(jobs), 5)
        for key in p.keys():
            media = p.get(key)
            self.assertTrue('length' not in media.tags)
            self.assertTrue('xxx' not in media.tags)
            self.assertEqual(media.tags['completed'], False)


if __name__ == '__main__':
    unittest.main()
