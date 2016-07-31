from __future__ import print_function

from os.path import join, dirname
import webbrowser

from jigna.vue_template import VueTemplate
from jigna.web_app import WebApp

from tornado.ioloop import IOLoop
from tornado import autoreload


def main(dev=False, **context):
    async = False
    html_dir = join(dirname(__file__), 'html')
    html_file = join(html_dir, 'vixen_ui.html')
    with open(html_file) as fp:
        html = fp.read()
        html = html.replace('$HTML_ROOT', html_dir)
    template = VueTemplate(html=html, base_url='/', async=async)
    ioloop = IOLoop.instance()
    if dev:
        port = 8000
    else:
        from jigna.utils.web import get_free_port
        port = get_free_port()
    app = WebApp(
        template=template, context=context,
        port=port, async=async,
        autoreload=True
    )
    autoreload.watch(html_file)
    app.listen(port)
    url = 'http://localhost:%d'%port
    if dev:
        print("Point your browser to", url)
    else:
        webbrowser.open(url)
    ioloop.start()
