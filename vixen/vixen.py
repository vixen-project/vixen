from contextlib import contextmanager
import copy
import json
from os.path import (abspath, dirname, exists, expanduser, join, isdir,
                     splitext)
import os
import subprocess
import sys

from traits.api import (Bool, DelegatesTo, Enum, HasTraits, List, Str,
                        Instance, Property)

from .project import Project, TagInfo, get_project_dir
from .directory import File, Directory
from .media import Media


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

    available_exts = List(Str)

    valid_path = Bool
    tag_name = Str

    ui = Instance('VixenUI')

    def add_tag(self, name):
        self.tags.append(TagInfo(name=name, type="string"))

    def remove_tag(self, index):
        del self.tags[index]

    def apply(self):
        with self.ui.busy():
            cp = self.project
            if cp is not None and self.valid_path:
                cp.name = self.name
                cp.description = self.description
                cp.path = self._get_actual_path(self.path)
                cp.update_tags(self.tags)
                cp.save()
                if self.ui is not None:
                    self.ui.save()
                self.available_exts = self._get_info()

    def _get_actual_path(self, path):
        return abspath(expanduser(path))

    def _get_info(self):
        cp = self.project
        exts = []
        if cp is not None:
            exts = sorted(
                set(splitext(x)[1] for x in cp.media),
                key=lambda x: x.lower()
            )
        return exts

    def _project_changed(self, proj):
        with self.ui.busy():
            if proj is not None:
                if len(proj.media) == 0:
                    proj.load()
                self.name = proj.name
                self.description = proj.description
                self.path = self._get_actual_path(proj.path)
                self.tags = copy.deepcopy(proj.tags)
                self.available_exts = self._get_info()

    def _path_changed(self, path):
        self.valid_path = isdir(self._get_actual_path(path))


class ProjectViewer(HasTraits):

    project = Instance(Project, allow_none=True)

    name = Str

    ui = Instance('VixenUI')

    parent = Instance(Directory)

    current_dir = Instance(Directory)

    current_file = Instance(File)

    paths = List

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
                    proj.save()
                self.name = proj.name
                self.current_dir = proj.root
                self.current_file = None

    def _current_dir_changed(self, d):
        self.parent = d.parent
        self.paths = d.directories + d.files

    def _current_file_changed(self, file):
        if file is None:
            return
        self.media = file.media

    def _csv_file_default(self):
        return ValidPath(path=join('~', 'Downloads', 'data.csv'), is_file=True)


class VixenUI(HasTraits):

    vixen = Instance(Vixen)

    mode = Enum('edit', 'view')

    editor = Instance(ProjectEditor)

    viewer = Instance(ProjectViewer)

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
