from collections import namedtuple
import datetime
import os

from jigna.core.wsgi import guess_type
from traits.api import Dict, HasTraits, Int, Long, Property, Str
from whoosh.util.times import datetime_to_long


# Some pre-defined file extensions.
IMAGE = ['.bmp', '.png', '.gif', '.jpg', '.jpeg', '.svg']
VIDEO = ['.avi', '.mp4', '.ogv', '.webm', '.flv']
AUDIO = ['.mp3', '.wav', '.ogg', '.m4a']
HTML = ['.html', '.htm']
PDF = ['.pdf']
# Only add the ones that mimetypes does not detect correctly here.
TEXT = ['.md', '.rst', '.pyx']


MediaData = namedtuple(
    'MediaData',
    ['path', 'relpath', 'file_name', 'size', 'ctime', 'ctime_',
     'mtime', 'mtime_', 'type']
)


def find_type(path):
    ext = os.path.splitext(path)[1].lower()
    result = "unknown"
    if ext in IMAGE:
        result = "image"
    elif ext in VIDEO:
        result = "video"
    elif ext in AUDIO:
        result = "audio"
    elif ext in HTML:
        result = "html"
    elif ext in PDF:
        result = "pdf"
    elif ext in TEXT:
        result = "text"
    else:
        type, encoding = guess_type(path)
        if len(type) > 0:
            if type.startswith('text'):
                result = 'text'
            elif type.startswith('video'):
                result = 'video'
            elif type.startswith('audio'):
                result = 'audio'
            elif type.startswith('image'):
                result = 'image'
    return result


def get_media_data(path, relpath):
    if os.path.exists(path):
        stat = os.stat(path)
        _mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
        _ctime = datetime.datetime.fromtimestamp(stat.st_ctime)
        size = stat.st_size
        mtime = _mtime.strftime('%d %b %Y %H:%M:%S')
        ctime = _ctime.strftime('%d %b %Y %H:%M:%S')
        fname = os.path.basename(path)
        _ctime = datetime_to_long(_ctime)
        _mtime = datetime_to_long(_mtime)
        type = find_type(path)
        return MediaData(
            path, relpath, fname, size, ctime, _ctime, mtime,
            _mtime, type
        )
    else:
        return None


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
    _ctime = Long

    # The modified time of the file.
    _mtime = Long

    @classmethod
    def from_path(cls, path, relpath):
        obj = cls(path=os.path.abspath(path))
        obj.relpath = relpath
        obj.update()
        return obj

    @classmethod
    def from_data(cls, data, tags):
        obj = cls()
        obj.update(data)
        obj.tags.update(tags)
        return obj

    def to_dict(self):
        return self.__dict__

    def update(self, data=None, tags=None):
        """Update the metadata from the file or from the data given.
        """
        if data is None:
            data = get_media_data(self.path, self.relpath)
        if data is not None:
            self.path = data.path
            self._mtime = data.mtime_
            self.mtime = data.mtime
            self._ctime = data.ctime_
            self.ctime = data.ctime
            self.size = data.size
            self.relpath = data.relpath
            self.type = data.type
        if tags is not None:
            self.tags.update(tags)

    def _get_file_name(self):
        return os.path.basename(self.path)
