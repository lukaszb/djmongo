#from django.conf import settings
import django
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.creation import BaseDatabaseCreation
from django.db.backends import BaseDatabaseFeatures
from django.db.backends import BaseDatabaseIntrospection
from django.db.backends import BaseDatabaseOperations
from django.db.backends import BaseDatabaseWrapper
from pymongo import Connection


DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 27017


class FakeCursor(object):
    def execute(self, *args, **kwargs):
        pass

class DatabaseWrapper(BaseDatabaseWrapper):
    operators = {}
    autocommit = None
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
        self.features = BaseDatabaseFeatures(self.connection)
        self.introspection = DatabaseIntrospection(self)

    def cursor(self):
        import mock
        return mock.Mock()

    def get_test_db_name(self):
        return self.settings_dict['TEST_NAME']

    def get_connection(self):
        kwargs = {
            'host': self.settings_dict['HOST'] or DEFAULT_HOST,
            'port': int(self.settings_dict['PORT'] or DEFAULT_PORT),
        }
        return ConnectionWrapper(**kwargs)

    def get_database(self, database):
        #return getattr(self.get_connection(), database)
        return getattr(self.get_connection(), database)

    @property
    def db(self):
        return self.get_database(self.settings_dict['NAME'])


class DatabaseCreation(BaseDatabaseCreation):
    
    def create_test_db(self, verbosity=1, autoclobber=False):
        """
        Creates a test database, prompting the user for confirmation if the
        database already exists. Returns the name of the test database created.
        """
        databases = self.connection.connection.database_names()
        test_db_name = self.connection.get_test_db_name()
        if test_db_name in databases:
            if not autoclobber:
                confirm = raw_input(
                    "Type 'yes' if you would like to try deleting the test "
                    "database '%s', or 'no' to cancel: " % test_db_name)
            if autoclobber or confirm:
                if verbosity >= 1:
                    print("Destroying old test database %r" % test_db_name)
                self.drop_database(test_db_name)
        else:
            # We do not need to create db actually - it is created 'on the fly'
            # by underlying pymongo
            #self.connection.db.collection_names()
            pass

        self.connection.settings_dict['_NAME'] = self.connection.settings_dict['NAME']
        self.connection.settings_dict['NAME'] = test_db_name


    def destroy_test_db(self, old_database_name, verbosity=1):
        """
        Destroy a test database, prompting the user for confirmation if the
        database already exists.
        """
        test_db_name = self.connection.get_test_db_name()
        if verbosity >= 1:
            print("Destroying test database %r" % test_db_name)
        self.drop_database(test_db_name)

        self.connection.settings_dict['NAME'] = self.connection.settings_dict['_NAME']

    def drop_database(self, database):
        """
        Drops given ``database``.
        """
        self.connection.get_connection().drop_database(database)


class DatabaseIntrospection(BaseDatabaseIntrospection):
    
    def get_table_list(self, cursor):
        #return self.connection.db.collection_names()
        return []


class DatabaseOperations(BaseDatabaseOperations):
    def quote_name(self, name):
        return '<%s>' % name

    def sql_flush(self, *args, **kwargs):
        # deliberately do nothing as this doesn't apply to us
        #return [True] # pretend that we did something
        return [True]


class ConnectionWrapper(Connection):
    autocommit = None

    def commit(self):
        pass

    def rollback(self):
        pass

