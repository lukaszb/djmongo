#from django.conf import settings
import django
import pymongo
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.creation import BaseDatabaseCreation
from django.db.backends import BaseDatabaseFeatures
from django.db.backends import BaseDatabaseIntrospection
from django.db.backends import BaseDatabaseOperations
from django.db.backends import BaseDatabaseWrapper
from djmongo.utils import can_drop_collection


DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 27017


class FakeCursor(object):
    def execute(self, *args, **kwargs):
        pass

class DatabaseFeatures(BaseDatabaseFeatures):
    supports_transactions = True


class DatabaseWrapper(BaseDatabaseWrapper):
    operators = {}
    vendor = 'mongodb'

    def __init__(self, settings_dict, alias=None):
        if not settings_dict.get('NAME'):
            raise ImproperlyConfigured('Missing "NAME" key at mongodb settings '
                'dictionary')
        if not settings_dict.get('TEST_NAME'):
            settings_dict['TEST_NAME'] = 'test_' + settings_dict['NAME']
        super(DatabaseWrapper, self).__init__(settings_dict, alias)
        self.connection = self.get_connection()

        if django.VERSION >= (1, 4):
            self.ops = DatabaseOperations(self)
        else:
            self.ops = DatabaseOperations()

        self.creation = DatabaseCreation(self)
        self.features = DatabaseFeatures(self.connection)
        self.introspection = DatabaseIntrospection(self)

    def cursor(self):
        return FakeCursor()

    def get_test_db_name(self):
        return self.settings_dict['TEST_NAME']

    def get_connection_uri(self):
        uri = 'mongodb://'
        user, password = self.settings_dict.get('USER'), self.settings_dict.get(
            'PASSWORD')
        host = self.settings_dict['HOST'] or DEFAULT_HOST
        port = self.settings_dict['PORT'] or DEFAULT_PORT
        if user and password:
            uri += ':'.join((user, password)) + '@'
        uri += ':'.join((host, str(port)))
        uri = '/'.join((uri, self.settings_dict['NAME']))
        return uri

    def get_connection(self):
        return ConnectionWrapper(host=self.get_connection_uri())

    def get_database(self, database):
        return getattr(self.get_connection(), database)

    @property
    def db(self):
        return self.get_database(self.settings_dict['NAME'])

    def clear_all_collections(self):
        for collection_name in self.db.collection_names():
            if can_drop_collection(collection_name):
                self.db.drop_collection(collection_name)


class DatabaseCreation(BaseDatabaseCreation):
    
    def create_test_db(self, verbosity=1, autoclobber=False):
        """
        Creates a test database, prompting the user for confirmation if the
        database already exists. Returns the name of the test database created.
        """
        test_db_name = self.connection.get_test_db_name()
        # We do not need to create db actually - it is created 'on the fly' by
        # underlying pymongo; Still, by call to collection_names method we
        # ensure that database is created
        self.connection.db.collection_names()

        self.connection.settings_dict['_NAME'] = self.connection.settings_dict['NAME']
        self.connection.settings_dict['NAME'] = test_db_name

    def destroy_test_db(self, old_database_name, verbosity=1):
        """
        Destroy a test database, prompting the user for confirmation if the
        database already exists.
        """
        self.connection.settings_dict['NAME'] = self.connection.settings_dict['_NAME']

    def drop_database(self, database):
        """
        Drops given ``database``.
        """
        self.connection.get_connection().drop_database(database)


class DatabaseIntrospection(BaseDatabaseIntrospection):
    
    def get_table_list(self, cursor):
        return []


class DatabaseOperations(BaseDatabaseOperations):
    def quote_name(self, name):
        return '%r' % name

    def sql_flush(self, *args, **kwargs):
        return []


class ConnectionWrapper(pymongo.Connection):

    def commit(self):
        pass

    def rollback(self):
        pass

