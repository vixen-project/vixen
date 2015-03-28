import multiprocessing
from threading import Thread
from traceback import format_exc
import time
from Queue import Queue
from subprocess import Popen, PIPE

from traits.api import (HasTraits, Str, Int, List, Instance, Bool, Property)


class CommandExecutor(HasTraits):
    number_of_processes = Int

    number_of_jobs = Property(Int)

    # Is the executor running.
    running = Property(Bool)

    # List of any errors.
    errors = List(Str)

    # Active jobs.
    jobs = Instance(Queue, ())

    processes = List([])

    _thread = Instance(Thread)

    def submit(self, command):
        self.jobs.put(command)

    def run(self):
        self._thread.start()

    def _done(self, proc):
        return proc.poll() is not None

    def _on_error(self, cmd, msg):
        message = 'On running: %s\n'\
                  'the following error was obtained:\n%s\n'%(cmd, msg)
        self.errors.append(message)

    def _run(self):
        max_proc = self.number_of_processes
        processes = self.processes
        jobs = self.jobs
        while True:
            while not jobs.empty() and len(processes) < max_proc:
                cmd = jobs.get()
                try:
                    processes.append((cmd, Popen(cmd, stdout=PIPE, stderr=PIPE)))
                except Exception:
                    self._on_error(cmd, format_exc())

            for cmd, proc in processes:
                if self._done(proc):
                    if proc.returncode == 0:
                        processes.remove(proc)
                    else:
                        msg = proc.stdout.read() + '\n' + proc.stderr.read()
                        self._on_error(cmd, msg)

            if len(processes) == 0 and jobs.empty():
                time.sleep(0.5)

    def _number_of_processes_default(self):
        return max(1, multiprocessing.cpu_count()/2)

    def __thread_default(self):
        return Thread(target=self._run)

    def _get_running(self):
        return self._thread.is_alive()

    def _get_number_of_jobs(self):
        return len(self.jobs)
