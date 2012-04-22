from django.db import connections
from django.core.exceptions import ImproperlyConfigured


class Manager(object):

    def __init__(self):
        pass

    @property
    def connection(self):
        conn = connections[self.document._meta.using]
        return conn

    @property
    def db(self):
        return self.connection.db

    @property
    def collection(self):
        return getattr(self.db, self.document._meta.collection_name)

    def count(self):
        return self.collection.count()


META_KEYS = ['using', 'collection_name']

class Options(object):
    using = 'mongodb'

    @classmethod
    def for_class(cls, Document, extra_opts=None):
        opts = cls()
        opts.collection_name = Document.__name__.lower()
        if not isinstance(extra_opts, dict):
            extra_opts = dict((key, getattr(extra_opts, key, None)) for key in META_KEYS)
        opts.update(**extra_opts)

        #opts.setup_using()

        return opts

    def update(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

    def setup_using(self):
        conn = connections[self.using]
        if conn.vendor != 'mongodb':
            #raise ImproperlyConfigured("using option must be set to mongodb engine")
            #for alias, conn in connec
            pass


class DocumentBase(type):

    def __new__(cls, name, bases, attrs):
        opts = attrs.pop('Meta', {})
        manager = Manager()
        attrs['objects'] = manager
        new_class = super(DocumentBase, cls).__new__(cls, name, bases, attrs)
        manager.document = new_class
        new_class._meta = Options.for_class(new_class, opts)
        return new_class

class Document(object):
    __metaclass__ = DocumentBase

    def __init__(self, data=None):
        self.data = data

    def save(self):
        self.objects.collection.insert(self.data, safe=True)



