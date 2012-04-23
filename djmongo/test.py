from django.test import TestCase as BaseTestCase
from djmongo.utils import get_mongodb_connections


class TestCase(BaseTestCase):

    def __call__(self, *args, **kwargs):
        result = super(TestCase, self).__call__(*args, **kwargs)
        self.__post_teardown()
        return result

    def __post_teardown(self):
        for conn in get_mongodb_connections():
            conn.clear_all_collections()

