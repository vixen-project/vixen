
import datetime
import json
import os
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
