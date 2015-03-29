from collections import defaultdict

from traits.api import HasTraits, List, Instance, Int, Str, Dict

from .media import Media
from .media_manager import MediaManager

class FilteredView(HasTraits):
    manager = Instance(MediaManager)

    grid = Int(1)

    camera = Str

    media = List(Media)

    selected = Instance(Media)

    grid_camera_map = Dict

    available_cameras = List
    available_grids = List


    def _manager_changed(self, manager):
        grids = defaultdict(lambda: defaultdict(list))
        for media in manager.media:
            tags = media.tags
            grid = int(tags.get('grid'))
            camera = tags.get('camera')
            grids[grid][camera].append(media)

        self.grid_camera_map = dict(grids)
        self.available_grids = list(sorted(grids.keys()))
        if self.grid not in grids:
            self.grid = self.available_grids[0]
            self.camera = self.available_cameras[0]

    def _camera_changed(self, camera):
        self.media = self.grid_camera_map.get(self.grid).get(camera)

    def _grid_changed(self, grid):
        available_cameras = self.grid_camera_map[grid].keys()
        self.available_cameras = available_cameras

    def _available_cameras_changed(self):
        if self.camera not in self.available_cameras:
            self.camera = self.available_cameras[0]
