#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``serve`` administrative command

Launch one or more applications.
"""

import os

import pkg_resources
import configobj

from nagare import config, log
from nagare.admin import reloader, util

# ---------------------------------------------------------------------------

# The default publisher configuration
# -----------------------------------

publisher_options_spec = {
    'publisher' : dict(
        host = 'string(default="127.0.0.1")', # Listen only on the loopback interface
        port = 'integer(default=-1)' # The default port depends of the publisher used
    ),

    'reloader' : dict(
        activated = 'boolean(default=False)', # No automatic reload
        interval = 'integer(default=1)',
    ),
}

# ---------------------------------------------------------------------------

def set_options(optparser):
    optparser.usage += ' application'

    optparser.add_option('-c', '--conf', dest='conf', help='configuration file')
    optparser.add_option('--host', action='store', type='string', help='Name of the interface to listen on ("0.0.0.0" to listen on all the interfaces)')
    optparser.add_option('-p', '--port', action='store', type='int', dest='port', help='Port to listen on')
    optparser.add_option('-d', '--debug', action='store_const', const='on', dest='debug', help='Activation of the web error page')
    optparser.add_option('--reload', action='store_const', const=True, dest='reload', help='Restart the application when a source file is changed')


def read_publisher_options(parser, options):
    """Read the configuration file for the publisher

    This configuration file is given with the ``-c``or ``--config`` option

    In:
      - ``parser`` -- the ``optparse.OptParser`` object used to parse the configuration file
      - ``options`` -- options in the command line

    Return:
      - a ``ConfigObj`` with the publisher parameters
    """
    if options.conf and not os.path.isfile(options.conf):
        parser.error('Configuration file "%s" doesn\'t exit' % options.conf)

    configspec = configobj.ConfigObj(publisher_options_spec)

    if options.conf:
        configspec.merge({ 'here' : 'string(default="%s")' % os.path.abspath(os.path.dirname(options.conf)) })

    choices = ', '. join(['"%s"' % entry.name for entry in pkg_resources.iter_entry_points('nagare.publishers')])
    configspec.merge({ 'publisher' : { 'type' : 'option(%s, default="standalone")' % choices } })

    choices = ', '. join(['"%s"' % entry.name for entry in pkg_resources.iter_entry_points('nagare.sessions')])
    configspec.merge({ 'sessions' : { 'type' : 'option(%s, default="standalone")' % choices } })

    conf = configobj.ConfigObj(options.conf, configspec=configspec, interpolation='Template')
    config.validate(options.conf, conf, parser.error)

    # The options in the command line overwrite the parameters read into the configuration file
    for (name, section, key) in (
                                    ('host', 'publisher', 'host'),
                                    ('port', 'publisher', 'port'),
                                    ('debug', 'publisher', 'debug'),
                                    ('reload', 'reloader', 'activated')
                                ):
        option = getattr(options, name)
        if option is not None:
            conf[section][key] = option

    return conf

# ---------------------------------------------------------------------------

try:
    from weberror.evalexception import EvalException

    debugged_app = lambda app: EvalException(app, xmlhttp_key='_a')
except ImportError:
    debugged_app = lambda app: app

def create_wsgi_pipe(app, options, config_filename, config, error):
    """Wrap the application into one or more WSGI "middlewares" to create a WSGI pipe

    In:
      - ``app`` -- the application
      - ``options`` -- options in the command line
      - ``config_filename`` -- the path to the configuration file
      - ``config`` -- the ``ConfigObj`` object, created from the configuration file
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - the wsgi pipe
    """
    if options.debug or config['application']['debug']:
        app = debugged_app(app)

    wsgi_pipe = config['application']['wsgi_pipe']
    if not wsgi_pipe:
        return app

    return util.load_object(wsgi_pipe)[0](app, options, config_filename, config, error)

# ---------------------------------------------------------------------------

def get_file_from_root(root, path):
    """
    Return the path of a static content, from a filesystem root

    In:
      - ``root`` -- the path of the root
      - ``path`` -- the url path of the wanted static content

    Return:
      - the path of the static content
    """
    filename = os.path.join(root, path[1:])

    if not os.path.exists(filename) or os.path.isdir(filename):
        return None

    return filename


def get_file_from_package(package, path):
    """
    Return the path of a static content, from a setuptools package

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

