# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Various tools used be the administrative commands"""

import os

import pkg_resources
import configobj

from nagare.admin import reference
from nagare import wsgi, config

# The default application configuration
# -------------------------------------

application_options_spec = {
    'application': dict(
        path='string()',  # Where to find the application object (see ``load_object()``) ?
        name='string()',  # URL for the application
        debug='boolean(default=False)',  # Debug web page activated ?

        redirect_after_post='boolean(default=False)',  # Follow the PRG pattern ?
        always_html='boolean(default=True)',  # Don't generate xhtml, even if it's a browser capability ?
        wsgi_pipe='string(default="")',  # Method to create the WSGI middlewares pipe
        static='string(default="$root/static")'  # Default directory of the static files
    ),

    'database': dict(
        activated='boolean(default=False)',  # Activate the database engine ?
        uri='string(default="")',  # Database connection string
        metadata='string(default="")',  # Database metadata : database entities description
        populate='string(default="")',  # Method to call after the database tables creation
        debug='boolean(default=False)',  # Set the database engine in debug mode ?
        __many__=dict(  # Database sub-sections
            activated='boolean(default=False)',
            populate='string(default="")'
        )
    ),

    'logging': dict()
}


def read_application_options(cfgfile, error, default={}):
    """Read the configuration file for the application

    In:
      - ``cfgfile`` -- path to an application configuration file
      - ``error`` -- the function to call in case of configuration errors
      - ``default`` -- optional default values

    Return:
      - a ``ConfigObj`` of the application parameters
    """
    if default:
        default['name'] = 'string(default="%s")' % configobj.ConfigObj(cfgfile)['application']['name']

    spec = configobj.ConfigObj(default)
    spec.merge(application_options_spec)

    choices = ', '. join(['"%s"' % entry.name for entry in pkg_resources.iter_entry_points('nagare.sessions')])
    spec.merge({'sessions': {'type': 'option(%s, default="")' % (choices + ', ""')}})

    conf = configobj.ConfigObj(cfgfile, configspec=spec, interpolation='Template' if default else None)
    config.validate(cfgfile, conf, error)

    # The database sub-sections inherit from the database section
    spec['database']['__many__'].merge(dict(
        uri='string(default=%s)' % str(conf['database']['uri']),
        metadata='string(default=%s)' % str(conf['database']['metadata']),
        debug='boolean(default=%s)' % str(conf['database']['debug']),
    ))
    conf = configobj.ConfigObj(cfgfile, configspec=spec, interpolation='Template' if default else None)
    config.validate(cfgfile, conf, error)

    if not conf['sessions']['type']:
        del conf['sessions']['type']

    return conf


def read_application(cfgfile, error):
    """Read the configuration file for the application and create the application object

    In:
      - ``cfgfile`` -- name of a registered application or path to an application configuration file
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - a tuple:

        - name of the application configuration file
        - the application object
        - the distribution of the application
        - a ``ConfigObj`` of the application parameters
    """
    if not os.path.isfile(cfgfile):
        # The name of a registered application is given, find its configuration file

        # Get all the registered applications
        apps = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.applications')])

        # Get the application
        app = apps.get(cfgfile)
        if app is None:
            error("application '%s' not found (use 'nagare-admin serve' to see the available applications)" % cfgfile)

        # From the directory of the application, get its configuration file
        requirement = pkg_resources.Requirement.parse(app.dist.project_name)
        cfgfile = pkg_resources.resource_filename(requirement, os.path.join('conf', cfgfile + '.cfg'))

    # Read the application configuration file
    aconf = read_application_options(cfgfile, error)

    # From the path of the application, create the application object
    (app, dist) = reference.load_object(aconf['application']['path'])

    here = os.path.abspath(os.path.dirname(cfgfile))
    root = os.path.abspath(os.path.join(here, '..')) if dist is None else dist.location

    defaults = {
        'here': 'string(default="%s")' % here,
        'root': 'string(default="%s")' % root
    }

    # Re-read the application configuration, with some substitution variables
    aconf = read_application_options(cfgfile, error, defaults)

    return cfgfile, app, dist, aconf


# ---------------------------------------------------------------------------

def get_database(conf, debug):
    """Read the database settings

    The location of the metadata object is read from the configuration file

    In:
      - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
      - ``debug`` -- debug mode for the database engine

    Return:
      - the tuple:
        - metadata object
        - database uri
        - database debug mode
        - database engines settings
    """
    metadata = conf.get('metadata')

    if not conf['activated'] or not metadata:
        return None

    # Import the metadata object
    metadata = reference.load_object(metadata)[0]

    # All the parameters, of the [database] section, with an unknown name are
    # given to the database engine
    engine_conf = dict([(k, v) for (k, v) in conf.items() if k not in ('uri', 'activated', 'metadata', 'debug', 'populate')])

    return metadata, conf['uri'], debug, engine_conf


def activate_WSGIApp(
    app,
    cfgfile, aconf, error,
    project_name='',
    static_path=None, static_url=None,
    data_path=None,
    publisher=None, sessions_manager=None,
    debug=False
):
    """Set all the properties of a WSGIApp application

    In:
      - ``app`` -- the WSGIApp application or the application root object factory
      - ``cfgfile`` -- the path to the configuration file
      - ``aconf`` -- the ``ConfigObj`` object, created from the configuration file
      - ``error`` -- the function to call in case of configuration errors
      - ``project_name`` -- name of the distutils distribution where the app is located
      - ``static_path`` -- the directory where the static contents of the application
        are located
      - ``static_url`` -- the url of the static contents of the application
      - ``data_path`` -- the directory where the data of the application are located
      - ``publisher`` -- the publisher of the application
      - ``session_manager`` -- the sessions manager
      - ``debug`` -- flag to display the generated SQL statements

    Return:
      - a tuple:
          - the ``wsgi.WSGIApp`` object
          - tuples (application databases settings, application databases populate functions)
    """
    databases = []
    populates = []
    # Get all the databases settings
    for (section, content) in aconf['database'].items():
        if isinstance(content, configobj.Section):
            database = get_database(content, content['debug'] or debug)
            if database:
                databases.append(database)
                populates.append(content['populate'])
            del aconf['database'][section]

    database = get_database(aconf['database'], aconf['database']['debug'] or debug)
    if database:
        databases.append(database)
        populates.append(aconf['database']['populate'])

    app = wsgi.create_WSGIApp(app)

    app.set_config(cfgfile, aconf, error)

    if static_path is not None:
        app.set_static_path(static_path)

    if static_url is not None:
        app.set_static_url(static_url)

    if data_path is not None:
        app.set_data_path(data_path)

    if publisher:
        app.set_publisher(publisher)

    if sessions_manager:
        app.set_sessions_manager(sessions_manager)

    if databases:
        app.set_databases(databases)

    if project_name:
        app.set_project(project_name)

    return app, zip(databases, populates)
