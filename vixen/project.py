import csv
import datetime
import json_tricks
import logging
import os
from os.path import (abspath, basename, dirname, exists, expanduser, isdir,
                     join, realpath, relpath, splitext)
import re
import shutil
import sys

from traits.api import (Any, Dict, Enum, HasTraits, Instance, List, Long,
                        Str)
from whoosh import fields, qparser, query

from .media import Media
from .directory import Directory
from . import processor


logger = logging.getLogger(__name__)

if sys.version_info[0] > 2:
    unicode = str
INT = fields.NUMERIC(numtype=int)
FLOAT = fields.NUMERIC(numtype=float)


def get_project_dir():
    d = expanduser(join('~', '.vixen'))
    if not isdir(d):
        os.makedirs(d)
    return d


def get_file_saved_time(path):
    dt = datetime.datetime.fromtimestamp(os.stat(path).st_ctime)
    return dt.ctime()


def _get_sample(fname):
    sample = ''
    with open(fname, 'rb') as fp:
        sample += fp.readline() + fp.readline()

    return sample


def _get_csv_headers(fname):
    sample = _get_sample(fname)
    sniffer = csv.Sniffer()
    has_header = sniffer.has_header(sample)
    dialect = sniffer.sniff(sample)
    with open(fname, 'rb') as fp:
        reader = csv.reader(fp, dialect)
        header = next(reader)
    return has_header, header, dialect


class TagInfo(HasTraits):
    name = Str
    type = Enum("string", "int", "float", "bool")
    default = Any

    def __repr__(self):
        return 'TagInfo(%r, %r)' % (self.name, self.type)

    def _default_default(self):
        map = {"string": "", "int": 0, "float": 0.0, "bool": False}
        return map[self.type]


def open_file(fname_or_file, mode='rb'):
    if hasattr(fname_or_file, 'read'):
        return fname_or_file
    else:
        return open(fname_or_file, mode)


def sanitize_name(name):
    name = name.lower()
    name = re.sub(r'\s+', '_', name)
    return re.sub(r'\W+', '', name)


def get_non_existing_filename(fname):
    if exists(fname):
        base, ext = splitext(basename(fname))
        return join(dirname(fname), base + '_a' + ext)
    else:
        return fname


COMMON_TAGS = dict(
    type='string', file_name='string', path='string',
    ctime='string', mtime='string', size='int'
)


def _cleanup_query(q, tag_types):
    type_map = dict(float=FLOAT.from_bytes, int=INT.from_bytes)
    for term in q.leaves():
        if isinstance(term, query.Term):
            if isinstance(term.text, (str, unicode)):
                fieldtype = tag_types[term.fieldname]
                if fieldtype in type_map:
                    term.text = type_map[fieldtype](term.text)
                else:
                    term.text = term.text.lower()
        elif isinstance(term, query.Phrase):
            term.words = [x.lower() for x in term.words]


def _check_value(value, expr):
    if isinstance(expr, (str, unicode)):
        return expr in value.lower()
    else:
        return expr == value


def _check_range(x, term):
    result = True
    if term.start is not None:
        if term.startexcl:
            result &= x > term.start
        else:
            result &= x >= term.start
    if term.end is not None and result:
        if term.endexcl:
            result &= x < term.end
        else:
            result &= x <= term.end
    return result


def _check_date_range(x, term):
    result = True
    if term.startdate is not None:
        result &= x >= term.startdate
    if term.enddate is not None and result:
        result &= x <= term.enddate
    return result


def _get_tag(media, attr):
    if attr in COMMON_TAGS:
        return getattr(media, attr)
    else:
        return media.tags.get(attr)


def _search_media(expr, media):
    if expr.is_leaf():
        if isinstance(expr, query.Term):
            attr = expr.fieldname
            return _check_value(_get_tag(media, attr), expr.text)
        elif isinstance(expr, query.Phrase):
            attr = expr.fieldname
            text = " ".join(expr.words)
            return _check_value(_get_tag(media, attr), text)
        elif isinstance(expr, query.DateRange):
            value = media._ctime if expr.fieldname == 'ctime' else media._mtime
            return _check_date_range(value, expr)
        elif isinstance(expr, query.NumericRange):
            attr = expr.fieldname
            return _check_range(_get_tag(media, attr), expr)
        else:
            print("Unsupported term: %r" % expr)
            return False
    else:
        if isinstance(expr, query.And):
            result = True
            for child in expr.children():
                result &= _search_media(child, media)
                if not result:
                    break
            return result
        elif isinstance(expr, query.Or):
            result = False
            for child in expr.children():
                result |= _search_media(child, media)
                if result:
                    break
            return result
        elif isinstance(expr, query.Not):
            subquery = list(expr.children())[0]
            return not _search_media(subquery, media)
        else:
            print("Unsupported term: %r" % expr)
            return False


