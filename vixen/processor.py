import multiprocessing
import os
import shlex
import subprocess
import sys
import time
from threading import Thread
from traceback import format_exc

from traits.api import (Any, Bool, Callable, Dict, Enum, HasTraits, Instance,
                        Int, List, Property, Str)


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
        try:
            self.result = self.func(*self.args, **self.kw)
            self.status = 'success'
        except:
            self.error = format_exc()
            self.status = 'error'

    def _thread_default(self):
        t = Thread(target=self._run)
        t.daemon = True
        return t


class Processor(HasTraits):
    jobs = List(Job)

    errored_jobs = List(Job)

    completed = List(Job)

    number_of_processes = Int(1)

    max_processes = Int

    status = Enum('none', 'running', 'success', 'error')

    def process(self):
        running = []
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

            if error is None:
                running.append(job)
                job.run()
            else:
                self.status = 'error'
                self.errored_jobs.append(error)
                break

        # Wait for all remaining jobs to complete.
        for job in running:
            job.thread.join()
            if job.status == 'error':
                self.errored_jobs.append(job)
                self.status = 'error'
            elif job.status == 'success':
                self.completed.append(job)

        if self.status != 'error':
            self.status = 'success'

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

    def clear(self):
        """Clear out any old file information.
        """
        self._done.clear()


class CommandFactory(FactoryBase):

    mirror_tree = Bool(True)

    input_extension = Str

    output_extension = Str

    command = Str

    def make_jobs(self, media_dict):
        jobs = []
        ext = self.output_extension
        if len(ext) > 0:
            ext = ext if '.' in ext else '.' + ext
        command = self.command
        for relpath, media in media_dict.items():
            if os.path.splitext(relpath.lower())[1] != self.input_extension:
                continue
            out_file = self._get_output(relpath, media, ext)
            if not self._done.get(out_file, False):
                cmd = self._get_command(media, out_file)
                job = Job(
                    func=self._run, args=[cmd, out_file], info=' '.join(cmd)
                )
                jobs.append(job)

        return jobs

    def _get_command(self, media, out_file):
        cmd = [c.replace('$input', media.path).replace('$output', out_file)
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

    def _run(self, command, out_file):
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

        os.remove(lock)
        self._done[out_file] = True


class PythonFunctionFactory(FactoryBase):

    # The code should contain a single function called "process" which is
    # called with the arguments: relpath, media, dest.  relpath is the key of
    # the media instance in the project dictionary, dest is the destination
    # directory, this can be empty if not specified.
    code = Str

    _func = Callable

    def make_jobs(self, media_dict):
        self._setup_func()
        jobs = []
        for relpath, media in media_dict.items():
            if not self._done.get(media.path, False):
                info = "Processing %s"%media.path
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
