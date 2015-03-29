import os
from os.path import abspath, exists, split, splitext

def _parse_path(path):
    rest, video = split(path)
    rest, camera = split(rest)
    rest, grid = split(rest)
    rest, date = split(rest)
    return camera, grid[5:], date

def _process_avi(path):
    video = abspath(path)
    webm_video = splitext(video)[0] + '.webm'
    poster = splitext(video)[0] + '.jpg'

    import subprocess
    if not exists(webm_video):
        command = ["ffmpeg", "-i", video, webm_video]
        out = subprocess.check_output(command, stderr=subprocess.STDOUT)
    if not exists(poster):
        command = ["ffmpeg", "-i", video,
                    "-ss", "0", "-vframes", "1", poster]
        out = subprocess.check_output(command, stderr=subprocess.STDOUT)
    return webm_video, poster


def process_file(path):
    """Process Kadambari's videos.

    This converts any AVI files to webm so they can be viewed, parses
    the file path to determine the tags and returns a bunch of tags.
    """
    size = os.stat(path).st_size
    ext = splitext(path)[1]
    if (ext not in ['.avi', '.AVI']) or (size == 0):
        return

    view, poster = _process_avi(path)
    type = "video"
    camera, grid, grid_date = _parse_path(path)
    jackal, indian_fox, desert_fox, dog = 0, 0, 0, 0
    others = ""
    pressure = ""
    temperature = ""
    remarks = ""
    tags = dict(
        poster=poster, camera=camera, grid=grid,
        grid_date=grid_date, jackal=jackal, indian_fox=indian_fox,
        desert_fox=desert_fox, dog=dog,
        others=others, pressure=pressure, temperature=temperature,
        remarks=remarks
    )
    return type, view, tags
