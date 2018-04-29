import logging
import multiprocessing
import os
import shlex
import shutil
import subprocess
import time
from threading import Thread
from traceback import format_exc

from traits.api import (Any, Bool, Callable, Dict, Enum, HasTraits, Instance,
                        Int, List, Str)


logger = logging.getLogger(__name__)


class Job(HasTraits):
    func = Callable

    args = List

    kw = Dict

    result = Any

    error = Str

    # Information about the job, some useful string.
    info = Str

    status = Enum('none', 'running', 'error', 'success')

    thread = Instance(Thread)

    def run(self):
        self.thread.start()

    def reset(self):
        self.status = 'none'
        self.error = ''
        self.thread = self._thread_default()

    def _run(self):
        self.status = 'running'
        logger.info("Running: %s", self.info)
        try:
            self.result = self.func(*self.args, **self.kw)
            self.status = 'success'
        except Exception as e:
            if hasattr(e, 'output'):
                self.error = 'OUTPUT: %s\n' % e.output
            self.error += format_exc()
            self.status = 'error'
            logger.info(self.error)

    def _thread_default(self):
        t = Thread(target=self._run)
        t.daemon = True
        return t


class Processor(HasTraits):
    jobs = List(Job)

    errored_jobs = List(Job)

    completed = List(Job)

    running = List(Job)

    number_of_processes = Int(1)

    max_processes = Int

    status = Enum('none', 'running', 'success', 'error')

    interrupt = Enum('', 'pause', 'stop')

    def process(self):
        self.running = []
        self.interrupt = ''
        running = self.running
        error = None
        self.status = 'running'
        jobs = [job for job in self.jobs if job.status == 'none']
        self._reset_errored_jobs()
        jobs.extend(self.errored_jobs)
        self.errored_jobs = []
        for job in jobs:
            while len(running) == self.number_of_processes:
                for j in running:
                    if not j.thread.is_alive():
                        if j.status == 'error':
                            error = j
                        else:
                            self.completed.append(j)
                        running.remove(j)
                time.sleep(0.01)

            while self.interrupt == 'pause':
                time.sleep(0.5)

            if error is not None:
                self.status = 'error'
                self.errored_jobs.append(error)
                break

            if self.interrupt == 'stop':
                break
            else:
                running.append(job)
                job.run()

        # Wait for all remaining jobs to complete.
        for job in running:
            job.thread.join()
            running.remove(job)
            if job.status == 'error':
                self.errored_jobs.append(job)
                self.status = 'error'
            elif job.status == 'success':
                self.completed.append(job)

        if self.status != 'error':
            self.status = 'success'

    def stop(self):
        if self.status == 'running':
            self.interrupt = 'stop'

    def pause(self):
        if self.status == 'running':
            self.interrupt = 'pause'

    def resume(self):
        if self.status == 'running' and self.interrupt == 'pause':
            self.interrupt = ''

    def _reset_errored_jobs(self):
        for job in self.errored_jobs:
            job.reset()

    def _max_processes_default(self):
        return multiprocessing.cpu_count()/2

    def _jobs_changed(self):
        self.completed = []


class FactoryBase(HasTraits):

    # The destination path.  This is typically the root of the directory where
    # any optional output files will be written.
    dest = Str

    # A simple database to store the processed files so they need not be
    # processed again.
    _done = Dict

    # The name of this factory.
    name = Str

    def clear(self):
        """Clear out any old file information.
        """
        self._done.clear()


