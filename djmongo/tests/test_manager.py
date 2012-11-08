from mock import patch
from mock import Mock
from django.core.exceptions import ImproperlyConfigured
from djmongo.test import TestCase
from djmongo.document import Document
from djmongo.document import Manager
from djmongo.exceptions import MultipleItemsReturnedError


class Item(Document):
    class Meta:
        using = 'mongodb'


class TestManager(TestCase):

    def test_raise_error_if_wrong_connection_used(self):
        with patch('djmongo.document.is_mongodb_connection') as m:
            m.return_value = False
            with self.assertRaises(ImproperlyConfigured):
                manager = Manager()
                manager.document = Mock()
                manager.document._meta.using = 'default'
                manager.connection

    def test_all(self):
        item1 = Item.objects.create(data={'foo': 'bar'})
        item2 = Item.objects.create(data={'foo': 'baz'})
        self.assertItemsEqual([item.data for item in Item.objects.all()],
            [item1.data, item2.data])

    def test_get(self):
        item = Item.objects.create(data={'title': 'Slayer'})
        Item.objects.create(data={'title': 'Sabaton'})
        Item.objects.create(data={'title': 'Therion'})
        Item.objects.create(data={'title': 'Pantera'})

        self.assertEqual(Item.objects.get(title='Slayer'), item)

    def test_get_raises_multiple_items_returned_error(self):
        Item.objects.create(data={'title': 'Slayer'})
        Item.objects.create(data={'title': 'Slayer'})

        with self.assertRaises(MultipleItemsReturnedError):
            Item.objects.get(title='Slayer')

    def test_get_raises_does_not_exist_error(self):
        Item.objects.create(data={'title': 'Sabaton'})
        Item.objects.create(data={'title': 'Therion'})
        Item.objects.create(data={'title': 'Pantera'})

        with self.assertRaises(Item.DoesNotExistError):
            Item.objects.get(title='Slayer')

    def test_filter(self):
        Item.objects.create(data={'title': 'Sabaton'})
        Item.objects.create(data={'title': 'Therion'})
        item = Item.objects.create(data={'title': 'Pantera', 'foo': 'bar'})

        self.assertItemsEqual([item.data for item in Item.objects.filter(
            title='Pantera')], [item.data])

    def test_filter__in(self):
        Item.objects.create(data={'slug': 'slayer'})
        Item.objects.create(data={'slug': 'sabaton'})
        Item.objects.create(data={'slug': 'therion'})

        self.assertItemsEqual([item.data['slug'] for item in
            Item.objects.filter(slug__in=['slayer'])], ['slayer'])
        self.assertItemsEqual([item.data['slug'] for item in
            Item.objects.filter(slug__in=set(['therion']))], ['therion'])

    def test_pluck(self):
        Item.objects.create(data={'title': 'Sabaton', 'id': 1})
        Item.objects.create(data={'title': 'Therion', 'id': 2})
        Item.objects.create(data={'title': 'Pantera', 'id': 3})

        self.assertItemsEqual(Item.objects.pluck('title'),
            ['Sabaton', 'Therion', 'Pantera'])

        self.assertItemsEqual(Item.objects.pluck('id', 'title'),
            [(1, 'Sabaton'), (2, 'Therion'), (3, 'Pantera')])

    def test_upsert(self):
        Item.objects.upsert({'id': 1, 'title': 'Slayer'}, id=1)
        self.assertItemsEqual(Item.objects.pluck('title'), ['Slayer'])
        Item.objects.upsert({'id': 1, 'title': 'Pantera'}, id=1)
        self.assertItemsEqual(Item.objects.pluck('title'), ['Pantera'])
        Item.objects.upsert({'id': 2, 'title': 'Slayer'}, id=1)
        self.assertItemsEqual(Item.objects.pluck('id', 'title'), [(2, 'Slayer')])

    def test_upsert_returns_a_document(self):
        item = Item.objects.upsert({'id': 1, 'title': 'Slayer'}, id=1)
        self.assertIsInstance(item, Document)
        self.assertIn('_id', item.data)
        del item.data['_id']
        self.assertDictEqual(item.data, {'id': 1, 'title': 'Slayer'})

    def test_upsert_works_even_if_not_marked_as_safe(self):
        data = {'id': 1, 'title': 'Slayer'}
        item = Item.objects.upsert(data, id=1, safe=False)
        self.assertDictEqual(item.data, data)



class CustomManager(Manager):

    def foo(self):
        if not hasattr(self, '_foo_calls'):
            self._foo_calls = 0
        self._foo_calls += 1


class Book(Document):

    class Meta:
        using = 'mongodb'

    objects = CustomManager()


class TestCustomManager(TestCase):

    def test_custom_manager_method_called(self):
        Book.objects.foo()
        Book.objects.foo()
        self.assertEqual(Book.objects._foo_calls, 2)

