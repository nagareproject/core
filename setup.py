#!/bin/env python

# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import sys
import os
import textwrap

from setuptools import setup, find_packages

VERSION = '0.5.0'


# -----------------------------------------------------------------------------

try:
    import stackless  # noqa: F401
except ImportError:
    print "Warning: you are installing Nagare on CPython instead of Stackless Python (http://www.stackless.com) or PyPy (http://pypy.org)."
    print "         Without 'continuation', the 'Component.call()' method will not be available."

if sys.version_info < (2, 5, 2):
    print 'The version of Python must be 2.5.2 or more'
    sys.exit(-2)

# -----------------------------------------------------------------------------

f = open(os.path.join(os.path.dirname(__file__), 'doc', 'features.txt'))
long_description = f.read()
f.close()

setup(
    name='nagare',
    version=VERSION,
    author='Alain Poirier',
    author_email='alain.poirier@net-ng.com',
    description='Nagare Python web framework',
    long_description=textwrap.dedent("""
    Description
    ^^^^^^^^^^^

    %s

    Installation
    ============

    For a standard installation, read the `quickstart <http://www.nagare.org/doc/quickstart>`_ document.

    Read `framework installation <http://www.nagare.org/doc/framework_installation>`_ to run the
    latest development version from the `Github repository <https://github.com/nagareproject/core>`_
    or to create a Nagare developer installation.
    """) % long_description,
    license='BSD',
    keywords='web wsgi framework sqlalchemy elixir seaside continuation ajax stackless',
    url='http://www.nagare.org',
    download_url='http://www.nagare.org/download',
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['nagare/static/*']},
    namespace_packages=('nagare',),
    zip_safe=False,
    dependency_links=('http://www.nagare.org/download/',),
    install_requires=(
        'PEAK-Rules', 'ConfigObj', 'lxml', 'WebOb',
        'Paste', 'flup==1.0.3.dev-20110405', 'python-memcached'
    ),
    message_extractors={'nagare': [
        ('test/**', 'ignore', None),
        ('**.py', 'python', None),
    ]},
    extras_require={
        'debug': ('WebError',),
        'database': ('SQLAlchemy>0.5.8', 'Elixir'),
        'doc': ('sphinx', 'sphinx_rtd_theme<0.3'),
        'test': ('nose',),
        'i18n': ('Babel>=2.5.0', 'pytz'),
        'full': (
            'WebError',
            'SQLAlchemy>0.5.8', 'Elixir',
            'sphinx', 'sphinx_rtd_theme<0.3',
            'nose',
            'Babel>=2.5.0', 'pytz'
        ),
    },
    test_suite='nose.collector',
    entry_points='''
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
