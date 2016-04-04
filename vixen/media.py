import datetime
import os

from traits.api import Dict, HasTraits, Long, Property, Str

# Some pre-defined file extensions.
IMAGE = ['.bmp', '.png', '.gif', '.jpg', '.jpeg']
VIDEO = ['.avi', '.mp4', '.ogv', '.webm', '.flv']
AUDIO = ['.mp3', '.wav', '.ogg', '.m4a']


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

    # The time obtained from the video's timestamp.
    time = Str

    # The date obtained from the video's timestamp.
    date = Str

    # The size of the file in bytes.
    size = Long


    @classmethod
    def from_path(cls, path):
        obj = cls(path=os.path.abspath(path))
        stat = os.stat(path)
        video_mtime = long(stat.st_mtime)
        obj.size = stat.st_size
        dt = datetime.datetime.fromtimestamp(video_mtime)
        obj.time = str(dt.time())
        date = dt.date()
        obj.date = date.strftime('%d %b %Y')
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
        else:
            self.type = "unknown"
