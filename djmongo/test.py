from django.test import TestCase as BaseTestCase
from djmongo.utils import get_mongodb_connections
from djmongo.document import Document


class TestCase(BaseTestCase):

    def __call__(self, *args, **kwargs):
        result = super(TestCase, self).__call__(*args, **kwargs)
        self.__post_teardown()
        return result

    def __post_teardown(self):
        for conn in get_mongodb_connections():
            conn.clear_all_collections()

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

