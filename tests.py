"""
Unit tests runner for ``djongo`` based on boundled example project.
Tests are independent from this example application but setuptools need
instructions how to interpret ``test`` command when we run::

    python setup.py test

"""
import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = 'djongo.testsettings'
from djongo import testsettings as settings

def run_tests(settings):
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(interactive=False)
    failures = test_runner.run_tests(['djongo'])
    return failures

def main():
    failures = run_tests(settings)
    sys.exit(failures)

if __name__ == '__main__':
    main()

