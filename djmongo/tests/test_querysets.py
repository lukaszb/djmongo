from djmongo.test import TestCase
from djmongo.querysets import QuerySet
from djmongo.document import Document


class Item(Document):
    class Meta:
        using = 'mongodb'


class TestQuerySet(TestCase):

    def setUp(self):
        for x in range(1, 31):
            Item.objects.create(data={
                'id': x,
                'number': x % 10,
            })

    def test_count(self):
        queryset = QuerySet(Item)
        self.assertEqual(queryset.count(), 30)

    def test_pluck(self):
        queryset = QuerySet(Item)

        expected = range(1, 31)
        self.assertItemsEqual(queryset.pluck('id'), expected)

        expected = range(10) * 3
        self.assertItemsEqual(queryset.pluck('number'), expected)

    def test_filter(self):
        queryset = QuerySet(Item)

        self.assertItemsEqual(queryset.filter(id=10).pluck('id'), [10])
        self.assertItemsEqual(queryset.filter(number=0, id=10).pluck('id'), [10])

    def test_filter_in(self):
        queryset = QuerySet(Item)
        self.assertItemsEqual(queryset.filter(id__in=[1, 3, 20, 40]).pluck('id'),
            [1, 3, 20])

    def test_filter_span_another_queryset_with_previouse_filters(self):
        queryset = QuerySet(Item)

        queryset2 = queryset.filter(ch='a')
        self.assertEqual(queryset2.get_filters(), {'ch': 'a'})

        queryset3 = queryset2.filter(number=2)
        self.assertEqual(queryset3.get_filters(), {'ch': 'a', 'number': 2})

    def test_filter_span(self):
        queryset = QuerySet(Item)
        Item.objects.collection.drop()
        Item.objects.create(data=dict(id=101, ch='a', number=1))
        Item.objects.create(data=dict(id=102, ch='a', number=1))
        Item.objects.create(data=dict(id=103, ch='a', number=2))
        Item.objects.create(data=dict(id=104, ch='b', number=1))
        Item.objects.create(data=dict(id=105, ch='b', number=2))

        self.assertItemsEqual(
            queryset.filter(number=1).filter(ch='a').pluck('id'),
            [101, 102])
        self.assertItemsEqual(
            queryset.filter(number=2).filter(ch='b').pluck('id'),
            [105])

    def test_order_by(self):
        queryset = QuerySet(Item)
        self.assertEquals(list(queryset.order_by('id').pluck('id')), range(1, 31))

    def test_order_by_reversed(self):
        queryset = QuerySet(Item)
        self.assertEquals(list(queryset.order_by('-id').pluck('id')), range(30, 0, -1))

    def test_slice_start(self):
        queryset = QuerySet(Item).order_by('id')
        self.assertEqual(list(queryset[28:].pluck('id')), [29, 30])

    def test_slice_end(self):
        queryset = QuerySet(Item).order_by('id')
        self.assertEqual(list(queryset[:5].pluck('id')), [1, 2, 3, 4, 5])

    def test_slice(self):
        queryset = QuerySet(Item).order_by('id')
        self.assertEqual(list(queryset[11:15].pluck('id')), [12, 13, 14, 15])

    def test_index(self):
        item = QuerySet(Item).order_by('id')[0]
        self.assertEqual(item.data['id'], 1)

    def test_index_raises_type_error(self):
        with self.assertRaises(TypeError):
            QuerySet(Item)['string']

    def test_iteration(self):
        items = list(QuerySet(Item).order_by('id')[:2])
        item1, item2 = items
        self.assertIsInstance(item1, Item)
        self.assertEqual(item1.data['id'], 1)
        self.assertIsInstance(item2, Item)
        self.assertEqual(item2.data['id'], 2)

