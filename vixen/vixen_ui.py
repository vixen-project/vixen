from jigna.api import Template, WebApp
from os.path import join, dirname
from tornado.ioloop import IOLoop
from tornado import autoreload


def main(media_manager):
    html_file = join(dirname(__file__), 'html', 'vixen_ui.html')
    template = Template(html_file=html_file, base_url='/', async=True)
    ioloop = IOLoop.instance()
    app = WebApp(
        template=template, context={'vixen':media_manager}, port=8000,
        autoreload=True
    )
    autoreload.watch(html_file)
    app.listen(8000)
    url = 'http://localhost:8000'
    print "Point your browser to", url
    ioloop.start()
