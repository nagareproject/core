#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Base class of all the publishers"""

import random

from paste import fileapp, httpexceptions, urlmap
import configobj

from nagare import config

try:
    from weberror.evalexception import EvalException
    
    debugged_app = lambda app: EvalException(app, xmlhttp_key='_a')
except ImportError:
    debugged_app = lambda app: app


def serve_file(filename):
    """Create a WSGI application that return a static file
    
    In:
      - ``filename`` -- path of the file to serve
      
    Return:
      - a WSGI application
    """
    if filename is None:
        return httpexceptions.HTTPNotFound()
    
    return fileapp.FileApp(filename)


class Publisher(object):
    """Base class of all the publishers"""
    
    default_port = 8080     # Port to listen to
    spec = {}               # Command line options

    def __init__(self, session_factory):
        """Initialisation
        
        In:
          - ``session_factory`` -- the sessions manager
        """
        self.urls = urlmap.URLMap() # Dispatch for all the registered applications
        self.apps = {}  # List of all the registered applications
        self.session_factory = session_factory

    def register_application(self, app_name, name, app, debug):
        """Register an application to launch
        
        In:
          - ``app_name`` -- name of the application
          - ``name`` -- url of the application
          - ``app`` -- the WSGI application
          - ``debug`` -- activation of the web error page
        """
        self.apps[app] = (app_name, name)
        
        if debug:
            app = debugged_app(app)

        self.urls['/'+name] = app
        print "Application '%s' registered as '/%s'" % (app_name, name)

    def register_static(self, name, get_file):
        """Register a WSGI application to serve static contents
        
        In:
          - ``name`` -- the URL of the contents will be prefix by ``/static/<name>/``
          - ``get_file`` -- function that will received the URL of the static content
            and will return its filename
            
        Return:
          - URL prefix (``/static/<name>/``)
        """
        self.urls['/static/'+name] = lambda environ, start_response: serve_file(get_file(environ['PATH_INFO']))(environ, start_response)

        return '/static/'+name+'/'

    def _validate_conf(self, filename, conf, error):
        """Validate the configuration read from the publisher configuration file
        
        In:
          -  ``filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
          
        Return:
          - the tuple:

            - hostname to listen to
            - port to listen to
            - conf object
        """
        conf = dict([(k, v) for (k, v) in conf.items() if k in self.spec])
        conf = configobj.ConfigObj(conf, configspec=self.spec, interpolation='Template')
        config.validate(filename, conf, error)
        conf = dict([(k, v) for (k, v) in conf.items() if v is not None])
        
        return (conf.pop('host'), conf.pop('port'), conf)

    def on_new_process(self):
        """The publisher has started a new process
        """
        random.seed(None)

        for app in self.apps:
            # Initialize each registered application of this new process
            # with a dedicated sessions manager
            app.start(self.session_factory())
            
    def serve(self, filename, conf, error):
        """Run the publisher
        
        In:
          -  ``filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors          
        """
        pass
