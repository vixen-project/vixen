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

    extensions = List(Str)

    def __getstate__(self):
        files = [x.path for x in self.files]
        dirs = [d.__getstate__() for d in self.directories]
        d = dict(path=self.path, files=files, directories=dirs,
                 extensions=self.extensions)
        return d

    def __setstate__(self, state):
        self.trait_setq(path=state['path'])
        self.files = [File(path=x, parent=self) for x in state['files']]
        self.extensions = state.get('extensions', [])
        dirs = []
        for dir_state in state['directories']:
            d = Directory(parent=self, extensions=self.extensions)
            d.__setstate__(dir_state)
            dirs.append(d)
        self.directories = dirs

    def __repr__(self):
        return 'Directory(path=%r)'%self.path

    def refresh(self):
        self._path_changed(self.path)

    def _path_changed(self, new):
        dirs = []
        files = []
        extensions = self.extensions
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
        self.directories = dirs
        self.files = files

    def _get_relpath(self):
        if self.parent is None:
            return ''
        else:
            return os.path.join(self.parent.relpath, self.name)

    def _get_name(self):
        return os.path.basename(self.path)

    def _extensions_changed(self, new, old):
        if len(self.path) > 0:
            if set(new) != set(old):
                self._path_changed(self.path)

    def _extensions_items_changed(self):
        if len(self.path) > 0:
            self._path_changed(self.path)
