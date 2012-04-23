=======
djmongo
=======

``djmongo`` is yet another mongodb_ adapter for Django_. This one however, is
build directly on pymongo_, tries to be as small and simple as possible and
mimics Django_'s ORM (managers/querysets).

``djmongo`` supports Django_ >= 1.3.


Installation
------------

To install ``djmongo`` simply run::

    pip install djmongo

Configuration
-------------

``djmongo`` provides *database engine* so configuration is rather
straight-forward::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'database.sqlite',
            'TEST_NAME': ':memory:',
        },

        'mongodb': {
            'ENGINE': 'djmongo.backend.mongodb',
            'NAME': 'testdb',
        }
    }

In above example we added ``mongodb`` aliased connection to local mongodb
server.


Usage
-----

Create a document::

    from djmongo.document import Document

    class MyDocument(Document):

        class Meta:
            using = 'mongodb'

    doc1 = MyDocument.objects.create(data={'foo': 'bar'})
    doc2 = MyDocument.objects.create(data={'foo': 'baz'})

    ...


Testing
-------

In order to properly test an application, one would like to destroy all objects
inserted during test run between test cases. Normally, Django_ does that using
transactions, however we need to destroy objects manually. One can do that at
*tearDown* method using connection's extra method called
``clear_all_collections``. Alternatively, one can use subclass of Django_'s
``django.test.TestCase``: ``djmongo.test.TestCase``.

Development
-----------

We use github_ for development of this package (repository, issue tracker).
We also use tox_ for package testing against - if one would like to run whole
test suite against all supported Django_ versions, simply *clone* repository and
run ``tox`` command within it (``pip install tox`` if it's missing).


(Un)license
-----------

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>

.. _Django: http://www.djangoproject.org/
.. _mongodb: http://www.mongodb.org/
.. _pymongo: https://github.com/mongodb/mongo-python-driver
.. _tox: http://pypi.python.org/pypi/tox
.. _github: http://github.com

