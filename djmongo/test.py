from django.test import TestCase as BaseTestCase
from djmongo.utils import get_mongodb_connections
from djmongo.document import Document
from djmongo.utils import can_drop_collection


class TestCase(BaseTestCase):

    def __call__(self, *args, **kwargs):
        result = super(TestCase, self).__call__(*args, **kwargs)
        self.post_teardown()
        return result

    def post_teardown(self):
        """
        Drops all collections from all mongodb connections for which
        ``can_drop_collection`` returns ``True``.
        """
        for conn in get_mongodb_connections():
            for collection_name in conn.db.collection_names():
                if self.can_drop_collection(collection_name, conn):
                    conn.db.drop_collection(collection_name)

    def can_drop_collection(self, collection_name, connection):
        """
        :param collection_name: collection's name, as string
        :param connection: mongodb connection
        """
        return can_drop_collection(collection_name)

    def assertDocumentsEqual(self, result, expected):

        def pop_id(data):
            if isinstance(data, Document):
                data = data.data
            if isinstance(data, dict):
                copied = data.copy()
                copied.pop('_id', None)
                return copied
            return data

        normalize = lambda data_list: (pop_id(item) for item in data_list)

        self.assertItemsEqual(normalize(result), normalize(expected))

