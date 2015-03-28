import datetime
import os
from os.path import exists, split, splitext

from traits.api import (Bool, HasTraits, Str, Int, Enum, Float, Long, Property)


class Video(HasTraits):

    # The name of the video.
    video = Str

    # The name of the web video.
    webm_video = Str

    # The poster image extracted from the video.
    poster = Str

    # The time extracted from the image (or set by hand)
    extracted_time = Str

    # The time obtained from the video's timestamp.
    file_time = Str

    file_date = Str

    # The time obtained from the directory structure.
    grid_date = Str

    # The mtime of the video
    video_mtime = Long

    # Grid number
    grid = Str

    # Camera number
    camera = Str

    species = Str

    number = Int

    age = Float

    sex = Enum('unknown', 'male', 'female')

    pressure = Str

    temperature = Str

    # Remarks for this file.
    remarks = Str

    ready = Property(Bool)

    def _parse_path(self, path):
        rest, video = split(path)
        rest, camera = split(rest)
        rest, grid = split(rest)
        rest, date = split(rest)
        return camera, grid, date

    @classmethod
    def from_video(cls, video):
        obj = cls(video=video)
        obj.webm_video = splitext(video)[0] + '.webm'
        obj.poster = splitext(video)[0] + '.jpg'
        camera, grid, date = obj._parse_path(video)
        obj.camera = camera
        obj.grid = grid[5:]
        obj.grid_date = date
        obj.video_mtime = long(os.stat(video).st_mtime)
        dt = datetime.datetime.fromtimestamp(obj.video_mtime)
        obj.file_time = str(dt.time())
        date = dt.date()
        obj.file_date = date.strftime('%d %b %Y')
        return obj

    def process(self, executor):
        if not exists(self.webm_video):
            command = ["ffmpeg", "-i", self.video, self.webm_video]
            executor.submit(command)
        if not exists(self.poster):
            command = ["ffmpeg", "-i", self.video,
                       "-ss", "0", "-vframes", "1", self.poster]
            executor.submit(command)

    def _get_ready(self):
        return exists(self.webm_video)
