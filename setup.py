import os
import multiprocessing

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.txt')) as f:
        README = f.read()
    with open(os.path.join(here, 'CHANGES.txt')) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ''

install_requires=[
    'setuptools',
    'wsgiref == 0.1.2',
    'redis==2.7.6',
    'pymongo==2.5.1',
    'Django==1.3.1',
    'pycurl==7.19.0',
    'argparse==1.2.1',
    'pytz',
    'msgpack-python',
]

tests_require = [
    'nose',
]

docs_extras = [
    'Sphinx',
    'docutils',
]

testing_extras = tests_require + [
    'virtualenv',
]

dependency_links = [
    "https://pypi.python.org/packages/2.7/p/pytz/pytz-2013b-py2.7.egg#md5=7cfcc57ddb87125a042b70c03580d6cf",
]

setup(name='maxstrike',
      version='1.0',
      description=('MaxStrike'),
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Intended Audience :: Developers",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Operating System :: POSIX"
      ],
      keywords='python django mongodb redis',
      author='Oneclick',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires = install_requires,
      dependency_links = dependency_links,
      extras_require = {
          'testing': testing_extras,
          'docs': docs_extras,
      },
      tests_require = tests_require,
      test_suite="nose.collector",
      entry_points={
        'console_scripts': [
            'indexer = apps.oclib.scripts.indexer:main',
        ]
      }
      )
