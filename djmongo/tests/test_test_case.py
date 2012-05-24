from djmongo.test import TestCase
from djmongo.document import Document


class TestOurTestCase(TestCase):

    def test_assertDocumentsEqual(self):

        self.assertDocumentsEqual([{'foo': 'bar'}, {'baz', 'tar'}],
            [{'foo': 'bar'}, {'baz', 'tar'}])

    def test_assertDocumentsEqual_ommit_mongo_id(self):

        self.assertDocumentsEqual([{'foo': 'bar', '_id': 123}, {'baz': 'tar',
            '_id': 456}],
            [{'foo': 'bar'}, {'baz': 'tar', '_id': 5556}])

    def test_assertDocumentsEqual_works_for_documents(self):

        self.assertDocumentsEqual([Document(data={'foo': 'bar'}),
            Document(data={'baz', 'tar'})],
            [{'foo': 'bar'}, {'baz', 'tar'}])

    def test_assertDocumentsEqual_works_for_iterators(self):

        self.assertDocumentsEqual(iter([{'foo': 'bar'}, {'baz', 'tar'}]),
            iter([{'foo': 'bar'}, {'baz', 'tar'}]))

    def test_assertDocumentsEqual_raises(self):

        with self.assertRaises(AssertionError):
            self.assertDocumentsEqual([{'foo': 'bar'}, {'baz', 'tar'}],
                [{'foo': 'bar'}, {'foo', 'bar'}])

    def test_assertDocumentsEqual_raises_for_different_number_of_items(self):

        with self.assertRaises(AssertionError):
            self.assertDocumentsEqual([{'foo': 'bar'}],
                [{'foo': 'bar'}, {'foo', 'bar'}])

