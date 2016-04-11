from contextlib import contextmanager
import copy
import json
from os.path import (abspath, dirname, exists, expanduser, join, isdir,
                     splitext)
import os
import subprocess
import sys

from traits.api import (Any, Bool, DelegatesTo, Dict, Enum, HasTraits, Instance,
                        Int, List, Property, Str)

from .project import Project, TagInfo, get_project_dir
from .directory import File, Directory
from .media import Media
from .processor import (FactoryBase, CommandFactory, Processor,
                        PythonFunctionFactory, Job)


class Vixen(HasTraits):

    projects = List(Project)

    save_file = Str

    def save(self):
        data = [dict(name=p.name, save_file=p.save_file)
                for p in self.projects]
        with open(self.save_file, 'w') as fp:
            json.dump(data, fp)

    def load(self):
        if exists(self.save_file):
            with open(self.save_file) as fp:
                data = json.load(fp)
            self.projects = [Project(name=x['name'], save_file=x['save_file'])
                             for x in data]

    def remove(self, project):
        if exists(project.save_file):
            os.remove(project.save_file)
        self.projects.remove(project)
        self.save()

    def _save_file_default(self):
        return join(get_project_dir(), 'projects.json')


class ValidPath(HasTraits):
    path = Str
    abspath = Property(Str, depends_on='path')
    valid = Bool
    is_file = Bool

    def _path_changed(self, path):
        if len(path) > 0:
            if self.is_file:
                self.valid = isdir(dirname(self.abspath))
            else:
                self.valid = isdir(self.abspath)
        else:
            self.valid = False

    def _is_file_changed(self, value):
        self._path_changed(self.path)

    def _get_abspath(self):
        return abspath(expanduser(self.path))


class ProjectEditor(HasTraits):

    project = Instance(Project, allow_none=True)

    name = Str
    description = Str
    path = Str
    tags = List(TagInfo)

    extensions = List(Str)

    processors = List(FactoryBase)

    available_exts = List(Str)

    valid_path = Bool
    tag_name = Str
    ext_name = Str
    processor_type = Str

    test_job = Dict(Int, Job)
    test_job_status = Dict(Int, Str)

    ui = Instance('VixenUI')

    def add_tag(self, name):
        self.tags.append(TagInfo(name=name, type="string"))

    def remove_tag(self, index):
        del self.tags[index]

    def add_extension(self, name):
        self.extensions.append(name.lower())

    def remove_extension(self, index):
        del self.extensions[index]

    def add_processor(self, name):
        procs = {'command': CommandFactory, 'python': PythonFunctionFactory}
        self.processors.append(procs[name](dest=self.path))

    def remove_processor(self, index):
        del self.processors[index]

    def find_extensions(self):
        with self.ui.busy():
            path = self._get_actual_path(self.path)
            exts = set(
                os.path.splitext(x.lower())[1]
                for r, d, files in os.walk(path) for x in files
            )
            self.available_exts = sorted(exts)

    def apply(self):
        with self.ui.busy():
            cp = self.project
            if cp is not None and self.valid_path:
                cp.name = self.name
                cp.description = self.description
                cp.path = self._get_actual_path(self.path)
                cp.extensions = self.extensions
                cp.processors = self.processors
                cp.update_tags(self.tags)
                cp.scan()
                cp.save()
                if self.ui is not None:
                    self.ui.save()

    def check_processor(self, proc):
        with self.ui.busy():
            proj = self.project
            jobs = []
            for key in proj.media:
                test_media = {key: proj.media[key]}
                jobs = proc.make_jobs(test_media)
                if len(jobs) > 0:
                    break
            index = self.processors.index(proc)
            self.clear_test_info(index)
            if len(jobs) == 0:
                self.test_job_status[index] = 'Error'
            else:
                job = jobs[0]
                self.test_job[index] = job
                job.run()
                job.thread.join()
                proc.clear()

    def clear_test_info(self, index):
        if index in self.test_job:
            del self.test_job[index]
        if index in self.test_job_status:
            del self.test_job_status[index]

    def _get_actual_path(self, path):
        return abspath(expanduser(path))

    def _project_changed(self, proj):
        with self.ui.busy():
            if proj is not None:
                if len(proj.media) == 0:
                    proj.load()
                self.name = proj.name
                self.description = proj.description
                self.path = self._get_actual_path(proj.path)
                self.tags = copy.deepcopy(proj.tags)
                self.extensions = list(proj.extensions)
                self.processors = proj.processors
                self.available_exts = []
                self.test_job = {}
                self.test_job_status = {}

    def _path_changed(self, path):
        self.valid_path = isdir(self._get_actual_path(path))


