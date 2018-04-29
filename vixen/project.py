import datetime
import io
import json_tricks
import logging
import os
from os.path import (abspath, basename, dirname, exists, expanduser,
                     join, realpath, relpath, splitext)
import re
import shutil
import sys

from traits.api import (Any, Dict, Enum, HasTraits, Instance, List, Long,
                        Str)
from whoosh import fields, qparser, query
from whoosh.util.times import datetime_to_long, long_to_datetime

from .common import get_project_dir
from .media import Media, MediaData, get_media_data
from .directory import Directory
from . import processor


logger = logging.getLogger(__name__)

if sys.version_info[0] > 2:
    unicode = str
    string_types = (str,)
    import csv
else:
    string_types = (basestring,)
    import backports.csv as csv
INT = fields.NUMERIC(numtype=int)
FLOAT = fields.NUMERIC(numtype=float)


def get_file_saved_time(path):
    dt = datetime.datetime.fromtimestamp(os.stat(path).st_ctime)
    return dt.ctime()


def _get_sample(fname):
    sample = ''
    with io.open(fname, 'r', newline='', encoding='utf-8') as fp:
        sample += fp.readline() + fp.readline()

    return sample


def _get_csv_headers(fname):
    sample = _get_sample(fname)
    sniffer = csv.Sniffer()
    has_header = sniffer.has_header(sample)
    dialect = sniffer.sniff(sample)
    with io.open(fname, 'r', newline='', encoding='utf-8') as fp:
        reader = csv.reader(fp, dialect)
        header = next(reader)
    return has_header, header, dialect


class TagInfo(HasTraits):
    name = Str
    type = Enum("string", "text", "int", "float", "bool")
    default = Any

    def __repr__(self):
        return 'TagInfo(%r, %r)' % (self.name, self.type)

    def _default_default(self):
        map = {"string": "", "text": "", "int": 0, "float": 0.0,
               "bool": False}
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
    file_name='string', path='string', relpath='string',
    ctime='string', mtime='string', size='int', type='string'
)


def _cleanup_query(q, tag_types):
    type_map = dict(float=FLOAT.from_bytes, int=INT.from_bytes)
    for term in q.leaves():
        if isinstance(term, query.Term):
            if isinstance(term.text, (str, unicode, bytes)):
                fieldtype = tag_types[term.fieldname]
                if fieldtype in type_map:
                    term.text = type_map[fieldtype](term.text)
                else:
                    term.text = term.text.lower()
        elif isinstance(term, query.Phrase):
            term.words = [x.lower() for x in term.words]


def _check_value(value, expr):
    if isinstance(expr, string_types):
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
        result &= x >= term.start
    if term.enddate is not None and result:
        result &= x <= term.end
    return result


def _search_media(expr, m_key, get_tag):
    """Given search expression, index to media, and a getter to get the attribute
    check if the media matches expression.
    """
    if expr.is_leaf():
        if isinstance(expr, query.Term):
            attr = expr.fieldname
            return _check_value(get_tag(m_key, attr), expr.text)
        elif isinstance(expr, query.Phrase):
            attr = expr.fieldname
            text = " ".join(expr.words)
            return _check_value(get_tag(m_key, attr), text)
        elif isinstance(expr, query.DateRange):
            if expr.fieldname == 'ctime':
                value = get_tag(m_key, 'ctime_')
            elif expr.fieldname == 'mtime':
                value = get_tag(m_key, 'mtime_')
            return _check_date_range(value, expr)
        elif isinstance(expr, query.NumericRange):
            attr = expr.fieldname
            return _check_range(get_tag(m_key, attr), expr)
        else:
            print("Unsupported term: %r" % expr)
            return False
    else:
        if isinstance(expr, query.And):
            result = True
            for child in expr.children():
                result &= _search_media(child, m_key, get_tag)
                if not result:
                    break
            return result
        elif isinstance(expr, query.Or):
            result = False
            for child in expr.children():
                result |= _search_media(child, m_key, get_tag)
                if result:
                    break
            return result
        elif isinstance(expr, query.Not):
            subquery = list(expr.children())[0]
            return not _search_media(subquery, m_key, get_tag)
        else:
            print("Unsupported term: %r" % expr)
            return False


