# Done for pyinstaller.
from __future__ import absolute_import

from argparse import ArgumentParser
from os.path import join, isdir, exists
import sys

def view(dev):
    # We need absolute imports here as PyInstaller does not work with
    # relative imports in the entry point script.
    from vixen.vixen import VixenUI
    ui = VixenUI()
    ui.vixen.load()
    from vixen.vixen_ui import main
    main(dev=dev, **ui.get_context())


def main():
    desc = "ViXeN: view, extract and annotate media"
    parser = ArgumentParser(description=desc, prog='vixen')
    parser.add_argument("--dev", default=False, action="store_true",
                        help="Do not open a browser.")
    args = parser.parse_args()
    view(dev=args.dev)


if __name__ == '__main__':
    main()