class CommandFactory(FactoryBase):

    mirror_tree = Bool(True)

    copy_timestamps = Bool(True, desc='copy timestamps of source to target')

    input_extension = Str

    output_extension = Str

    command = Str

    name = 'CommandFactory'

    def make_jobs(self, media_keys, project):
        jobs = []
        ext = self.output_extension
        if len(ext) > 0:
            ext = ext if '.' in ext else '.' + ext

        for key in media_keys:
            media = project.get(key)
            relpath = media.relpath
            if os.path.splitext(relpath.lower())[1] != self.input_extension:
                continue
            if not os.path.exists(media.path):
                continue
            out_file = self._get_output(relpath, media, ext)
            if not self._done.get(out_file, False):
                cmd = self._get_command(media, out_file)
                job = Job(
                    func=self._run, args=[cmd, media.path, out_file],
                    info=' '.join(cmd)
                )
                jobs.append(job)

        return jobs

    def _get_command(self, media, out_file):
        cmd = [c.replace('$input', media.path).replace('$output', out_file).
               replace('\\', '\\\\')
               for c in shlex.split(self.command)]
        return cmd

    def _get_output(self, relpath, media, ext):
        if self.mirror_tree:
            output_base = os.path.join(self.dest, relpath)
        else:
            output_base = os.path.join(self.dest, os.path.basename(relpath))
        if len(ext) > 0:
            output = os.path.splitext(output_base)[0] + ext
        else:
            output = output_base
        return output

    def _run(self, command, in_file, out_file):
        basedir = os.path.dirname(out_file)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        lock = out_file + '.lck'
        if os.path.exists(lock):
            if os.path.exists(out_file):
                os.remove(out_file)

        open(lock, 'w').close()

        if not os.path.exists(out_file):
            subprocess.check_output(command, stderr=subprocess.STDOUT)

        if self.copy_timestamps:
            shutil.copystat(in_file, out_file)

        os.remove(lock)
        self._done[out_file] = True


class PythonFunctionFactory(FactoryBase):

    # The code should contain a single function called "process" which is
    # called with the arguments: relpath, media, dest.  relpath is the key of
    # the media instance in the project dictionary, dest is the destination
    # directory, this can be empty if not specified.
    code = Str

    _func = Callable(transient=True)

    name = 'PythonFunctionFactory'

    def make_jobs(self, media_keys, project):
        self._setup_func()
        jobs = []
        for key in media_keys:
            media = project.get(key)
            relpath = media.relpath
            if not self._done.get(media.path, False):
                info = "Processing %s" % media.path
                job = Job(
                    func=self._run, args=[relpath, media, self.dest],
                    info=info
                )
                jobs.append(job)
        return jobs

    def _setup_func(self):
        ns = {}
        code_obj = compile(self.code, '<string>', 'exec')
        exec(code_obj, ns)
        self._func = ns['process']

    def _run(self, relpath, media, dest):
        self._func(relpath, media, dest)
        self._done[media.path] = True

    def _code_default(self):
        return "def process(relpath, media, dest): pass"


class TaggerFactory(FactoryBase):
    command = Str

    _tag_types = Any(transient=True)

    name = 'TaggerFactory'

    def make_jobs(self, media_keys, project):
        self._setup_tag_types(project)
        jobs = []

        for key in media_keys:
            media = project.get(key)
            path = media.path
            if not os.path.exists(media.path):
                continue
            if not self._done.get(path, False):
                cmd = shlex.split(self.command) + [path]
                job = Job(
                    func=self._run, args=[cmd, media], info=' '.join(cmd)
                )
                jobs.append(job)

        return jobs

    def _run(self, command, media):
        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate()
        if p.returncode == 0:
            tag_types = self._tag_types
            updates = {}
            for line in stdout.splitlines():
                line = line.decode('utf-8')
                if len(line) == 0:
                    continue
                try:
                    tag, value = [x.strip() for x in line.split(':', 1)]
                except ValueError:
                    pass
                else:
                    if tag in tag_types:
                        updates[tag] = tag_types[tag](value)

            media.tags.update(updates)
            self._done[media.path] = True

    def _setup_tag_types(self, project):

        TRUE = ('1', 't', 'true', 'y', 'yes')
        type_map = {
            'bool': lambda x: x.lower() in TRUE,
            'string': lambda x: x,
            'int': int,
            'float': float
        }

        self._tag_types = {x.name: type_map[x.type] for x in project.tags}


def dump(factory):
    """Dump a factory instance so it can be safely pickled."""
    name = factory.__class__.__name__
    data = factory.__getstate__()
    return name, data


def load(state):
    """Create and setup the state from pickled data.
    Returns a factory instance.
    """
    name, data = state
    obj = globals()[name]()
    obj.__setstate__(data)
    return obj
