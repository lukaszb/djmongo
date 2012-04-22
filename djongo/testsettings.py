TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'database.sqlite',
        'TEST_NAME': ':memory:',
    },

    'mongodb': {
        'ENGINE': 'djongo.backend.mongodb',
        'NAME': 'testdb',
    }
}

INSTALLED_APPS = (
    'djongo',
)
