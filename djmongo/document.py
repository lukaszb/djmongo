import pymongo
from django.db import connections
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from djmongo.utils import is_mongodb_connection
from djmongo.exceptions import DjongoError
from djmongo.querysets import QuerySet


class Index(object):
    ASCENDING = pymongo.ASCENDING
    DESCENDING = pymongo.DESCENDING

    __slots__ = ('keys', 'unique', 'name')

    def __init__(self, keys, unique=False, name=None):
        if isinstance(keys, basestring):
            keys = [(keys, Index.ASCENDING)]
        self.keys = set(keys)
        self.unique = unique
        self.name = name

    def __eq__(self, other):
        return self.keys == other.keys and self.unique == other.unique

    def __cmp__(self, other):
        return cmp(repr(self), repr(other))

    def __repr__(self):
        result = '<Index: {keys}'.format(keys=self.descriptive_keys())
        if self.unique:
            result += ' | UNIQUE'
        result += '>'
        return result

    def descriptive_keys(self):
        """
        Returns keys representation.
        """
        return [(unicode(key), order == Index.ASCENDING and 'Ascending' or 'Descending')
                for key, order in sorted(self.keys)]

    def create_for_collection(self, collection):
        collection.create_index(list(self.keys), unique=self.unique)


class Manager(object):
    document = None

    def __init__(self):
        pass

    def get_query_set(self):
        return QuerySet(self.document)

    @property
    def connection(self):
        conn = connections[self.document._meta.using]
        if not is_mongodb_connection(conn):
            raise ImproperlyConfigured("Must be used with mongodb backend "
                "(got %r)" % conn)
        return conn

    @property
    def db(self):
        return self.connection.db

    def _get_collection(self):
        return getattr(self.db, self.document._meta.collection_name)

    @property
    def collection(self):
        return self._get_collection()

    def count(self, **filters):
        return self.filter(**filters).count()

    def create(self, **kwargs):
        document = self.document(**kwargs)
        document.save()
        return document

    def get_indexes(self):
        return [Index(keys=index['key'], unique=index.get('unique', False), name=name)
                for name, index in self.collection.index_information().items()]

    def all(self):
        return self.get_query_set().all()

    def filter(self, **filters):
        return self.get_query_set().filter(**filters)

    def get(self, **filters):
        return self.get_query_set().get(**filters)

    def pluck(self, *fields, **filters):
        return self.filter(**filters).pluck(*fields)

    def upsert(self, data, safe=True, **filters):
        result = self.collection.update(filters, data, upsert=True, safe=safe)
        if safe:
            data['_id'] = result.get('upserted')
        return self.document(data=data)


META_KEYS = ['using', 'collection_name', 'indexes', 'verbose_name',
    'verbose_name_plural']

class Options(object):

    @classmethod
    def defaults(cls, Document):
        return {
            'app_label': None,
            'using': None,
            'collection_name': Document.__name__.lower(),
            'verbose_name': Document.__name__,
            'indexes': [],
        }

    @classmethod
    def for_class(cls, Document, extra_opts=None):
        opts = cls()
        for attr, value in cls.defaults(Document).items():
            setattr(opts, attr, value)

        for key in META_KEYS:
            if hasattr(extra_opts, key):
                setattr(opts, key, getattr(extra_opts, key))

        # Update verbose_name_plural
        if not hasattr(opts, 'verbose_name_plural'):
            opts.verbose_name_plural = opts.verbose_name + 's'

        # Calculate app_label
        modname = Document.__module__
        while modname:
            if modname in settings.INSTALLED_APPS:
                opts.app_label = modname.split('.')[-1]
                break
            modname = '.'.join(modname.split('.')[:-1])

        opts.module_name = Document.__name__.lower().replace('_', '')
        opts.object_name = Document.__name__

        return opts


class DocumentBase(type):

    def __new__(cls, name, bases, attrs):
        opts = attrs.pop('Meta', object())
        manager = attrs['_default_manager'] = Manager()
        if 'objects' not in attrs:
            attrs['objects'] = manager
        new_class = super(DocumentBase, cls).__new__(cls, name, bases, attrs)
        manager.document = attrs['objects'].document = new_class
        new_class._meta = Options.for_class(new_class, opts)
        if new_class.auto_ensure_indexes:
            new_class.ensure_indexes()
        return new_class


class Document(object):
    __metaclass__ = DocumentBase

    auto_ensure_indexes = True

    def __init__(self, data=None):
        self.data = data or {}

    def __eq__(self, other):
        if self.id is not None:
            return self.id == other.id
        return self.data == other.data

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self.data)

    @property
    def id(self):
        return self.data.get('_id')

    def save(self, safe=True):
        if not self.id:
            self.data[u'_id'] = self.objects.collection.insert(self.data,
                safe=safe)
        else:
            update_data = self.data.copy()
            del update_data['_id']
            self.objects.collection.update({'_id': self.id},
                {'$set': update_data}, safe=safe)
        return self

    @property
    def pk(self):
        return self.id

    @classmethod
    def ensure_indexes(cls):
        for index in cls._meta.indexes:
            index.create_for_collection(cls.objects.collection)

    class DoesNotExist(DjongoError):
        pass

