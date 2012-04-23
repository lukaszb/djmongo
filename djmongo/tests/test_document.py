from mock import Mock
from djmongo.test import TestCase
from djmongo.document import Document
from djmongo.document import Options
from djmongo.document import Manager
from djmongo.document import Index


class Item(Document):
    class Meta:
        using = 'mongodb'


class TestDocumentClassCreation(TestCase):

    def setUp(self):

        class MyDocument(Document):
            pass

        class AnotherDocument(Document):
            pass

        self.MyDocument = MyDocument
        self.AnotherDocument = AnotherDocument
        
    def test_manager_is_created_for_each_class(self):
        self.assertIsInstance(self.MyDocument.objects, Manager)
        self.assertIsInstance(self.AnotherDocument.objects, Manager)

    def test_manager_is_different_for_each_class(self):
        self.assertNotEqual(self.MyDocument.objects, self.AnotherDocument.objects)

    def test_manager_are_same_across_instances(self):
        doc1 = self.MyDocument()
        doc2 = self.MyDocument()

        self.assertEqual(doc1.objects, doc2.objects)

    def test_manager_points_to_proper_document_class(self):
        self.assertEqual(self.MyDocument.objects.document, self.MyDocument)

    def test_meta_has_proper_collection_name(self):
        self.assertEqual(self.MyDocument._meta.collection_name, 'mydocument')

        class SomeDocument(Document):
            class Meta:
                collection_name = 'foobar'

        self.assertEqual(SomeDocument._meta.collection_name, 'foobar')


class TestMetaOptions(TestCase):

    def test_defaults(self):

        class ADoc(Document):
            pass

        self.assertDictEqual(Options.defaults(ADoc), {
            'using': None,
            'collection_name': 'adoc',
            'indexes': [],
        })

    def test_using_is_overridden(self):

        class MyDocument(Document):
            class Meta:
                using = 'foo'

        self.assertEqual(MyDocument._meta.using, 'foo')

    def test_collection_name_is_overridden(self):

        class MyDocument(Document):
            class Meta:
                collection_name = 'foo'

        self.assertEqual(MyDocument._meta.collection_name, 'foo')

    def test_indexes_is_overridden(self):

        index = Index('title')

        class MyDocument(Document):
            class Meta:
                using = 'mongodb'
                indexes = [index]

        self.assertEqual(MyDocument._meta.indexes, [index])


class TestIndexes(TestCase):
    maxDiff = None

    def test_get_indexes(self):

        mocked_collection =  Mock()
        mocked_collection.index_information = Mock(return_value={
            u'_id_': {u'key': [(u'_id', 1)], u'v': 1},
            u'titles_-1': {u'key': [(u'titles', -1)], u'v': 1},
            u'titles_-1_val_1': {u'key': [(u'titles', -1), (u'val', 1)], u'v': 1},
            u'titles_1': {u'key': [(u'titles', 1)], u'v': 1},
            u'val_1': {u'key': [(u'val', 1)], u'unique': True, u'v': 1},
        })

        manager = Manager()
        manager._get_collection = Mock(return_value=mocked_collection)
        expected = [
            Index('titles'),
            Index('_id'),
            Index('val', unique=True),
            Index([('titles', Index.DESCENDING), ('val', Index.ASCENDING)]),
            Index([('titles', Index.DESCENDING)]),
        ]
        self.assertEqual(sorted(manager.get_indexes()), sorted(expected))

    def test_proper_indexes_are_created(self):
        
        index1 = Index('ID', unique=True)
        index2 = Index([('ID', Index.ASCENDING), ('title', Index.DESCENDING)])

        class IndexedDocument(Document):
            class Meta:
                using = 'mongodb'
                indexes = [index1, index2]

        self.assertIn(index1, IndexedDocument.objects.get_indexes())
        self.assertIn(index2, IndexedDocument.objects.get_indexes())

    def test_auto_ensure_indexes_is_respected(self):

        class NotYetIndexedDocument(Document):
            auto_ensure_indexes = False

            class Meta:
                using = 'mongodb'
                indexes = [Index('title')]

        self.assertEqual(NotYetIndexedDocument.objects.get_indexes(), [])


class TestDocument(TestCase):

    def test_eq(self):
        self.assertEqual(Document(data={'foo': 'bar'}),
            Document(data={'foo': 'bar'}))
        self.assertNotEqual(Document(data={'foo': 'bar'}),
            Document(data={'foo': 'baz'}))

    def test_id(self):
        self.assertEqual(Document(data={'_id': 'foobar', 'foo': 'bar'}).id,
            'foobar')

    def test_repr(self):
        self.assertEqual(repr(Document(data={})), '<Document: {}>')

    def test_save(self):
        item = Item()
        self.assertIsNone(item.id)
        item.save()
        self.assertIsNotNone(item.id)
        self.assertItemsEqual([item.id for item in Item.objects.all()],
            [item.id])

    def test_save_updates_if_it_already_has_id(self):
        item = Item(data={'title': 'Slayer'})
        item.save()
        item.data['genre'] = 'trash metal'
        item.save()
        self.assertEqual(Item.objects.get(title='Slayer').data.get('genre'),
            'trash metal')

