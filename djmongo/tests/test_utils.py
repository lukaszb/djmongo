from django.conf import settings
from djmongo.test import TestCase
from djmongo.utils import can_drop_collection

class TestCanDropCollection(TestCase):

    def test_default_can_drop_collections_true_only_if_properly_prefixed(self):
        self.assertFalse(can_drop_collection('foobar'))
        self.assertFalse(can_drop_collection('foo.bar'))
        self.assertFalse(can_drop_collection('foo.bar.baz'))
        self.assertFalse(can_drop_collection('system.users'))

        prefix = settings.MONGODB_COLLECTIONS_PREFIX
        self.assertTrue(can_drop_collection('%s.%s' % (prefix, 'foobar')))
        self.assertTrue(can_drop_collection('%s.%s' % (prefix, 'foo.bar')))
        self.assertTrue(can_drop_collection('%s.%s' % (prefix, 'foo.bar.baz')))
        self.assertTrue(can_drop_collection('%s.%s' % (prefix, 'system')))
        self.assertTrue(can_drop_collection('%s.%s' % (prefix, 'system.users')))

