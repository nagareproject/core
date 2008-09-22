#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``serve-module`` administrative command

Launch a standalone (without database connection) application, in debug mode.

No configuration file in read. The only possible parameters are given on the
command line and are (run ``nagare-admin serve-module`` to see them):

  - the host
  - the port
  - the web debug mode
  - the reload mode

Also not static contents can be served.

.. warning::
    Use this command in development or to quickly test a piece code.
    Don't run a production application with this command
"""

import sys, os

import pkg_resources

from nagare import wsgi
from nagare.admin import util, reloader

def get_file_from_package(package, path):
    """
    Return the path of a static content, located into a setuptools package
    
    In:
      - ``package`` -- the setuptools package of a registered application
      - ``path`` -- the url path of the static content wanted
      
    Return:
      - the path of the static content
    """
    path = os.path.join('static', path[1:])
    
    if not pkg_resources.resource_exists(package, path) or pkg_resources.resource_isdir(package, path):
        return None
    
    return pkg_resources.resource_filename(package, path)


def set_options(optparser):
    optparser.usage += ' module_or_file name'

    optparser.add_option('--host', action='store', type='string', default='127.0.0.1', help='Name of the interface to listen to ("0.0.0.0" to listen to on all the interfaces)')
    optparser.add_option('-p', '--port', action='store', type='int', dest='port', default=8080, help='Port to listen to')
    optparser.add_option('--no-debug', action='store_const', const=False, default=True, dest='debug', help='Desactivation of the web error page')


def run(parser, options, args):
    """launch an object
    
    In:
      - ``parser`` -- the optparse.OptParser object used to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines
      
    The unique argument is the path of the object to launch. The path syntax is describe
    into the module ``nagare.admin.util``. For example, ``/tmp/counter.py:Counter``
    is the path to the class ``Counter`` of the module ``tmp.counter.py``
     
    """    
    if len(args) != 2:
        parser.error('Bad number of arguments')

    if 'nagare_reloaded' not in os.environ:
        return reloader.restart_with_monitor()
    
    # With the ``serve-module`` command, the automatic reloader on changes is
    # always activated
    watcher = reloader.install()

    # Load the object
    if os.path.sep in args[0]:
        path = 'file ' + args[0]
    else:
        path = 'python ' + args[0]
    app = util.load_object(path)[0]
    
    # Wrap it into a WSGIApp
    app = wsgi.create_WSGIApp(app)

    # Always use the standalone session manager (in memory sessions)
    sessions = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.sessions')])
    s = sessions['standalone'].load()(None, {}, None)
    
    # Always use the standalone publisher (Python HTTP server)
    publishers = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.publishers')])
    p = publishers['standalone'].load()(s)

    p.register_application(args[0], args[1], app, options.debug)
    app.set_config('', { 'application' : { 'redirect_after_post' : False, 'name' : args[1], 'always_html' : True } }, None, '', p)
    
    # The static contents of the framework are served by the standalone server
    p.register_static('nagare', lambda path, r=pkg_resources.Requirement.parse('nagare'): get_file_from_package(r, path))
    
    # Launch the object
    p.serve(None, dict(host=options.host, port=options.port), None)

# ---------------------------------------------------------------------------

class Serve(util.Command):
    desc = 'Launch a python module'

    set_options = staticmethod(set_options)
    run = staticmethod(run)
