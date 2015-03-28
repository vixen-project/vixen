from traits.api import (HasTraits, Instance, Directory, List)

import os

from .video import Video
from .command_executor import CommandExecutor

def iter_all_videos(root, exts=('avi', 'AVI')):
    """Given a directory iterate over all the videos given the extensions
    specified in the `exts` argument.
    """
    for root, dirs, files in os.walk(root):
        for name in files:
            if name.endswith(exts):
                yield os.path.join(root, name)

class VideoManager(HasTraits):
    root = Directory
    videos = List(Video)
    executor = Instance(CommandExecutor)

    selected = Instance(Video)

    def _executor_default(self):
        return CommandExecutor()

    def _root_changed(self):
        self.executor.run()
        videos = []
        for fname in iter_all_videos(self.root):
            video = Video.from_video(fname)
            videos.append(video)
        self.videos = videos
