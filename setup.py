import os
import sys
from setuptools import setup, find_packages

djmongo = __import__('djmongo')
readme_file = os.path.join(os.path.dirname(__file__), 'README.rst')
try:
    long_description = open(readme_file).read()
except IOError, err:
    sys.stderr.write("[ERROR] Cannot find file specified as "
        "``long_description`` (%s)\n" % readme_file)
    sys.exit(1)

setup(
    name = 'djmongo',
    version = djmongo.get_version(),
    url = 'http://github.com/lukaszb/djmongo',
    author = 'Lukasz Balcerzak',
    author_email = 'lukaszbalcerzak@gmail.com',
    download_url='http://github.com/lukaszb/djmongo/downloads',
    description = djmongo.__doc__.strip(),
    long_description = long_description,
    zip_safe = False,
    packages = find_packages(),
    include_package_data = True,
    scripts = [],
    requires = [],
    license = 'BSD',
    install_requires = [
        'Django>=1.3',
        'pymongo>=2.1.1',
    ],
    classifiers = ['Development Status :: 5 - Production/Stable',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Security',
    ],
    test_suite='tests.main',
)
