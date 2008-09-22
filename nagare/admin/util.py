#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Various tools used be the directive commands"""

import sys, os

import pkg_resources
import configobj

from nagare import config

# ---------------------------------------------------------------------------

class Command:
    """The base class of all the administration directives"""
    desc = ''

    @classmethod
    def set_options(cls, parser):
        pass

    @classmethod
    def run(cls, options, args):
        pass

# ---------------------------------------------------------------------------

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

    return (entry_point.load(), entry_point.dist)


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
    return (dist.get_entry_info('nagare.applications', app).load(), dist)


def load_file(filename, app):
    """Load an object from a file
    
    In:
      - ``filename`` -- name of the file
      - ``app`` -- name of the object to load
      
    Return:
      - (the object, None)
    """
    dir = os.path.abspath(os.path.dirname(filename))
    if dir not in sys.path:
        sys.path.insert(0, dir)

    name = os.path.splitext(os.path.basename(filename))[0]
    return load_module(name, app)


def load_module(module, app):
    """Load an object from a module
    
    In:
      - ``module`` -- name of the module
      - ``app`` -- name of the object to load
      
    Return:
      - (the object, None)
    """
    r = __import__(module, fromlist=('',))

    if app is not None:
        r = getattr(r, app)
    
    return (r, None)    

loaders = {
            '' : load_module,
            'python' : load_module,
            'egg' : load_egg,
            'file' : load_file,
            'app' : load_app
          }

def load_object(path):
    """Load an object from a path
    
    The possible path syntaxes are:
    
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
      
    Return:
      - a tuple (object loaded, distribution where this object is located or None)
    """
    if ' ' in path:
        scheme, path = path.split(' ', 1)
    else:
        scheme = ''
        
    if ':' in path:
        (path, o) = path.split(':', 1)
    else:
        o = None
        
    return loaders[scheme](path, o)

# ---------------------------------------------------------------------------

# The default application configuration
# -------------------------------------

application_options_spec = {
    'application' : dict(
        path = 'string()',              # Where to find the application object (for ``load_object()``) ?
        name = 'string()',              # URL for the application
        debug = 'boolean(default=False)',   # Debug web page activated ?
                        
        redirect_after_post = 'boolean(default=False)',  # Follow the PRG pattern ?
        always_html = 'boolean(default=True)' # Don't generate xhtml, even if its a browser capability ?
    ),
    'database' : dict(
        activated = 'boolean(default=False)',   # Activate the database engine ?
        uri = 'string(default="")', # Database connection string
        metadata = 'string(default="")',    # Database metadata : database entities description
        populate = 'string(default="")', # Method to call after the database tables creation
        debug = 'boolean(default=False)', # Set the database engine in debug mode ?
        __many__ = dict(    # Database sub-sections
            activated = 'boolean(default=False)',
            populate = 'string(default="")'
        )
    )
}
    
def read_application_options(cfgfile, error, default={}):
    """Read the configuration file for the application
    
    In:
      - ``cfgfile`` -- path to an application configuration file
      - ``error`` -- the function to call in case of configuration errors
      - ``default`` -- optional default values      
      
    Return:
      - a ConfigObj with the application parameters    
    """    
    spec = configobj.ConfigObj(default)
    spec.merge(application_options_spec)
    
    conf = configobj.ConfigObj(cfgfile, configspec=spec, interpolation='Template' if default else None)    
    config.validate(cfgfile, conf, error)
    
    # The database sub-sections inherit from the database section
    spec['database']['__many__'].merge(dict(
                            uri = 'string(default=%s)' % str(conf['database']['uri']),
                            metadata = 'string(default=%s)' % str(conf['database']['metadata']),
                            debug = 'boolean(default=%s)' % str(conf['database']['debug']),
                           ))
    conf = configobj.ConfigObj(cfgfile, configspec=spec, interpolation='Template' if default else None)
    config.validate(cfgfile, conf, error)
    
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
        - a ConfigObj with the application parameters
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
        cfgfile = pkg_resources.resource_filename(requirement, os.path.join('conf', cfgfile+'.cfg'))
    
    # Read the application configuration
    aconf = read_application_options(cfgfile, error)

    # From the path of the application, create the application object
    (app, dist) = load_object(aconf['application']['path'])
    
    defaults = dict(here='string(default="%s")' % os.path.abspath(os.path.dirname(cfgfile)))
    if dist is not None:
        defaults['root'] = 'string(default="%s")' % dist.location

    # Re-read the application configuration, with some substitution variables
    aconf = read_application_options(cfgfile, error, defaults)
    
    return (cfgfile, app, dist, aconf)
