from django.conf import settings
from django.db import connections


def is_mongodb_connection(connection):
    from djmongo.backend.mongodb.base import DatabaseWrapper
    return isinstance(connection, DatabaseWrapper)


def get_mongodb_connections():
    return [conn for conn in connections.all() if is_mongodb_connection(conn)]

def can_drop_collection(collection_name):

    return (collection_name.startswith(settings.MONGODB_COLLECTIONS_PREFIX) and
            not collection_name.startswith('system.'))

