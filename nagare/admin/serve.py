#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``serve`` administrative command

Launch one or more applications.
"""

import sys, os

import pkg_resources
import configobj

from nagare import wsgi, database, config

from nagare.admin import reloader, db, util

# ---------------------------------------------------------------------------

# The default publisher configuration
# -----------------------------------

publisher_options_spec = {
    'publisher' : dict(
        host = 'string(default="127.0.0.1")', # Listen only on the loopback interface
        port = 'integer(default=-1)'    # The default port depends of the publisher used
    ),
    
    'reloader' : dict(
        activated = 'boolean(default=False)',   # No automatic reload
        interval = 'integer(default=1)'
    ),
}

# ---------------------------------------------------------------------------

def set_options(optparser):
    optparser.usage += ' application'

    optparser.add_option('-c', '--conf', dest='conf', help='configuration file')
    optparser.add_option('--host', action='store', type='string', help='Name of the interface to listen to ("0.0.0.0" to listen to on all the interfaces)')
    optparser.add_option('-p', '--port', action='store', type='int', dest='port', help='Port to listen to')
    optparser.add_option('-d', '--debug', action='store_const', const='on', dest='debug', help='Activation of the web error page')
    optparser.add_option('--reload', action='store_const', const=True, dest='reload', help='Restart the application when a source file is changed')


def read_publisher_options(parser, options):
    """Read the configuration file for the publisher
    
    This configuration file is given with the ``-c``or ``--config`` option
    
    In:
      - ``parser`` -- the optparse.OptParser object used to parse the configuration file
      - ``options`` -- options on the command lines
      
    Return:
      - a ConfigObj with the publisher parameters    
    """
    if options.conf and not os.path.isfile(options.conf):
        parser.error('Configuration file "%s" doesn\'t exit' % options.conf)

    configspec = configobj.ConfigObj(publisher_options_spec)

    choices = ', '. join(['"%s"' % entry.name for entry in pkg_resources.iter_entry_points('nagare.publishers')])
    configspec.merge({ 'publisher' : { 'type' : 'option(%s, default="standalone")' % choices } })
    
    choices = ', '. join(['"%s"' % entry.name for entry in pkg_resources.iter_entry_points('nagare.sessions')])
    configspec.merge({ 'sessions' : { 'type' : 'option(%s, default="standalone")' % choices } })

    conf = configobj.ConfigObj(options.conf, configspec=configspec)
    config.validate(options.conf, conf, parser.error)

    # The options on the command line overwrite the parameters read into the configuration file
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

def get_file_from_root(root, path):
    """
    Return the path of a static content, from a filesystem root
    
    In:
      - ``root`` -- the path of the root
      - ``path`` -- the url path of the static content wanted
      
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
      - ``path`` -- the url path of the static content wanted
      
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
      - ``parser`` -- the optparse.OptParser object used to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines
      
    The arguments are a list of names of registered applications
    or paths to applications configuration files.
    """    
    # If no argiments are given, display the list of the registered applications
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
        
        if options.conf:
            filenames = [options.conf]
        else:
            filenames = None
                    
        watcher = reloader.install(pconf['reloader']['interval'], files=filenames)
    else:
        watcher = None

    # Load the session manager
    sessions = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.sessions')])
    t = pconf['sessions'].pop('type')
    s = sessions[t].load()(options.conf, pconf['sessions'], parser.error)
    
    # Load the publisher
    publishers = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.publishers')])
    t = pconf['publisher']['type']
    p = publishers[t].load()(s)

    # If no port is given, set the port number according the publisher used
    if pconf['publisher']['port'] == -1:
        pconf['publisher']['port'] = p.default_port

    # Configure each application and register it to the publisher
    for cfgfile in args:
        # Read the configuraton file of the application
        (cfgfile, app, dist, aconf) = util.read_application(cfgfile, parser.error)
        
        if watcher:
            watcher.watch_file(aconf.filename)
        
        # Create the function to get the static contents of the application
        static = aconf['application'].get('static')
        get_file = None
        if static is not None:
            # If a ``static`` parameter exists, under the ``[application]`` section,
            # serve the static contents from this root
            if os.path.isdir(static):
                get_file = lambda path, static=static: get_file_from_root(static, path)
        else:
            # Else, serve the static contenants from the ``static`` directory
            # of the application package
            if dist is not None:
                get_file = lambda path, requirement=pkg_resources.Requirement.parse(dist.project_name): get_file_from_package(requirement, path)

        app = wsgi.create_WSGIApp(app)

        # Activate the database metadata
        for (section, content) in aconf['database'].items():
            if isinstance(content, configobj.Section):
                db.set_metadata(content, content['debug'])
                del aconf['database'][section]

        db.set_metadata(aconf['database'], aconf['database']['debug'])

        # Register the application to the publisher
        p.register_application(
                               aconf['application']['path'],
                               aconf['application']['name'],
                               app,
                               options.debug or aconf['application']['debug']
                              )

        # Register the function to serve the static contents of the application
        static_url = p.register_static(aconf['application']['name'], get_file)
        
        # Configure the application
        app.set_config(cfgfile, aconf, parser.error, static_url, p)

    # Register the function to serve the static contents of the framework
    p.register_static('nagare', lambda path, r=pkg_resources.Requirement.parse('nagare'): get_file_from_package(r, path))

    # Launch all the applications
    p.serve(options.conf, pconf['publisher'], parser.error)

# ---------------------------------------------------------------------------

class Serve(util.Command):
    desc = 'Launch an application'

    set_options = staticmethod(set_options)
    run = staticmethod(run)