class Project(HasTraits):
    name = Str
    description = Str
    path = Str
    root = Instance(Directory)
    tags = List(TagInfo)

    _media = Dict(Str, Media)

    extensions = List(Str)

    processors = List(processor.FactoryBase)

    number_of_files = Long

    # Path where the project data is saved.
    save_file = Str

    last_save_time = Str

    _data = Dict

    _tag_data = Dict

    _relpath2index = Dict()

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

        for tag in removed:
            del self._tag_data[tag.name]

        n_entries = len(self._relpath2index)
        for tag in added:
            self._tag_data[tag.name] = [tag.default]*n_entries

        # The above can be the first time when self._tag_data is accessed, when
        # creating a new project for example. In this case,
        # self.__tag_data_default is called, so if self.tags is set then the
        # removed tags will not exist in _tag_data causing an error. So we only
        # set self.tags below.
        self.tags = new_tags

        # Update the cached media
        for m in self._media.values():
            for tag in removed:
                del m.tags[tag.name]
            for tag in added:
                m.tags[tag.name] = tag.default

        self._query_parser = self._make_query_parser()

    def copy(self):
        """Make a copy of this project. This does not copy the data but only
        the tags, extensions and the other settings of the project.

        This will not copy any of the processor states but only their settings.

        """
        name = self.name + ' copy'
        p = Project(name=name)
        traits = ['description', 'extensions', 'path', 'processors', 'tags']
        p.copy_traits(self, traits, copy='deep')
        # Clear out the _done information from the processors
        for proc in p.processors:
            proc._done.clear()
        return p

    # ####  CRUD interface to the data ####

    def update(self, media_data, tags=None):
        """Create/update the internal data given the media data and tags.

        Parameters
        ----------

        f: vixen.directory.File instance
        tags: dict
        """
        relpath = media_data.relpath
        if not self.has_media(relpath):
            index = len(self._relpath2index)
            self._relpath2index[relpath] = index
            for key in MediaData._fields:
                self._data[key].append(None)
            for tag in self.tags:
                self._tag_data[tag.name].append(tag.default)

        index = self._relpath2index[relpath]
        for i, key in enumerate(MediaData._fields):
            self._data[key][index] = media_data[i]
        if tags:
            for key, value in tags.items():
                self._tag_data[key][index] = value
        media = self._media.get(relpath)
        if media is not None:
            media.update(media_data, tags)

    def get(self, relpath):
        """Given the relative path of some media, return a Media instance.
        """
        if relpath in self._media:
            return self._media[relpath]
        else:
            data = {}
            index = self._relpath2index[relpath]
            for key in MediaData._fields:
                data[key] = self._data[key][index]
            tags = {}
            for key in self._tag_data:
                tags[key] = self._tag_data[key][index]

            media = Media.from_data(MediaData(**data), tags)
            media.on_trait_change(self._media_tag_handler, 'tags_items')
            self._media[relpath] = media
            return media

    def remove(self, relpaths):
        """Given a list of relative path of some media, remove them from the
        database.
        """
        relpath2index = self._relpath2index
        indices = [(x, relpath2index[x]) for x in relpaths]
        for relpath, index in sorted(indices, reverse=True):
            last = len(relpath2index) - 1
            if index == last:
                self._delete_record(last, relpath)
            else:
                self._replace_with_last_record(index, last)
                self._delete_record(last, relpath)

    def has_media(self, relpath):
        """Returns True if the media data is available.
        """
        return relpath in self._relpath2index

    def keys(self):
        """Return all the keys for the media relative paths."""
        return self._relpath2index.keys()

    def _get_media_attr(self, index, attr):
        """Given an index to the media, return its value.
        """
        if attr in self._data:
            return self._data[attr][index]
        elif attr in self._tag_data:
            return self._tag_data[attr][index]

    # ####  End of CRUD interface to the data ####

    def clean(self):
        """Scan the project and remove any dead entries.

        This is useful when you remove or rename files. This does not refresh
        the directory tree or set the number of files. It simply cleans up the
        db of files that no longer exist.
        """
        logger.info('Cleaning project: %s', self.name)
        root_path = self.path
        to_remove = []
        relpath2index = self._relpath2index
        for rpath in list(relpath2index.keys()):
            fname = os.path.join(root_path, rpath)
            if not os.path.exists(fname):
                to_remove.append(rpath)
        self.remove(to_remove)

    def export_csv(self, fname, cols=None):
        """Export metadata to a csv file.  If `cols` are not specified,
        it writes out all the useful metadata.

        Parameters
        -----------

        fname: str: a path to the csv file to dump.
        cols: sequence: a sequence of columns to write.
        """
        logger.info('Exporting CSV: %s', fname)
        all_keys = ((set(MediaData._fields) | set(self._tag_data.keys()))
                    - set(('ctime_', 'mtime_')))
        if cols is None:
            cols = all_keys
            cols = list(sorted(cols))

        data_cols = set([x for x in cols if x in self._data])

        with io.open(fname, 'w', newline='', encoding='utf-8') as of:
            # Write the header.
            writer = csv.writer(of)
            writer.writerow(cols)
            for i in range(len(self._relpath2index)):
                line = []
                for col in cols:
                    if col in data_cols:
                        elem = self._data[col][i]
                    else:
                        elem = self._tag_data[col][i]
                    line.append(elem)
                writer.writerow(line)

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
            'text': lambda x: x,
            'int': int,
            'float': float
        }

        count = 0
        total = 0
        with io.open(fname, 'r', newline='', encoding='utf-8') as fp:
            reader = csv.reader(fp, dialect)
            next(reader)  # Skip header
            for record in reader:
                total += 1
                path = record[path_idx]
                rpath = relpath(path, self.path)
                index = self._relpath2index.get(rpath, None)
                media = self._media.get(rpath)
                if index is not None:
                    count += 1
                    for tag, header_index in tags.items():
                        data = record[header_index]
                        try:
                            value = type_map[tag.type](data)
                            if media is not None:
                                media.tags[tag.name] = value
                            else:
                                self._tag_data[tag.name][index] = value
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
        version = data.get('version')
        if version == 1:
            self._read_version1_media(data['media'])
        else:
            self._data = data['media_data']
            self._tag_data = data['tag_data']
            self._relpath2index = data['relpath2index']
        root = Directory()
        root.__setstate__(data.get('root'))
        self.extensions = root.extensions
        self.root = root
        self.number_of_files = len(self._relpath2index)

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
        tags = [(t.name, t.type) for t in self.tags]
        root = self.root.__getstate__()
        processors = [processor.dump(x) for x in self.processors]
        data = dict(
            version=2, path=self.path, name=self.name,
            description=self.description, tags=tags,
            media_data=self._data, tag_data=self._tag_data,
            relpath2index=self._relpath2index,
            root=root, processors=processors
        )
        json_tricks.dump(data, fp, compression=True)
        fp.close()
        logger.info('Saved project: %s', self.name)

    def scan(self, refresh=False):
        """Find all the media recursively inside the root directory.
        This will not clobber existing records but will add any new ones.
        """
        self._setup_root()

        def _scan(dir):
            for f in dir.files:
                if not self.has_media(f.relpath) or refresh:
                    data = get_media_data(f.path, f.relpath)
                    self.update(data)
            for d in dir.directories:
                if refresh:
                    d.refresh()
                _scan(d)

        if refresh:
            self.root.refresh()
        _scan(self.root)

        self.number_of_files = len(self._relpath2index)

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
        for key, index in self._relpath2index.items():
            if _search_media(parsed_q, index, self._get_media_attr):
                yield basename(key), key

    def refresh(self):
        logger.info('Refreshing project: %s', self.name)
        self.clean()
        self.scan(refresh=True)

    # #### Private protocol ################################################

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
        else:
            return ''

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
            string=TEXT, text=TEXT, int=INT, float=FLOAT, bool=BOOLEAN
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

    def __data_default(self):
        data = {}
        for key in MediaData._fields:
            data[key] = []
        return data

    def __tag_data_default(self):
        tags = {}
        for key in self.tags:
            tags[key.name] = []
        return tags

    def _media_tag_handler(self, obj, tname, old, new):
        index = self._relpath2index[obj.relpath]
        for tag in new.changed:
            self._tag_data[tag][index] = obj.tags[tag]

    def _read_version1_media(self, media):
        data = self.__data_default()
        tag_data = self.__tag_data_default()
        relpath2index = {}
        keymap = dict.fromkeys(MediaData._fields)
        for k in keymap:
            keymap[k] = k
        keymap['_ctime'] = 'ctime_'
        keymap['_mtime'] = 'mtime_'

        for index, (key, m) in enumerate(media):
            relpath2index[key] = index
            tags = m.pop('tags')
            for tname, v in tags.items():
                tag_data[tname].append(v)
            for k, v in m.items():
                data[keymap[k]].append(v)
            if 'file_name' not in m:
                data['file_name'].append(basename(key))

        data['mtime_'] = [datetime_to_long(x) for x in data['mtime_']]
        data['ctime_'] = [datetime_to_long(x) for x in data['ctime_']]
        self._data = data
        self._tag_data = tag_data
        self._relpath2index = relpath2index

    def _delete_record(self, index, relpath):
        for key in MediaData._fields:
            del self._data[key][index]
        for key in self._tag_data:
            del self._tag_data[key][index]
        if relpath in self._media:
            del self._media[relpath]
        del self._relpath2index[relpath]

    def _replace_with_last_record(self, index, last):
        _data = self._data
        _tag_data = self._tag_data
        for key in MediaData._fields:
            _data[key][index] = _data[key][last]
        for key in self._tag_data:
            _tag_data[key][index] = _tag_data[key][last]
        last_relpath = _data['relpath'][last]
        self._relpath2index[last_relpath] = index

    def _save_as_v1(self, fp):
        """Save copy to specified path.

        This mainly exists for testing and making sure we still read the old
        saved files.
        """
        def _rewrite_dir(state):
            "Rewrite directories in the old format."
            state['files'] = [x[0] for x in state['files']]
            state['directories'] = [_rewrite_dir(d)
                                    for d in state['directories']]
            state.pop('relpath')
            state.pop('name')
            return state

        fp = open_file(fp, 'wb')
        media = [(key, self.get(key).to_dict()) for key in self._relpath2index]
        tags = [(t.name, t.type) for t in self.tags]
        root = _rewrite_dir(self.root.__getstate__())
        processors = [processor.dump(x) for x in self.processors]
        for k, m in media:
            m['_ctime'] = long_to_datetime(m['_ctime'])
            m['_mtime'] = long_to_datetime(m['_mtime'])
        data = dict(
            version=1, path=self.path, name=self.name,
            description=self.description, tags=tags, media=media,
            root=root, processors=processors
        )
        json_tricks.dump(data, fp, compression=True)
        fp.close()
        logger.info('Saved project: %s', self.name)
