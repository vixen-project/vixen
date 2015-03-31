
import datetime
import json
import os
import shutil
from urllib import quote

from traits.api import HasTraits, Directory, List, Str

from .media import Media

def get_file_saved_time(path):
    dt = datetime.datetime.fromtimestamp(os.stat(path).st_ctime)
    return dt.ctime()


class MediaManager(HasTraits):
    root = Directory

    media = List(Media)

    saved_file = Str

    last_save_time = Str

    def load_processed_results(self, results):
        """Load data from the results from the Media processor.
        """
        media = []
        for path, result in results:
            if result is not None:
                type, view, tags = result
                m = Media.from_path(path)
                m.set(type=type, view=quote(view), tags=tags)
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