class Project(HasTraits):
    name = Str
    description = Str
    path = Str
    root = Instance(Directory)
    tags = List(TagInfo)

    media = Dict(Str, Media)

    extensions = List(Str)

    processors = List(processor.FactoryBase)

    number_of_files = Long

    # Path where the project data is saved.
    save_file = Str

    last_save_time = Str

    _query_parser = Instance(qparser.QueryParser)

    def add_tags(self, tags):
        tags = list(self.tags) + tags
        self.update_tags(tags)

    def update_tags(self, new_tags):
        old_tags = self.tags
        new_tag_names = set(tag.name for tag in new_tags)
        tag_info = dict((tag.name, tag.type) for tag in old_tags)
        removed = []
        added = []
        for tag in new_tags:
            if tag.name not in tag_info:
                added.append(tag)
            elif tag_info[tag.name] != tag.type:
                removed.append(tag)
                added.append(tag)
        for tag in old_tags:
            if tag.name not in new_tag_names:
                removed.append(tag)
        self.tags = new_tags

        for m in self.media.values():
            for tag in removed:
                del m.tags[tag.name]
            for tag in added:
                m.tags[tag.name] = tag.default

        self._query_parser = self._make_query_parser()

    def get(self, relpath):
        """Given the relative path of some media, return a Media instance.
        """
        return self.media[relpath]

    def keys(self):
        """Return all the keys for the media relative paths."""
        return self.media.keys()

    def export_csv(self, fname, cols=None):
        """Export metadata to a csv file.  If `cols` are not specified,
        it writes out all the useful metadata.

        Parameters
        -----------

        fname: str: a path to the csv file to dump.
        cols: sequence: a sequence of columns to write.
        """
        logger.info('Exporting CSV: %s', fname)
        lines = []
        data = []
        all_keys = set()
        for key in sorted(self.media.keys()):
            item = self.media[key]
            d = item.flatten()
            all_keys.update(d.keys())
            data.append(d)

        all_keys -= set(('_ctime', '_mtime'))
        if cols is None:
            cols = all_keys
            cols = list(sorted(cols))
        # Write the header.
        lines.append(','.join(cols))
        # Assemble the lines.
        for d in data:
            line = []
            for key in cols:
                elem = d[key]
                if isinstance(elem, str):
                    elem = '"%s"' % elem
                else:
                    elem = str(elem) if elem is not None else ""
                line.append(elem)
            lines.append(','.join(line))

        # Write it out.
        of = open_file(fname, 'w')
        for line in lines:
            of.write(line + '\n')
        of.close()

    def import_csv(self, fname):
        """Read tag information from given CSV filename.

        Returns the success status and the error message if any. Note that this
        only applies tags for column headers with known tags. Unknown tags are
        not added.

        Parameters
        ----------

        fname : str   Input filename.

        """
        logger.info('Importing tags from: %s', fname)
        has_header, header, dialect = _get_csv_headers(fname)
        if not has_header:
            return False, "The CSV file does not appear to have a header."
        if 'path' not in header:
            msg = "The CSV file does not have a 'path' column."
            return False, msg

        tags = {x: header.index(x.name) for x in self.tags if x.name in header}
        path_idx = header.index('path')
        TRUE = ('1', 't', 'true', 'y', 'yes')
        type_map = {
            'bool': lambda x: x.lower() in TRUE,
            'string': lambda x: x,
            'int': int,
            'float': float
        }

        count = 0
        total = 0
        with open(fname, 'rb') as fp:
            reader = csv.reader(fp, dialect)
            next(reader)  # Skip header
            for record in reader:
                total += 1
                path = record[path_idx]
                rpath = relpath(path, self.path)
                media = self.media.get(rpath)
                if media is not None:
                    count += 1
                    for tag, index in tags.items():
                        data = record[index]
                        try:
                            media.tags[tag.name] = type_map[tag.type](data)
                        except ValueError:
                            pass

        msg = "Read tags for %d paths out of %d entries." % (count, total)
        if count == 0 and total > 0:
            msg += ("\nPlease check that your path column matches "
                    "the media paths.")
            return False, msg
        else:
            msg += ("\nPlease check the imported tags and make sure you "
                    "save the project.")
            return True, msg

    def load(self, fp=None):
        """Load media info from opened file object.
        """
        if fp is None:
            if not exists(self.save_file):
                return
            fp = open_file(self.save_file, 'rb')
        else:
            fp = open_file(fp, 'rb')

        data = json_tricks.load(
            fp, preserve_order=False, ignore_comments=False
        )
        fp.close()
        self.name = data.get('name', '')
        self.description = data.get('description', '')
        self.path = data.get('path')
        self.tags = [TagInfo(name=x[0], type=x[1]) for x in data['tags']]
        self.processors = [processor.load(x)
                           for x in data.get('processors', [])]
        media = dict((key, Media(**kw)) for key, kw in data['media'])
        # Don't send object change notifications when this large data changes.
        self.trait_setq(media=media)
        root = Directory()
        root.__setstate__(data.get('root'))
        self.extensions = root.extensions
        self.root = root
        self.number_of_files = len(self.media)
        # This is needed as this is what makes the association from the media
        # to the file.
        self.scan()

    def save(self):
        """Save current media info to a file object
        """
        if len(self.save_file) > 0:
            self.save_as(self.save_file)
            self._update_last_save_time()
        else:
            raise IOError("No valid save file set.")

    def save_as(self, fp):
        """Save copy to specified path.
        """
        fp = open_file(fp, 'wb')
        media = [(key, m.to_dict()) for key, m in self.media.items()]
        tags = [(t.name, t.type) for t in self.tags]
        root = self.root.__getstate__()
        processors = [processor.dump(x) for x in self.processors]
        data = dict(
            version=1, path=self.path, name=self.name,
            description=self.description, tags=tags, media=media,
            root=root, processors=processors
        )
        json_tricks.dump(data, fp, compression=True)
        fp.close()
        logger.info('Saved project: %s', self.name)

    def scan(self, refresh=False):
        """Find all the media recursively inside the root directory.
        This will not clobber existing records but will add any new ones.
        """
        media = self.media
        new_media = {}
        self._setup_root()
        default_tags = dict((ti.name, ti.default) for ti in self.tags)

        def _scan(dir):
            for f in dir.files:
                m = media.get(f.relpath)
                if m is None:
                    m = self._create_media(f, default_tags)
                    new_media[f.relpath] = m
                if refresh:
                    m.update()
            for d in dir.directories:
                if refresh:
                    d.refresh()
                _scan(d)

        if refresh:
            self.root.refresh()
        _scan(self.root)

        if len(new_media) > 0:
            # This is done because if media is changed, a trait change notify
            # will be sent to listeners with a very large amount of data
            # potentially.  The jigna webserver will marshal all the keys
            # and not be able to send the information.
            media_copy = dict(media)
            media_copy.update(new_media)
            self.trait_setq(media=media_copy)
            self.number_of_files = len(self.media)

    def search(self, q):
        """A generator which yields the (filename, relpath) for each file
        satisfying the search query.
        """
        logger.info('Searching for %s', q)
        try:
            parsed_q = self._query_parser.parse(q)
        except Exception:
            logger.warn("Invalid search expression: %s", q)
            print("Invalid search expression: %s" % q)
            return
        tag_types = self._get_tag_types()
        _cleanup_query(parsed_q, tag_types)
        for key in self.media:
            m = self.media[key]
            if _search_media(parsed_q, m):
                yield basename(key), key

    def refresh(self):
        logger.info('Refreshing project: %s', self.name)
        self.scan(refresh=True)

    # #### Private protocol ################################################

    def _create_media(self, f, default_tags):
        m = Media.from_path(f.path, f.relpath)
        m.tags = dict(default_tags)
        return m

    def _setup_root(self):
        path = abspath(expanduser(self.path))
        root = self.root
        if root is None or realpath(root.path) != realpath(path):
            self.root = Directory(path=path, extensions=self.extensions)

    def _tags_default(self):
        return [TagInfo(name='completed', type='bool')]

    def _save_file_default(self):
        if len(self.name) > 0:
            fname = sanitize_name(self.name) + '.vxn'
            d = get_project_dir()
            return get_non_existing_filename(join(d, fname))
        else:
            return ''

    def _update_last_save_time(self):
        self.last_save_time = get_file_saved_time(self.save_file)

    def _last_save_time_default(self):
        if exists(self.save_file):
            return get_file_saved_time(self.save_file)

    def _name_changed(self, name):
        if len(name) > 0:
            old_save_file = self.save_file
            old_dir = dirname(old_save_file)
            new_save_file = join(old_dir, sanitize_name(name) + '.vxn')
            if new_save_file != old_save_file:
                self.save_file = new_save_file
                if exists(old_save_file):
                    shutil.move(old_save_file, self.save_file)

    def _extensions_changed(self, ext):
        if self.root is not None:
            self.root.extensions = ext

    def _extensions_items_changed(self):
        if self.root is not None:
            self.root.extensions = self.extensions

    def _get_tag_types(self):
        result = dict(COMMON_TAGS)
        result.update(dict((t.name, t.type) for t in self.tags))
        return result

    def _make_schema(self):
        from whoosh.fields import BOOLEAN, DATETIME, TEXT, Schema
        kw = dict(
            type=TEXT, file_name=TEXT, path=TEXT,
            mtime=DATETIME, ctime=DATETIME, size=INT
        )
        type_to_field = dict(
            string=TEXT, int=INT, float=FLOAT, bool=BOOLEAN
        )
        for tag in self.tags:
            kw[tag.name] = type_to_field[tag.type]

        return Schema(**kw)

    def _make_query_parser(self):
        schema = self._make_schema()
        qp = qparser.QueryParser('path', schema=schema)
        qp.add_plugin(qparser.GtLtPlugin())
        from whoosh.qparser.dateparse import DateParserPlugin
        qp.add_plugin(DateParserPlugin())
        return qp

    def __query_parser_default(self):
        return self._make_query_parser()
