from __future__ import print_function

import logging
from os.path import dirname, isdir, join
import sys
import webbrowser

from jigna.vue_template import VueTemplate
from jigna.web_app import WebApp

from tornado.ioloop import IOLoop
from tornado import autoreload


def silence_tornado_access_log():
    logger = logging.getLogger('tornado.access')
    logger.setLevel(logging.WARNING)


def get_html_file():
    html_dir = join(dirname(__file__), 'html')

    # When the app is bundled by pyinstaller, we cannot have a vixen directory
    # in the same place as the executable vixen so the HTML/CSS/JS is all
    # placed in the vixen_data directory instead.
    if not isdir(html_dir):
        html_dir = join(dirname(dirname(__file__)), 'vixen_data', 'html')

    return join(html_dir, 'vixen_ui.html')


def get_html(html_file):
    """Returns the HTML to render.
    """
    # The root is prepended to media.path, useful on windows as '/' has to be
    # prepended using a js expression
    root = ''
    html_dir = dirname(html_file)
    if sys.platform.startswith('win'):
        html_dir = '/' + html_dir
        root = "'/' + "

    with open(html_file) as fp:
        html = fp.read()
        html = html.replace('$HTML_ROOT', html_dir)
        html = html.replace('$ROOT', root)
    return html


def main(dev=False, port=None, test=False, **context):
    async = False

    base_url = '/'
    if sys.platform.startswith('win'):
        base_url = ''

    html_file = get_html_file()
    html = get_html(html_file)
    template = VueTemplate(html=html, base_url=base_url, async=async)
    silence_tornado_access_log()
    ioloop = IOLoop.current()
    if port is None:
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
    url = 'http://localhost:%d' % port
    if dev:
        print("Point your browser to", url)
    else:
        webbrowser.open(url)
    if not test:
        # When running tests, don't start the ioloop.
        ioloop.start()
    else:
        return ioloop
