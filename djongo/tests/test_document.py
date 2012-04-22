from django.test import TestCase
from djongo.document import Document
from djongo.document import Manager

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

