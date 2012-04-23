from mock import patch
from mock import Mock
from django.core.exceptions import ImproperlyConfigured
from djmongo.document import Document
from djmongo.test import TestCase
from djmongo.backend.mongodb.base import DatabaseWrapper
from djmongo.backend.mongodb.base import FakeCursor


class MyDocument(Document):

    class Meta:
        using = 'mongodb'


class TestFakeCursor(TestCase):

    def test_execute(self):
        cursor = FakeCursor()
        self.assertIsNone(cursor.execute())
        self.assertIsNone(cursor.execute(1, 2, foo='bar'))


@patch('djmongo.backend.mongodb.base.ConnectionWrapper')
class TestDatabaseWrapper(TestCase):

    def setUp(self):
        self.conn = DatabaseWrapper({
            'NAME': 'foobar',
            'HOST': 'localhost',
            'PORT': 27017,
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
                'PORT': 27017,
            })

    @patch('djmongo.backend.mongodb.base.django')
    def test_django_13_ops(self, django_mock, cw_mock):
        django_mock.VERSION = (1, 3)
        with patch('djmongo.backend.mongodb.base.DatabaseOperations') as m:
            DatabaseWrapper({
                'NAME': 'foobar',
                'HOST': 'localhost',
                'PORT': 27017,
            })
            m.assert_called_once_with()

    @patch('djmongo.backend.mongodb.base.django')
    def test_django_14_ops(self, django_mock, cw_mock):
        django_mock.VERSION = (1, 5)
        with patch('djmongo.backend.mongodb.base.DatabaseOperations') as m:
            db = DatabaseWrapper({
                'NAME': 'foobar',
                'HOST': 'localhost',
                'PORT': 27017,
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


class TestObjectsAreCreatedDuringSetUp(TestCase):

    def setUp(self):
        MyDocument.objects.create(data={'foo': 'bar1'})
        MyDocument.objects.create(data={'foo': 'bar2'})
        MyDocument.objects.create(data={'foo': 'bar3'})

    def test_count(self):
        self.assertEqual(MyDocument.objects.count(), 3)