class Pager(HasTraits):

    """A simple paginator for a large list of elements.
    """

    selected = Any

    limit = Int(20)

    index = Property(Int, depends_on='_index')

    page = Property(Int, depends_on='_page')

    start = Property(Int, depends_on='_page')

    view = Property(List, depends_on=['page', 'data'])

    total = Property(Int, depends_on='data')

    total_pages = Property(Int, depends_on=['data', 'limit'])

    data = List
    _page = Int
    _index = Int

    def select(self, relindex):
        self.index = (self.page -1)*self.limit + relindex

    def next(self):
        self.index += 1

    def prev(self):
        self.index -= 1

    def next_page(self):
        self.page += 1

    def prev_page(self):
        self.page -= 1

    def _data_changed(self, data):
        self.selected = None
        # Set this to an invalid index, we can't set it to zero as
        # this will trigger a change to selected, if we set _index to 0 then
        # if a user clicks on the zero'th index nothing will change as _index
        # is already 0.
        self._index = -1
        self._page = 1

    def _get_page(self):
        return self._page

    def _set_page(self, page):
        p = min(max(1, page), self.total_pages)
        limit = self.limit
        if p != self._page:
            self._page = p

    def _get_start(self):
        return (self.page - 1)*self.limit

    def _get_view(self):
        p = self.page -1
        limit = self.limit
        return self.data[p*limit:(p+1)*limit]

    def _get_index(self):
        return self._index

    def _set_index(self, index):
        idx = min(max(0, index), self.total-1)
        if idx != self._index:
            self._index = idx
            data = self.data
            if len(data) > 0:
                self.selected = data[idx]
            else:
                self.selected = None
            desired_page = int(idx/self.limit) + 1
            if self.page != desired_page:
                self.page = desired_page

    def __index_default(self):
        return -1

    def _get_total(self):
        return len(self.data)

    def _get_total_pages(self):
        size = len(self.data)
        n = size/self.limit if size > 0 else 1
        rem = size%self.limit
        if rem > 0:
            return n + 1
        else:
            return n


class ProjectViewer(HasTraits):

    project = Instance(Project, allow_none=True)

    name = Str

    ui = Instance('VixenUI')

    parent = Instance(Directory)

    current_dir = Instance(Directory)

    current_file = Instance(File)

    pager = Instance(Pager)

    media = Instance(Media)

    csv_file = Instance(ValidPath)

    csv_file_valid = DelegatesTo('csv_file', prefix='valid')

    type = Enum("unknown", "image", "video", "audio")

    def go_to_parent(self):
        if self.parent is not None:
            self.current_dir = self.parent

    def view(self, path):
        if isinstance(path, Directory):
            self.current_dir = path
        else:
            self.current_file = path

    def rescan(self):
        with self.ui.busy():
            proj = self.project
            if proj is not None:
                proj.refresh()
                self.current_dir = proj.root
                self._current_dir_changed(proj.root)

    def os_open(self, path):
        """Ask the OS to open the path with a suitable application.
        """
        if sys.platform == 'windows':
            os.startfile(path)
        elif sys.platform.startswith('linux'):
            subprocess.call(['xdg-open', path])
        elif sys.platform == 'darwin':
            subprocess.call(['open', path])

    def _project_changed(self, proj):
        with self.ui.busy():
            if proj is not None:
                if len(proj.media) == 0:
                    proj.load()
                self.name = proj.name
                self.current_dir = proj.root
                self.current_file = None

    def _current_dir_changed(self, d):
        self.parent = d.parent
        self.pager.data = d.directories + d.files

    def _current_file_changed(self, file):
        if file is None:
            return
        self.media = file.media

    def _csv_file_default(self):
        return ValidPath(path=join('~', 'Downloads', 'data.csv'),
                         is_file=True)

    def _pager_default(self):
        p = Pager(limit=20)
        p.on_trait_change(self.view, 'selected')
        return p



class VixenUI(HasTraits):

    vixen = Instance(Vixen)

    mode = Enum('edit', 'view')

    editor = Instance(ProjectEditor)

    viewer = Instance(ProjectViewer)

    processor = Instance(Processor)

    is_busy = Bool(False)

    loading_image = Str

    def get_context(self):
        return dict(
            ui=self, vixen=self.vixen, editor=self.editor, viewer=self.viewer
        )

    def home(self):
        self.mode = 'edit'

    def edit(self, project):
        self.editor.project = project
        self.mode = 'edit'

    def view(self, project):
        self.viewer.project = project
        self.mode = 'view'
        self.editor.project = None

    def process(self, project):
        jobs = []
        for proc in project.processors:
            jobs.extend(proc.make_jobs(project.media))
        self.processor.jobs = jobs
        self.processor.process()

    def remove(self, project):
        self.vixen.remove(project)
        self.editor.project = None

    def add_project(self):
        projects = self.vixen.projects
        name = 'Project%d'%(len(projects) + 1)
        p = Project(name=name)
        projects.append(p)
        self.editor.project = p

    def save(self):
        with self.busy():
            if self.editor.project is not None:
                self.editor.project.save()
            self.vixen.save()

    @contextmanager
    def busy(self):
        self.is_busy = True
        try:
            yield
        finally:
            self.is_busy = False

    def _vixen_default(self):
        v = Vixen()
        v.load()
        return v

    def _editor_default(self):
        return ProjectEditor(ui=self)

    def _viewer_default(self):
        return ProjectViewer(ui=self)

    def _loading_image_default(self):
        return join(dirname(__file__), 'html', 'loading.gif')

    def _processor_default(self):
        return Processor()
