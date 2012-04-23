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

    def test_get_filters(self):
        self.assertDictEqual(Item.objects._get_filters(
            dict(slug__in=['foo', 'bar'], tag='baz')),
            {'slug': {'$in': ['foo', 'bar']}, 'tag': 'baz'})

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

