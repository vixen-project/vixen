import os
from os.path import basename, join

from traits.api import Any, HasTraits, Instance, List, Property, Str


class File(HasTraits):
    path = Str
    parent = Instance('Directory')
    name = Str
    relpath = Str

    def __init__(self, path, parent, relpath=None, name=None):
        self.path = path
        self.parent = parent
        self.name = basename(path) if name is None else name
        if relpath is None:
            self.relpath = join(parent.relpath, self.name)
        else:
            self.relpath = relpath

    def __repr__(self):
        return 'File(path=%r)' % self.path


class Directory(HasTraits):
    path = Str
    name = Str
    relpath = Str
    parent = Instance('Directory')
    directories = Property(List(Instance('Directory')))
    files = List(Instance(File))

    extensions = List(Str)

    _directories = List(Instance('Directory'))
    _directory_state = Any

    def __getstate__(self):
        files = [(x.path, x.relpath, x.name) for x in self.files]
        if self._directory_state is None:
            dirs = [d.__getstate__() for d in self.directories]
        else:
            dirs = self._directory_state
        result = dict(path=self.path, files=files, directories=dirs,
                      extensions=self.extensions, relpath=self.relpath,
                      name=self.name)
        return result

    def __setstate__(self, state):
        extensions = state.get('extensions', [])
        path = state['path']
        if 'relpath' in state:
            self.__dict__.update(dict(
                relpath=state['relpath'], path=path,
                name=state['name'], extensions=extensions
            ))
            self.files = [
                File(path=x[0], parent=self, relpath=x[1], name=x[2])
                for x in state['files']
            ]
        else:
            name = basename(path)
            if self.parent is not None:
                relpath = join(self.parent.relpath, name)
            else:
                relpath = ''
            self.__dict__.update(dict(
                path=path, extensions=extensions, name=name, relpath=relpath
            ))
            self.files = [File(path=x, parent=self) for x in state['files']]

        self._directory_state = state['directories']

    def __repr__(self):
        return 'Directory(path=%r)' % self.path

    def refresh(self):
        self._path_changed(self.path)

    def _path_changed(self, new):
        dirs = []
        files = []
        extensions = self.extensions
        self.name = basename(new)
        if self.parent is None:
            self.relpath = ''
        else:
            self.relpath = join(self.parent.relpath, self.name)
        try:
            for pth in os.listdir(new):
                full_path = os.path.join(new, pth)
                if os.path.isdir(full_path):
                    d = Directory(extensions=extensions, parent=self)
                    d.path = full_path
                    dirs.append(d)
                elif os.path.isfile(full_path):
                    if len(extensions) == 0:
                        files.append(File(path=full_path, parent=self))
                    elif os.path.splitext(pth.lower())[1] in extensions:
                        files.append(File(path=full_path, parent=self))

        except IOError:
            pass
        self._directory_state = None
        self._directories = dirs
        self.files = files

    def _extensions_changed(self, new, old):
        if len(self.path) > 0:
            if set(new) != set(old):
                self._path_changed(self.path)

    def _extensions_items_changed(self):
        if len(self.path) > 0:
            self._path_changed(self.path)

    def _get_directories(self):
        if self._directory_state is not None:
            dirs = []
            for dir_state in self._directory_state:
                d = Directory(parent=self)
                d.__setstate__(dir_state)
                dirs.append(d)
            self._directories = dirs
            self._directory_state = None

        return self._directories
