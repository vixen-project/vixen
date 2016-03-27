import json

from traits.api import (Any, Dict, Enum, HasTraits, Instance, List, Long, 
                        Property, Str)

from .media import Media
from .directory import Directory


class TagInfo(HasTraits):
    name = Str
    type = Enum("string", "int", "float", "bool")
    default = Any

    def _default_default(self):
        map = {"string": "", "int": 0, "float": 0.0, "bool": False}
        return map[self.type]


def open_file(fname_or_file, mode='r'):
    if hasattr(fname_or_file, 'read'):
        return fname_or_file
    else:
        return open(fname_or_file, mode)


class Project(HasTraits):
    name = Str
    description = Str
    path = Str
    root = Instance(Directory)
    tags = List(TagInfo)

    media = Dict(Str, Media)

    def add_tag(self, name, type):
        ti = TagInfo(name=name, type=type)
        self.tags.append(ti)
        for m in self.media.values():
            if name not in m.tags:
                m.tags[name] = ti.default

    def export_csv(self, fp, cols=None):
        """Export metadata to a csv file.  If `cols` are not specified,
        it writes out all the useful metadata.

        Parameters
        -----------

        path: str: a path to the csv file to dump.
        cols: sequence: a sequence of columns to write.
        """
        lines = []
        data = []
        all_keys = set()
        for key in sorted(self.media.keys()):
            item = self.media[key]
            d = item.flatten()
            all_keys.update(d.keys())
            data.append(d)
        if cols is None:
            cols = all_keys
            # Typically we don't want these.
            cols -= set(('view', 'poster'))
            cols = list(sorted(cols))
        # Write the header.
        lines.append(','.join(cols))
        # Assemble the lines.
        for d in data:
            line = []
            for key in cols:
                elem = d[key]
                if isinstance(elem, basestring):
                    elem = '"%s"'%elem
                else:
                    elem = str(elem) if elem is not None else ""
                line.append(elem)
            lines.append(','.join(line))

        # Write it out.
        of = open_file(fp, 'w')
        for line in lines:
            of.write(line +'\n')
        of.close()

    def load(self, fp):
        """Load media info from opened file object.
        """
        fp = open_file(fp)
        data = json.load(fp)
        fp.close()
        self.name = data.get('name', '')
        self.description = data.get('description', '')
        self.path = data.get('path')
        self.tags = [TagInfo(name=x[0], type=x[1]) for x in data['tags']]
        self.media = dict((key, Media(**kw)) for key, kw in data['media'])
        self.scan()

    def save(self, fp=None):
        """Save current media info to a file object
        """
        fp = open_file(fp)
        media = [(key, m.to_dict()) for key, m in self.media.items()]
        tags = [(t.name, t.type) for t in self.tags]
        data = dict(
            version=1, path=self.path, name=self.name,
            description=self.description, tags=tags, media=media
        )
        json.dump(data, fp)
        fp.close()

    def save_as(self, path):
        """Save copy to specified path.
        """
        self.save(path)

    def scan(self, refresh=False):
        """Find all the media recursively inside the root directory.
        This will not clobber existing records but will add any new ones.
        """
        media = self.media
        default_tags = dict((ti.name, ti.default) for ti in self.tags)
        def _scan(dir):
            for f in dir.files:
                if f.relpath not in media:
                    media[f.relpath] = self._create_media(f, default_tags)
            for d in dir.directories:
                if refresh:
                    d.refresh()
                _scan(d)
        if refresh:
            self.root.refresh()
        _scan(self.root)

    def refresh(self):
        self.scan(refresh=True)
 
    def _create_media(self, f, default_tags):
        m = Media.from_path(f.path)
        m.tags = dict(default_tags)
        return m

    def _path_changed(self, path):
        self.root = Directory(path=path)

    def _tags_default(self):
        return [TagInfo(name='processed', type='bool')]

