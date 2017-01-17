# Done for pyinstaller.
from __future__ import absolute_import

from argparse import ArgumentParser


def make_ui():
    # We need absolute imports here as PyInstaller does not work with
    # relative imports in the entry point script.
    from vixen.vixen import VixenUI
    ui = VixenUI()
    ui.vixen.load()
    return ui


def view(dev, port):
    from vixen.vixen_ui import main
    ui = make_ui()
    main(dev=dev, port=port, **ui.get_context())


def main():
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
    args = parser.parse_args()
    if args.version:
        import vixen
        print("ViXeN version: %s" % vixen.__version__)
    elif args.console:
        ui = make_ui()
        import code
        code.interact(local=locals())
    else:
        view(dev=args.dev, port=args.port)


if __name__ == '__main__':
    main()
