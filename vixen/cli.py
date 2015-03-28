from argparse import ArgumentParser
from os.path import join, isdir, exists
import sys

def process(args):
    root = args.root
    output = args.output
    quiet = args.quiet
    from vixen.media_manager import MediaManager
    from vixen.process_file import process_file
    vixen = MediaManager(root=root)
    vixen.process(process_file, quiet=quiet)

    if output is None:
        output = join(root, 'info.vxn')
    of = open(output, 'w')
    vixen.save(of)

def view(args):
    root_or_saved = args.root
    if isdir(root_or_saved):
        saved = join(root_or_saved, 'info.vxn')
        if not exists(saved):
            msg = "Error: the root directory seems unprocessed,\n"\
                  "Please run 'vixen process' on the directory."
            print msg
            sys.exit(1)

    elif root_or_saved.endswith('.vxn'):
        saved = root_or_saved

    fp = open(saved)
    from vixen.media_manager import MediaManager
    vixen = MediaManager()
    vixen.load(fp)
    from vixen.vixen_ui import main
    main(vixen)


def main():
    desc = "ViXeN: view, extract and annotate media"
    parser = ArgumentParser(description=desc, prog='vixen')
    subparsers = parser.add_subparsers(
        title='subcommands', description='valid subcommands',
        help='additional help'
    )

    process_cmd = subparsers.add_parser('process')
    process_cmd.add_argument(
        '-q', '--quiet', action='store_true', default=False,
        help='Do not print out progress information while processing.'
        )
    process_cmd.add_argument(
        '-o', '--output', type=str, default=None,
        help='Optional output file to save processed data into.'
        )
    process_cmd.add_argument('root', type=str,
        help='Root of directory to process')
    process_cmd.set_defaults(func=process)

    view_cmd = subparsers.add_parser('view')
    view_cmd.add_argument('root', type=str,
        help='Root of processed directory to view.')
    view_cmd.set_defaults(func=view)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
