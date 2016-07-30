from __future__ import print_function
from jigna.vue_template import VueTemplate
from jigna.web_app import WebApp
from os.path import join, dirname
from tornado.ioloop import IOLoop
from tornado import autoreload


def main(**context):
    async = False
    html_dir = join(dirname(__file__), 'html')
    html_file = join(html_dir, 'vixen_ui.html')
    with open(html_file) as fp:
        html = fp.read()
        html = html.replace('$HTML_ROOT', html_dir)
    template = VueTemplate(html=html, base_url='/', async=async)
    ioloop = IOLoop.instance()
    app = WebApp(
        template=template, context=context,
        port=8000, async=async,
        autoreload=True
    )
    autoreload.watch(html_file)
    app.listen(8000)
    url = 'http://localhost:8000'
    print("Point your browser to", url)
    ioloop.start()
