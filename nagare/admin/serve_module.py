#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``serve-module`` administrative command

Launch a standalone (without any database connection) application, in debug mode.

No configuration file in read. The only possible parameters are given on the
command line and are (run ``nagare-admin serve-module`` to see them):

  - the host
  - the port
  - the web debug mode
  - the reload mode

Also no static contents can be served.

.. warning::
    Use this command in development mode or to quickly test a piece code.
    Don't run a production application with this command
"""

import os

import pkg_resources

from nagare import wsgi, log
from nagare.admin import util, reloader

try:
    from weberror.evalexception import EvalException

    debugged_app = lambda app: EvalException(app, xmlhttp_key='_a')
except ImportError:
    debugged_app = lambda app: app


def get_file_from_package(package, path):
    """
    Return the path of a static content, located into a setuptools package

    In:
      - ``package`` -- the setuptools package of a registered application
      - ``path`` -- the url path of the wanted static content

    Return:
      - the path of the static content
    """
    path = os.path.join('static', path[1:])

    if not pkg_resources.resource_exists(package, path) or pkg_resources.resource_isdir(package, path):
        return None

    return pkg_resources.resource_filename(package, path)


def set_options(optparser):
    optparser.usage += ' module_or_file name'

    optparser.add_option('--host', action='store', type='string', default='127.0.0.1', help='Name of the interface to listen on ("0.0.0.0" to listen on all the interfaces)')
    optparser.add_option('-p', '--port', action='store', type='int', dest='port', default=8080, help='Port to listen on')
    optparser.add_option('--no-debug', action='store_const', const=False, default=True, dest='debug', help='Desactivation of the web error page')


def run(parser, options, args):
    """launch an object

    In:
      - ``parser`` -- the ``optparse.OptParser`` object used to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines

    The unique argument is the path of the object to launch. The path syntax is described
    into the module ``nagare.admin.util``. For example, ``/tmp/counter.py:Counter``
    is the path to the class ``Counter`` of the module ``tmp.counter.py``

    """
    if len(args) != 2:
        parser.error('Bad number of arguments')

    if 'nagare_reloaded' not in os.environ:
        return reloader.restart_with_monitor()

    # With the ``serve-module`` command, the automatic reloader is always activated
    reloader.install(excluded_directories=(pkg_resources.get_default_cache(),))

    # Load the object
    if os.path.sep in args[0]:
        path = 'file ' + args[0]
    else:
        path = 'python ' + args[0]
    app = util.load_object(path)[0]

    # Wrap it into a WSGIApp
    app = wsgi.create_WSGIApp(app)

    # Always use the standalone publisher (Python HTTP server)
    publishers = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.publishers')])
    publisher = publishers['standalone'].load()()

    wsgi_pipe = debugged_app(app) if options.debug else app
    publisher.register_application(args[0], args[1], app, wsgi_pipe)
    app.set_config('', { 'application' : { 'redirect_after_post' : False, 'name' : args[1], 'always_html' : True } }, None)
    app.set_publisher(publisher)

    # Always use the standalone session manager (in memory sessions)
    sessions_managers = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.sessions')])
    sessions_manager = sessions_managers['standalone'].load()()
    app.set_sessions_manager(sessions_manager)

    # Set the application logger level to DEBUG
    log.configure({ 'logger' : { 'level' : 'DEBUG' } }, args[1])
    log.activate()
    log.set_logger('nagare.application.'+args[1])

    # The static contents of the framework are served by the standalone server
    publisher.register_static('nagare', lambda path, r=pkg_resources.Requirement.parse('nagare'): get_file_from_package(r, path))

    # Launch the object
    publisher.serve(None, dict(host=options.host, port=options.port), None)

# ---------------------------------------------------------------------------

class Serve(util.Command):
    desc = 'Launch a python module'

    set_options = staticmethod(set_options)
    run = staticmethod(run)
