#!/bin/env python

#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

VERSION = '0.1.0'

import sys, os
from setuptools import setup, find_packages

# ---------------------------------------------------------------------------

try:
    import stackless
except ImportError:
    print 'You must use Python Stackless !'
    print 'Get it at http://www.stackless.com'
    sys.exit(-1)

if sys.version_info < (2, 5, 2):
    print 'The version of Stackless Python must be 2.5.2 or more'
    sys.exit(-2)

# ---------------------------------------------------------------------------

f = open(os.path.join(os.path.dirname(__file__), 'docs', 'features.txt'))
long_description = f.read()
f.close()

setup(
      name = 'nagare',
      version = VERSION,
      author = 'Alain Poirier',
      author_email = 'alain.poirier at net-ng.com',
      description = 'Nagare Python web framework',
      long_description = long_description,
      license = 'BSD',
      keywords = 'web wsgi framework sqlalchemy elixir seaside continuation ajax stackless',
      url = 'http://www.nagare.org',
      download_url = 'http://www.nagare.org/download',
      packages = find_packages(),
      include_package_data = True,
      package_data = { '' : ['nagare/static/*',] },
      namespace_packages = ('nagare',),
      zip_safe = False,
      dependency_links = ('http://www.nagare.org/download/',),
      install_requires = ('PEAK-Rules', 'configobj', 'lxml==2.1.1', 'WebOb', 'Paste', 'flup', 'python-memcached'),
      extras_require = {
        'debug' : ('weberror',),
        'database' : ('sqlalchemy==0.4.6', 'elixir==0.5.2'),
        'doc' : ('pygments', 'docutils', 'rstdoc==0.9.0'),
        'test' : ('nose',),
        'full' : (
                  'weberror',
                  'sqlalchemy==0.4.6', 'elixir==0.5.2',
                  'pygments', 'docutils', 'rstdoc',
                  'nose'
                 ),
      },
      test_suite = 'nose.collector',
      #tests_require = 'nose',
      entry_points = '''
      [distutils.commands]
      generate_api = nagare.doc.setuplib:GenerateAPI [doc]
      generate_html = nagare.doc.setuplib:GenerateHTML [doc]

      [console_scripts]
      nagare-admin = nagare.admin.main:main

      [nagare.commands]
      info = nagare.admin.info:Info
      serve = nagare.admin.serve:Serve
      serve-module = nagare.admin.serve_module:Serve
      create-app = nagare.admin.create:Create
      create-db = nagare.admin.db:DBCreate
      drop-db = nagare.admin.db:DBDrop
      shell = nagare.admin.shell:Shell
      create-rules = nagare.admin.create_rules:CreateRules

      [nagare.publishers]
      standalone = nagare.publishers.standalone_publisher:Publisher
      fastcgi = nagare.publishers.fcgi_publisher:Publisher
      fapws2 = nagare.publishers.fapws_publisher:Publisher
      eventlet = nagare.publishers.eventlet_publisher:Publisher

      [nagare.sessions]
      standalone = nagare.sessions.threaded_sessions:SessionsFactory
      memcache = nagare.sessions.memcached_sessions:SessionsFactory

      [nagare.applications]
      admin = nagare.admin.admin_app:app

      [nagare.admin]
      info = nagare.admin.interface.info:Admin
      apps = nagare.admin.interface.applications:Admin
      ''',
      classifiers = (
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
