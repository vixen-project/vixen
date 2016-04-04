from jigna.vue_template import VueTemplate
from jigna.web_app import WebApp
from os.path import join, dirname
from tornado.ioloop import IOLoop
from tornado import autoreload


def main(**context):
    async = False
    html_file = join(dirname(__file__), 'html', 'vixen_new_ui.html')
    template = VueTemplate(html_file=html_file, base_url='/', async=async)
    ioloop = IOLoop.instance()
    app = WebApp(
        template=template, context=context,
        port=8000, async=async,
        autoreload=True
    )
    autoreload.watch(html_file)
    app.listen(8000)
    url = 'http://localhost:8000'
    print "Point your browser to", url
    ioloop.start()
