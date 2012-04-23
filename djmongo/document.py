import pymongo
from django.db import connections
from django.core.exceptions import ImproperlyConfigured
from djmongo.utils import is_mongodb_connection
from djmongo.exceptions import MultipleItemsReturnedError
from djmongo.exceptions import DjongoError


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
        return self.collection.find(filters).count()

    def create(self, **kwargs):
        document = self.document(**kwargs)
        document.save()
        return document

    def get_indexes(self):
        return [Index(keys=index['key'], unique=index.get('unique', False), name=name)
                for name, index in self.collection.index_information().items()]

    def all(self):
        for data in self.collection.find():
            yield self.document(data=data)

    def _get_filters(self, filters):
        new_filters = filters.copy()
        for key in (k for k in new_filters if '__' in k):
            field, operator = key.split('__', 1)
            if operator in ['in']:
                new_filters[field] = {'$' + operator: list(new_filters.pop(key))}
        return new_filters

    def filter(self, **filters):
        filters = self._get_filters(filters)
        for item in self.collection.find(filters):
            yield self.document(data=item)

    def get(self, **filters):
        result = None
        for item in self.collection.find(filters):
            if result is not None:
                raise MultipleItemsReturnedError("More than one item found "
                    "for filters: %r" % filters)
            else:
                result = item
        if result is None:
            raise self.document.DoesNotExistError("No item found for filters: %r"
                % filters)
        return self.document(data=result)

    def pluck(self, *fields, **filters):
        for doc in self.filter(**filters):
            if len(fields) == 1:
                yield doc.data.get(fields[0])
            else:
                yield tuple(doc.data.get(field) for field in fields)

    def upsert(self, data, safe=True, **filters):
        self.collection.update(filters, data, upsert=True, safe=safe)


META_KEYS = ['using', 'collection_name', 'indexes']

class Options(object):

    @classmethod
    def defaults(cls, Document):
        return {
            'using': None,
            'collection_name': Document.__name__.lower(),
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


        return opts


class DocumentBase(type):

    def __new__(cls, name, bases, attrs):
        opts = attrs.pop('Meta', object())
        manager = Manager()
        attrs['objects'] = manager
        new_class = super(DocumentBase, cls).__new__(cls, name, bases, attrs)
        manager.document = new_class
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

    @classmethod
    def ensure_indexes(cls):
        for index in cls._meta.indexes:
            index.create_for_collection(cls.objects.collection)

    class DoesNotExistError(DjongoError):
        pass

