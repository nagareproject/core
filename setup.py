#!/bin/env python

# --
# Copyright (c) 2008-2019 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import os
import textwrap

from setuptools import setup, find_packages


try:
    import stackless  # noqa: F401
except ImportError:
    print("Warning: you are installing Nagare on CPython instead of Stackless Python (http://www.stackless.com) or PyPy (http://pypy.org).")
    print("         Without 'continuation', the 'Component.call()' method will not be available.")

# -----------------------------------------------------------------------------


with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    LONG_DESCRIPTION = f.read()


setup(
    name='nagare',
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
    """) % LONG_DESCRIPTION,
    license='BSD',
    keywords='web wsgi framework sqlalchemy seaside continuation ajax stackless',
    url='http://www.nagare.org',
    download_url='http://www.nagare.org/download',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
    install_requires=[
        'WebOb', 'cryptography',
        'nagare-server-mvc',
        'nagare-services-sessions',
        'nagare-renderers-html',
        'nagare-services-i18n'
    ],
    message_extractors={'nagare': [('**.py', 'python', None)]},
    extras_require={
        'dev': ['nagare-services-webassets'],
        'doc': ['sphinx', 'sphinx_rtd_theme<0.3']
    },
    entry_points='''
        [nagare.commands]
        #create-rules = nagare.admin.create_rules:CreateRules

        [nagare.applications]
        #admin = nagare.admin.admin_app:app

        #[nagare.admin]
        #info = nagare.admin.interface.info:Admin
        #apps = nagare.admin.interface.applications:Admin

        [nagare.services]
        exceptions = nagare.services.core_exceptions:ExceptionsService
        state = nagare.services.state:StateService
        create_root = nagare.services.create_root:RootService
        redirect_after_post = nagare.services.prg:PRGService
        callbacks = nagare.services.callbacks:CallbacksService
        ajax = nagare.services.ajax:AjaxService
        ''',
    classifiers=[
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
    ]
)
