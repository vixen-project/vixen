
import datetime
import json
import os
import shutil
import sys

from traits.api import (HasTraits, Instance, Directory, List, Str)

from .media import Media

def get_all_files(root):
    """Given a directory find all the files nested inside.
    """
    result = []
    for root, dirs, files in os.walk(root):
        for name in files:
            result.append(os.path.join(root, name))
    return result

def get_file_saved_time(path):
    dt = datetime.datetime.fromtimestamp(os.stat(path).st_ctime)
    return dt.ctime()


class MediaManager(HasTraits):
    root = Directory

    media = List(Media)

    selected = Instance(Media)

    saved_file = Str

    last_save_time = Str

    def process(self, processor, quiet=False):
        """Process all files inside the specified root.
        """
        file_names = get_all_files(self.root)
        n_files = len(file_names)
        media = []
        for count, file_name in enumerate(file_names):
            if not quiet:
                print "\rProcessing", count, "of", n_files, ":", file_name,
                sys.stdout.flush()
            result = processor(file_name)
            if result is not None:
                type, view, tags = result
                m = Media.from_path(file_name)
                m.set(type=type, view=view, tags=tags)
                media.append(m)
        self.media = media

    def save(self, fp=None):
        """Save current media info to a file object
        """
        media = [m.to_dict() for m in self.media]
        data = dict(version=1, root=self.root, media=media)
        if fp is None:
            fp = open(self.saved_file, 'w')
        json.dump(data, fp)
        fp.close()
        if hasattr(fp, 'name'):
            self._update_saved_file_info(fp.name)

    def save_as(self, path):
        """Save copy to specified path.
        """
        self.save()
        shutil.copy(self.saved_file, path)

    def export_csv(self, path, cols=None):
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
        for item in self.media:
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
                elem = str(elem) if elem is not None else ""
                line.append(elem)
            lines.append(','.join(line))

        # Write it out.
        with open(path, 'w') as of:
            for line in lines:
                of.write(line +'\n')

    def load(self, fp):
        """Load media info from opened file object.
        """
        if hasattr(fp, 'name'):
            self._update_saved_file_info(fp.name)
        data = json.load(fp)
        self.root = data.get('root')
        self.media = [Media(**kw) for kw in data['media']]

    def _update_saved_file_info(self, path):
        self.saved_file = path
        self.last_save_time = get_file_saved_time(path)
