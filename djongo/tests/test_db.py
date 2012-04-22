from django.test import TestCase
from django.db import connections
from djongo.document import Document



class MyDocument(Document):
    using = 'mongodb'


class TestConnection(TestCase):

    def test_(self):
        conn = connections['mongodb']
        print conn


class TestIntrospection(TestCase):
    pass


class TestObjectsDoNotLeakBetweenTests(TestCase):

    def test_1(self):
        document1 = MyDocument(data={'foo': 'bar'})
        document1.save()
        document2 = MyDocument(data={'foo': 'baz'})
        document2.save()

        self.assertEqual(MyDocument.objects.count(), 2)

    def test_2(self):
        document1 = MyDocument(data={'foo': 'bar'})
        document1.save()
        document2 = MyDocument(data={'foo': 'baz'})
        document2.save()

        self.assertEqual(MyDocument.objects.count(), 2)

