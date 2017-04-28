#!/bin/env python

#--
# Copyright (c) 2008-2013 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

VERSION = '0.4.1'

import sys
import os
import textwrap

from setuptools import setup, find_packages

# -----------------------------------------------------------------------------

try:
    import stackless
except ImportError:
    print "Warning: you are installing Nagare on CPython instead of Stackless Python (http://www.stackless.com) or PyPy (http://pypy.org)."
    print "         Without 'continuation', the 'Component.call()' method will not be available."

if sys.version_info < (2, 5, 2):
    print 'The version of Python must be 2.5.2 or more'
    sys.exit(-2)

# -----------------------------------------------------------------------------

f = open(os.path.join(os.path.dirname(__file__), 'docs', 'features.txt'))
long_description = f.read()
f.close()

setup(
      name='nagare',
      version=VERSION,
      author='Alain Poirier',
      author_email='alain.poirier at net-ng.com',
      description='Nagare Python web framework',
      long_description=textwrap.dedent("""
      Description
      ^^^^^^^^^^^

      %s

      Installation
      ============

      For a standard installation, read the ``docs/quickstart.txt`` document.

      Read ``docs/framework_installation.txt`` to install the
      `latest <http://www.nagare.org/snapshots/nagare-latest#egg=nagare-dev>`_
      development version from the `Mercurial repository <http://hg.nagare.org/core>`_
      or to create a Nagare developer installation.
      """) % long_description,
      license='BSD',
      keywords='web wsgi framework sqlalchemy elixir seaside continuation ajax stackless',
      url='http://www.nagare.org',
      download_url='http://www.nagare.org/download',
      packages=find_packages(),
      include_package_data=True,
      use_hg_version=True,
      package_data={'': ['nagare/static/*']},
      namespace_packages=('nagare',),
      zip_safe=False,
      dependency_links=('http://www.nagare.org/download/',),
      install_requires=('PEAK-Rules', 'ConfigObj', 'lxml>=3.0.1', 'WebOb>=1.2.3', 'Paste', 'flup', 'python-memcached', 'nagare-namespaces'),
      message_extractors={'nagare': [
          ('test/**', 'ignore', None),
          ('**.py', 'python', None),
      ]},
      extras_require={
        'debug': ('WebError',),
        'database': ('SQLAlchemy', 'Elixir'),
        'doc': ('Pygments==1.1', 'docutils', 'RstDoc'),
        'test': ('nose',),
        'i18n': ('Babel', 'pytz'),
        'full': (
                  'WebError',
                  'SQLAlchemy', 'Elixir',
                  'Pygments==1.1', 'docutils', 'RstDoc',
                  'nose',
                  'Babel', 'pytz'
                 ),
      },
      test_suite='nose.collector',
      #tests_require = 'nose',
      entry_points='''
      [distutils.commands]
      generate_api = nagare.doc.setuplib:GenerateAPI [doc]
      generate_html = nagare.doc.setuplib:GenerateHTML [doc]

      [console_scripts]
      nagare-admin = nagare.admin.command:run

      [nagare.commands]
      info = nagare.admin.info:Info
      serve = nagare.admin.serve:Serve
      serve-module = nagare.admin.serve_module:Serve
      create-app = nagare.admin.create:Create
      create-db = nagare.admin.db:DBCreate
      drop-db = nagare.admin.db:DBDrop
      shell = nagare.admin.shell:Shell
      batch = nagare.admin.shell:Batch
      create-rules = nagare.admin.create_rules:CreateRules

      [nagare.publishers]
      standalone = nagare.publishers.standalone_publisher:Publisher
      threaded = nagare.publishers.standalone_publisher:Publisher
      fastcgi = nagare.publishers.fcgi_publisher:Publisher
      fapws3 = nagare.publishers.fapws_publisher:Publisher
      eventlet = nagare.publishers.eventlet_publisher:Publisher

      [nagare.sessions]
      standalone = nagare.sessions.memory_sessions:SessionsWithPickledStates
      pickle = nagare.sessions.memory_sessions:SessionsWithPickledStates
      memcache = nagare.sessions.memcached_sessions:Sessions

      [nagare.applications]
      admin = nagare.admin.admin_app:app

      [nagare.admin]
      info = nagare.admin.interface.info:Admin
      apps = nagare.admin.interface.applications:Admin
      ''',
      classifiers=(
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Environment :: Web Environment',
        'Operating System :: Microsoft :: Windows :: Windows NT/2000',
        'Operating System :: Unix',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
      )
)
