from mock import patch
from mock import Mock
from django.core.exceptions import ImproperlyConfigured
from djmongo.compat import unittest
from djmongo.document import Document
from djmongo.test import TestCase
from djmongo.backend.mongodb.base import DatabaseWrapper
from djmongo.backend.mongodb.base import FakeCursor
from django.db import connections
import pymongo


HOST = 'localhost'
PORT = 27017

def has_local_db():
    try:
        pymongo.Connection(host=HOST, port=PORT)
        return True
    except pymongo.errors.AutoReconnect:
        return False

class MyDocument(Document):

    class Meta:
        using = 'mongodb'


class TestFakeCursor(TestCase):

    def test_execute(self):
        cursor = FakeCursor()
        self.assertIsNone(cursor.execute())
        self.assertIsNone(cursor.execute(1, 2, foo='bar'))

@unittest.skipIf(not has_local_db(), "There is no local mongodb instance to test")
@patch('djmongo.backend.mongodb.base.ConnectionWrapper')
class TestDatabaseWrapper(TestCase):

    def setUp(self):
        self.conn = DatabaseWrapper({
            'NAME': 'foobar',
            'HOST': 'localhost',
            'PORT': PORT,
        })

    def test_cursor(self, *args):
        self.assertIsInstance(self.conn.cursor(), FakeCursor)

    def test_get_test_db_name(self, *args):
        self.conn.settings_dict['TEST_NAME'] = 'test_foobar'
        self.assertEqual(self.conn.get_test_db_name(), 'test_foobar')

    def test_missing_NAME(self, *args):
        with self.assertRaises(ImproperlyConfigured):
            DatabaseWrapper({
                'HOST': 'localhost',
                'PORT': PORT,
            })

    @patch('djmongo.backend.mongodb.base.django')
    def test_django_13_ops(self, django_mock, cw_mock):
        django_mock.VERSION = (1, 3)
        with patch('djmongo.backend.mongodb.base.DatabaseOperations') as m:
            DatabaseWrapper({
                'NAME': 'foobar',
                'HOST': 'localhost',
                'PORT': PORT,
            })
            m.assert_called_once_with()

    @patch('djmongo.backend.mongodb.base.django')
    def test_django_14_ops(self, django_mock, cw_mock):
        django_mock.VERSION = (1, 5)
        with patch('djmongo.backend.mongodb.base.DatabaseOperations') as m:
            db = DatabaseWrapper({
                'NAME': 'foobar',
                'HOST': 'localhost',
                'PORT': PORT,
            })
            m.assert_called_once_with(db)

    def test_introspection_get_table_list(self, cw_mock):
        self.assertEqual(self.conn.introspection.get_table_list(FakeCursor()),
            [])

    def test_ops_quote_name(self, cw_mock):
        self.assertEqual(self.conn.ops.quote_name('foo'), repr('foo'))

    def test_ops_sql_flush(self, cw_mock):
        self.assertEqual(self.conn.ops.sql_flush(), [])

    def test_connection_commit(self, cw_mock):
        self.assertIsNone(self.conn.connection.commit())

    def test_connection_rollback(self, cw_mock):
        self.assertIsNone(self.conn.connection.rollback())

    def test_get_connection_uri(self, cw_mock):
        self.conn.settings_dict = {
            'HOST': 'example.com',
            'PORT': 101,
            'USER': 'foo',
            'PASSWORD': 'bar',
            'NAME': 'testdb',
        }
        self.assertEqual(self.conn.get_connection_uri(),
            'mongodb://foo:bar@example.com:101/testdb')

    def test_get_connection_uri_without_user_password(self, cw_mock):
        self.conn.settings_dict = {
            'HOST': 'example.com',
            'PORT': 101,
            'NAME': 'testdb',
        }
        self.assertEqual(self.conn.get_connection_uri(),
            'example.com:101')

    def test_creation_drop_database(self, cw_mock):
        creation = self.conn.creation
        creation.connection = Mock()
        creation.drop_database('foo')
        creation.connection.get_connection().drop_database.assert_called_with('foo')


class TestObjectsDoNotLeakBetweenTests(TestCase):

    def test_1(self):
        MyDocument.objects.create(data={'foo': 'bar'})
        MyDocument.objects.create(data={'foo': 'baz'})

        self.assertEqual(MyDocument.objects.count(), 2)

    def test_2(self):
        MyDocument.objects.create(data={'foo': 'bar'})
        MyDocument.objects.create(data={'foo': 'baz'})

        self.assertEqual(MyDocument.objects.count(), 2)

    def test_clear_all_collections(self):
        conn = connections['mongodb']
        conn.db.testitems.insert({})
        conn.db.testitems2.insert({})

        col_count = conn.collections_count()
        conn.clear_all_collections()

        self.assertEqual(conn.collections_count(), col_count - 2)


class TestObjectsAreCreatedDuringSetUp(TestCase):

    def setUp(self):
        MyDocument.objects.create(data={'foo': 'bar1'})
        MyDocument.objects.create(data={'foo': 'bar2'})
        MyDocument.objects.create(data={'foo': 'bar3'})

    def test_count(self):
        self.assertEqual(MyDocument.objects.count(), 3)


class TestOverrideCanDropCollectionTestCase(TestCase):

    collections_prefix = 'testfoo.'

    def can_drop_collection(self, collection_name, connection):
        return collection_name.startswith(self.collections_prefix)

    def setUp(self):
        self.conn = connections['mongodb']

    def test_post_teardown(self):
        self.conn.db.testfoo.items1.insert({})
        self.conn.db.testfoo.items2.insert({})
        self.conn.db.anothertest.items.insert({})

        self.post_teardown()
        # by now our testfoo.items1 and testfoo.items2 should be dropped
        self.assertEqual(self.conn.db.testfoo.items1.count(), 0)
        self.assertEqual(self.conn.db.testfoo.items2.count(), 0)
        self.assertEqual(self.conn.db.anothertest.items.count(), 1)


class TestDjmongoTestCase(TestCase):

    def setUp(self):
        self.conn = connections['mongodb']

    def test_that_we_use_test_name(self):
        self.assertEqual(self.conn.db.name, 'test_testdb')

