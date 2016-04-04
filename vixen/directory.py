import os

from traits.api import HasTraits, Instance, List, Property, Str

from .media import Media

class File(HasTraits):
    path = Str
    parent = Instance('Directory')
    name = Property(Str)
    relpath = Property(Str)

    media = Instance(Media)

    def __repr__(self):
        return self.name

    def _get_relpath(self):
        return os.path.join(self.parent.relpath, self.name)

    def _get_name(self):
        return os.path.basename(self.path)


class Directory(HasTraits):
    path = Str
    name = Property(Str)
    relpath = Property(Str)
    parent = Instance('Directory')
    directories = List(Instance('Directory'))
    files = List(Instance(File))

    def __repr__(self):
        return 'Directory(path=%r)'%self.path

    def refresh(self):
        self._path_changed(self.path)

    def _path_changed(self, new):
        dirs = []
        files = []
        try:
            for pth in os.listdir(new):
                full_path = os.path.join(new, pth)
                if os.path.isdir(full_path):
                    dirs.append(Directory(parent=self, path=full_path))
                elif os.path.isfile(full_path):
                    files.append(File(path=full_path, parent=self))
        except IOError:
            pass
        self.directories = dirs
        self.files = files

    def _get_relpath(self):
        if self.parent is None:
            return ''
        else:
            return os.path.join(self.parent.relpath, self.name)

    def _get_name(self):
        return os.path.basename(self.path)
