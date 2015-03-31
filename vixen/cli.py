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

    of = open(output, 'w')
    vixen.save(of)
    print "Done."

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
    mm = MediaManager()
    mm.load(fp)
    from vixen.filtered_view import FilteredView
    vixen = FilteredView()
    vixen.manager = mm
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
    process_cmd.add_argument(
        '-n', type=int, default=None,
        help='Maximum number of parallel processes allowed for processing.'
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
