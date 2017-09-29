# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Import an object from a string reference

The possible reference syntaxes are:

  - ``'python <module>:<object>'`` -- loads an object from a Python module
    (for example: ``'python os.path:isfile'``)
  - ``'<module>:<object>'``  -- same as ``'python <module>:<object>'``
  - ``'file <file>:<object>'`` -- loads an object from a file
    (for example: ``'file /tmp/counter.py:Counter'``)
  - ``'egg <dist>:<app>'`` -- loads the registered application ``<app>``
    from the ``<dist>`` distribution
    (for example: ``'egg nagare:admin'`` or ``'egg nagare.examples:wiki'``)
  - ``'app <app>'`` -- load the registered application ``<app>``
    (for example: ``'app examples'``)
"""

import sys
import os

import pkg_resources


def load_entry_point(app, entry_point):
    """Load an object registered under an entry point

    In:
      - ``app`` -- name of the object
      - ``entry_point`` -- name of the entry_point

    Return:
      - (the object, the distribution of the object)
    """
    apps = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points(entry_point)])
    entry_point = apps[app]

    return entry_point.load(), entry_point.dist


def load_app(app, _):
    """Load a registered application

    In:
      - ``app`` -- name of the application
      - ``_`` -- *unused**

    Return:
      - (the application, the distribution of the application)
    """
    return load_entry_point(app, 'nagare.applications')


def load_egg(dist, app):
    """Load a registered application of a distribution

    In:
      - ``dist`` -- name of the distribution
      - ``app`` -- name of the application

    Return:
      - (the application, the distribution of the application)
    """
    dist = pkg_resources.get_distribution(dist)
    return dist.get_entry_info('nagare.applications', app).load(), dist


def load_file(filename, app):
    """Load an object from a file

    In:
      - ``filename`` -- name of the file
      - ``app`` -- name of the object to load

    Return:
      - (the object, None)
    """
    dirname = os.path.abspath(os.path.dirname(filename))
    if dirname not in sys.path:
        sys.path.insert(0, dirname)

    name = os.path.splitext(os.path.basename(filename))[0]
    return load_module(name, app)


def load_module(module, app):
    """Load an object from a Python module

    In:
      - ``module`` -- name of the module
      - ``app`` -- name of the object to load

    Return:
      - (the object, None)
    """
    r = __import__(module, fromlist=('',))

    if app is not None:
        r = getattr(r, app)

    return r, None


loaders = {
    '': load_module,
    'python': load_module,
    'egg': load_egg,
    'file': load_file,
    'app': load_app
}


def load_object(reference):
    """Load an object from a reference

    In:
      - ``reference`` -- reference as a string

    Return:
      - a tuple (object loaded, distribution where this object is located or ``None``)
    """
    if ' ' in reference:
        scheme, reference = reference.split(' ', 1)
    else:
        scheme = ''

    if ':' in reference:
        (reference, o) = reference.split(':', 1)
    else:
        o = None

    return loaders[scheme](reference, o)
