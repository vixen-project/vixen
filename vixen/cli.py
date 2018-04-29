# Done for pyinstaller.
from __future__ import absolute_import

from argparse import ArgumentParser
import logging
from logging.handlers import RotatingFileHandler
import os
import sys

from vixen.common import get_project_dir

logger = logging.getLogger(__name__)


def _logging_excepthook(exc_type, value, tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, value, tb)
        return
    logger.error('Uncaught exception', exc_info=(exc_type, value, tb))


def log_platform_info():
    import vixen
    logger.info('ViXeN version: %s', vixen.__version__)
    logger.info('Runing from %s',
                os.path.abspath(os.path.dirname(vixen.__file__)))
    import platform
    logger.info(platform.uname())


def setup_logger():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    logging.captureWarnings(True)
    logdir = get_project_dir()
    fname = os.path.join(logdir, 'vixen.log')
    handler = RotatingFileHandler(
        filename=fname, maxBytes=2**18, backupCount=3
    )
    formatter = logging.Formatter(
        '%(levelname)s|%(asctime)s|%(name)s|%(message)s'
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)
    sys.excepthook = _logging_excepthook
    logger.info('**** Starting ViXeN ****')
    logger.info('Project root: %s', logdir)
    log_platform_info()


def make_ui():
    # We need absolute imports here as PyInstaller does not work with
    # relative imports in the entry point script.
    from vixen.vixen import VixenUI
    ui = VixenUI()
    ui.setup_logging_handler()
    ui.vixen.load()
    return ui


def view(dev, port):
    from vixen.vixen_ui import main
    ui = make_ui()
    main(dev=dev, port=port, **ui.get_context())


def main(args=None):
    setup_logger()
    desc = "ViXeN: view, extract and annotate media"
    parser = ArgumentParser(description=desc, prog='vixen')
    parser.add_argument("--dev", default=False, action="store_true",
                        help="Do not open a browser.")
    parser.add_argument("--port", default=None, dest="port", type=int,
                        help="Port to use for server.")
    parser.add_argument(
        "--version", default=False, action="store_true",
        help="Show the ViXeN version."
    )
    parser.add_argument(
        "--console", default=False, action="store_true",
        help="Start a Python console (useful for direct scripting)."
    )
    opts = parser.parse_args(args)
    logger.info('vixen called as: %s', sys.argv)
    logger.info('Parsed command line args: %s', opts)
    if opts.version:  # pragma: no cover
        import vixen
        print("ViXeN version: %s" % vixen.__version__)
    elif opts.console:  # pragma: no cover
        ui = make_ui()
        import code
        code.interact(local=locals())
    else:
        view(dev=opts.dev, port=opts.port)


if __name__ == '__main__':
    main()
