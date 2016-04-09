from argparse import ArgumentParser
from os.path import join, isdir, exists
import sys

def view(args):
    # We need absolute imports here as PyInstaller does not work with
    # relative imports in the entry point script.
    from vixen.vixen import VixenUI
    ui = VixenUI()
    ui.vixen.load()
    from vixen.vixen_ui import main
    main(**ui.get_context())


def main():
    desc = "ViXeN: view, extract and annotate media"
    parser = ArgumentParser(description=desc, prog='vixen')
    args = parser.parse_args()
    view(args)


if __name__ == '__main__':
    main()
