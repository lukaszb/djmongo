from django.db import connections


def is_mongodb_connection(connection):
    from djmongo.backend.mongodb.base import DatabaseWrapper
    return isinstance(connection, DatabaseWrapper)


def get_mongodb_connections():
    return [conn for conn in connections.all() if is_mongodb_connection(conn)]

def can_drop_collection(collection_name):
    return not collection_name.startswith('system.')

