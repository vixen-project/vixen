import datetime
import os

from jigna.core.wsgi import guess_type
from traits.api import Date, Dict, HasTraits, Int, Property, Str

# Some pre-defined file extensions.
IMAGE = ['.bmp', '.png', '.gif', '.jpg', '.jpeg', '.svg']
VIDEO = ['.avi', '.mp4', '.ogv', '.webm', '.flv']
AUDIO = ['.mp3', '.wav', '.ogg', '.m4a']
HTML = ['.html', '.htm']
PDF = ['.pdf']
# Only add the ones that mimetypes does not detect correctly here.
TEXT = ['.md', '.rst', '.pyx']


class Media(HasTraits):

    # The type of the media, typically ("video", "image" or whatever).  This
    # is technically entirely user defined and hence left as a generic string
    # here.
    type = Str

    # Any user defined tags associated with the media.
    # This is entirely dependent on the nature of the user's data and study
    # and is free-form.
    tags = Dict

    # The file name.
    file_name = Property(Str)

    # The file path.
    path = Str

    # The relative path of the file, this is typically relative to the root
    # of a particular project.
    relpath = Str

    # The date string obtained from the file's mtime.
    mtime = Str

    # The date string obtained from the file's ctime.
    ctime = Str

    # The size of the file in bytes.
    size = Int

    # The created time of the file. This and the _mtime are private as we
    # cannot send this to the HTML UI as it is not JSON serializable. However
    # they are is useful for searching through the media.
    _ctime = Date

    # The modified time of the file.
    _mtime = Date

    @classmethod
    def from_path(cls, path, relpath):
        obj = cls(path=os.path.abspath(path))
        obj.relpath = relpath
        obj.update()
        return obj

    def to_dict(self):
        return self.__dict__

    def flatten(self):
        """Return a flattened dict of the metadata for processing or dumping.
        """
        data = dict(self.to_dict())
        tags = data.pop('tags', {})
        data.update(tags)
        return data

    def update(self):
        """Update the metadata from the file.
        """
        path = self.path
        if os.path.exists(path):
            stat = os.stat(path)
            self._mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
            self._ctime = datetime.datetime.fromtimestamp(stat.st_ctime)
            self.size = stat.st_size
            self.mtime = self._mtime.strftime('%d %b %Y %H:%M:%S')
            self.ctime = self._ctime.strftime('%d %b %Y %H:%M:%S')

    def _get_file_name(self):
        return os.path.basename(self.path)

    def _path_changed(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE:
            self.type = "image"
        elif ext in VIDEO:
            self.type = "video"
        elif ext in AUDIO:
            self.type = "audio"
        elif ext in HTML:
            self.type = "html"
        elif ext in PDF:
            self.type = "pdf"
        elif ext in TEXT:
            self.type = "text"
        else:
            type, encoding = guess_type(path)
            result = "unknown"
            if len(type) > 0:
                if type.startswith('text'):
                    result = 'text'
                elif type.startswith('video'):
                    result = 'video'
                elif type.startswith('audio'):
                    result = 'audio'
                elif type.startswith('image'):
                    result = 'image'
                else:
                    self.type = 'unknown'
            self.type = result
