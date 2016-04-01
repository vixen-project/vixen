from argparse import ArgumentParser
from os.path import join, isdir, exists
import sys

def process(args):
    root = args.root
    output = args.output
    quiet = args.quiet
    if output is None:
        output = join(root, 'info.vxn')
        if exists(output):
            msg = "WARNING: You seem to have already processed this "\
                  "directory!\nThis will overwrite the current data."
            print msg
            ans = raw_input("Are you sure you want to proceed? (y/n): ")
            if ans not in ('y', 'Y'):
                print "Aborting."
                return

    from vixen.media_processor import MediaProcessor
    from vixen.media_manager import MediaManager
    from vixen.process_file import process_file
    if args.n is not None:
        mp = MediaProcessor(number_of_processes=args.n)
    else:
        mp = MediaProcessor()
    results = mp.process(root, process_file, quiet=quiet)
    vixen = MediaManager(root=root)
    vixen.load_processed_results(results)

    with open(output, 'w') as of:
        vixen.save(of)
    print "Done."

def view(args):
    from .vixen import VixenUI
    ui = VixenUI()
    ui.vixen.load()
    from .vixen_ui import main
    main(**ui.get_context())


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
    process_cmd.add_argument(
        '-n', type=int, default=None,
        help='Maximum number of parallel processes allowed for processing.'
        )
    process_cmd.add_argument('root', type=str,
        help='Root of directory to process')
    process_cmd.set_defaults(func=process)

    view_cmd = subparsers.add_parser('view')
    view_cmd.set_defaults(func=view)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
