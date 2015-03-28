import datetime
import os

from traits.api import Dict, HasTraits, Long, Str


class Media(HasTraits):

    ########## Traits to be set by the user #######
    # The file/resource that can be viewed by vixen.  For example, with videos
    # this is typically a webm file which is created when the media is
    # initially  processed by vixen.  If the original path is already a webm,
    # then the view may be the same as the `path` trait.
    view = Str

    # The type of the media, typically ("video", "image" or whatever).  This
    # is technically entirely user defined and hence left as a generic string
    # here.
    type = Str

    # Any user defined tags associated with the media.
    # This is entirely dependent on the nature of the user's data and study
    # and is free-form.
    tags = Dict

    ########## Automatically setup traits. ######

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
        obj = cls(path=path)
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
