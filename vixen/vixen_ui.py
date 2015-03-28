from jigna.api import Template, WebApp
from os.path import abspath, expanduser, join, dirname
import sys
from tornado.ioloop import IOLoop
from tornado import autoreload

from vixen.video_manager import VideoManager


def main():
    root = abspath(expanduser(sys.argv[1]))
    html_file = join(dirname(__file__), 'html', 'vixen_ui.html')
    template = Template(html_file=html_file, base_url='/', async=True)
    ioloop = IOLoop.instance()
    vixen = VideoManager(root=root)
    app = WebApp(template=template, context={'vixen':vixen}, port=8000,
                 autoreload=True)
    autoreload.watch(html_file)
    app.listen(8000)
    url = 'http://localhost:8000'
    print "Point your browser to", url
    ioloop.start()

if __name__ == '__main__':
    main()
