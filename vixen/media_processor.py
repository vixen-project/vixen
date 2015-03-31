import multiprocessing
import os
import sys
import time
from threading import Thread
from traceback import format_exc

from traits.api import (HasTraits, Int, List, Instance, Property, Callable,
    Any, Enum, Str, Dict)

def get_all_files(root):
    """Given a directory find all the files nested inside.
    """
    result = []
    for root, dirs, files in os.walk(root):
        for name in files:
            result.append(os.path.join(root, name))
    return result


class Job(HasTraits):
    func = Callable

    args = List

    kw = Dict

    result = Any

    error = Str

    status = Enum('none', 'running', 'error', 'success')

    thread = Instance(Thread)

    def run(self):
        self.thread.start()

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


class MediaProcessor(HasTraits):
    number_of_processes = Int

    def process(self, root, processor, quiet=False):
        file_names = get_all_files(root)
        n_files = len(file_names)

        jobs = [Job(func=processor, args=[f]) for f in file_names]

        running = []
        error = None
        for count, job in enumerate(jobs):
            while len(running) == self.number_of_processes:
                for j in running:
                    if not j.thread.is_alive():
                        if j.status == 'error':
                            error = j
                        running.remove(j)
                time.sleep(0.01)

            if error is None:
                if not quiet:
                    print "Processing", count, "of", n_files, ":", job.args[0]
                    sys.stdout.flush()
                running.append(job)
                job.run()
            else:
                print "Aborting!"
                print "Error processing job,", error.args
                print error.error
                break

        # Wait for all remaining jobs to complete.
        for job in running:
            job.thread.join()

        return [(j.args[0], j.result) for j in jobs]

    def _number_of_processes_default(self):
        return max(1, multiprocessing.cpu_count()/2)