# ---------------------------------------------------------------------------

def run(parser, options, args):
    """Launch one or more applications

    In:
      - ``parser`` -- the ``optparse.OptParser`` object used to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines

    The arguments are a list of names of registered applications
    or paths to application configuration files.
    """
    # If no argument are given, display the list of the registered applications
    if len(args) == 0:
        print 'Available applications:'

        # The applications are registered under the ``nagare.applications`` entry point
        applications = pkg_resources.iter_entry_points('nagare.applications')
        for name in sorted([application.name for application in applications]):
            print ' -', name
        return

    # Read the (optional) publisher configuration file
    pconf = read_publisher_options(parser, options)
    if pconf['reloader']['activated']:
        if 'nagare_reloaded' not in os.environ:
            return reloader.restart_with_monitor()

        filenames = pconf['reloader'].get('files', [])
        if isinstance(filenames, basestring):
            filenames = [filenames]
        filenames = filter(os.path.isfile, filenames)
        if options.conf:
            filenames.append(options.conf)

        watcher = reloader.install(pconf['reloader']['interval'], filenames, (pkg_resources.get_default_cache(),))
    else:
        watcher = None

    # Load the publisher
    publishers = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.publishers')])
    t = pconf['publisher']['type']
    publisher = publishers[t].load()()

    # If no port is given, set the port number according to the used publisher
    if pconf['publisher']['port'] == -1:
        pconf['publisher']['port'] = publisher.default_port

    configs = []

    # Merge all the ``[logging]`` section of all the applications
    for cfgfile in args:
        # Read the configuration file of the application
        (cfgfile, app, dist, aconf) = util.read_application(cfgfile, parser.error)
        configs.append((cfgfile, app, dist, aconf))

        log.configure(aconf['logging'].dict(), aconf['application']['name'])

    # Configure the logging service
    log.activate()

    # Configure each application and register it to the publisher
    for (cfgfile, app, dist, aconf) in configs:
        #log.set_logger('nagare.application.'+aconf['application']['name'])

        if watcher:
            watcher.watch_file(aconf.filename)

        requirement = None if not dist else pkg_resources.Requirement.parse(dist.project_name)

        data_path = None if not requirement else pkg_resources.resource_filename(requirement, '/data')

        # Create the function to get the static contents of the application
        static_path = aconf['application'].get('static')
        get_file = None
        if static_path is not None and os.path.isdir(static_path):
            # If a ``static`` parameter exists, under the ``[application]`` section,
            # serve the static contents from this root
            get_file = lambda path, static_path=static_path: get_file_from_root(static_path, path)
        else:
            # Else, serve the static from the ``static`` directory
            # of the application package
            if requirement:
                get_file = lambda path, requirement=requirement: get_file_from_package(requirement, path)
                static_path = pkg_resources.resource_filename(requirement, '/static')

        # Register the function to serve the static contents of the application
        static_url = publisher.register_static(aconf['application']['name'], get_file)

        # Load the sessions manager factory
        sessions_managers = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.sessions')])
        conf = pconf['sessions'].dict()
        conf.update(aconf['sessions'].dict())
        t = conf.pop('type')

        sessions_manager = sessions_managers[t].load()()
        sessions_manager.set_config(options.conf, conf, parser.error)

        (app, metadatas) = util.activate_WSGIApp(
                                                    app,
                                                    cfgfile, aconf, parser.error,
                                                    '' if not dist else dist.project_name,
                                                    static_path, static_url,
                                                    data_path,
                                                    publisher,
                                                    sessions_manager
                                                )

        # Register the application to the publisher
        publisher.register_application(
                                       aconf['application']['path'],
                                       aconf['application']['name'],
                                       app,
                                       create_wsgi_pipe(app, options, cfgfile, aconf, parser.error)
                                      )

    # Register the function to serve the static contents of the framework
    publisher.register_static(
                                'nagare',
                                lambda path, r=pkg_resources.Requirement.parse('nagare'): get_file_from_package(r, path)
                             )

    # Launch all the applications
    publisher.serve(options.conf, pconf['publisher'], parser.error)

# ---------------------------------------------------------------------------

class Serve(util.Command):
    desc = 'Launch an application'

    set_options = staticmethod(set_options)
    run = staticmethod(run)
