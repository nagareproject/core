#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""This is the admin application. By default, when launched, it's mapped to url
``/admin`` and ``/``.

The default view of this application is the administration view
of the framework. 
"""

from __future__ import with_statement

import operator

import pkg_resources
import configobj

from nagare import component, presentation, wsgi, config

class Admin(object):
    """The root component of the admin application
    
    It loads all the components registered under the ``nagare.admin`` entry point and renders them
    into its view.
    """
    def __init__(self, apps):
        """Load the components registered under the ``nagare.admin`` entry point
        
        In:
          - ``apps`` -- list of all the applications launched
        """
        # Load the components
        self.components = [entry.load()(apps) for entry in pkg_resources.iter_entry_points('nagare.admin')]
        
        # Sort them according to their ``priority`` attribut
        self.components.sort(key=operator.attrgetter('priority'))

@presentation.render_for(Admin)
def render(self, h, *args):
    """Aggregates all the default views of the components"""
    
    h.head.css_url('/static/nagare/application.css')    
    h.head << h.head.title('Nagare Administration interface')

    with h.div(class_='mybody', style='line-heught: 0px'):

        with h.div(id='myheader'):
            h << h.a(h.img(src='/static/nagare/img/logo.gif'), id='logo', href='http://www.nagare.org/', title='Nagare home')
            h << h.span('Administration interface', id='title')

        with h.div(id='main'):        
            h << [component.Component(c) for c in self.components]
            h << h.div(u'\N{Copyright Sign} ', h.a('Net-ng', href='http://www.net-ng.com'), u'\N{no-break space}', align='right')
        
    h << h.div(' ', class_='footer')
        
    return h.root

# -------------------------------------------e--------------------------------

application_spec = { 'application' : { 'as_root' : 'boolean(default=True)' } }

class WSGIApp(wsgi.WSGIApp):
    """The admin application
    
    Read the additional boolean parameter ``as_root`` into the ``[application]`` section.
    If ``True``, mappes itself to the ``/`` url.
    """

    def set_config(self, config_filename, conf, error, static, publisher):
        """Read the value of the ``as_root`` parameter and keeps the list of all
        the launched applications
        
        In:
          -  ``config_filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
          - ``static`` -- the directory where the static contents of the application
            are located
          - ``publisher`` -- the publisher of the application
        """
        conf = configobj.ConfigObj(conf, configspec=configobj.ConfigObj(application_spec))
        config.validate(config_filename, conf, error)

        if conf['application']['as_root']:
            publisher.register_application(conf['application']['path'], '', self, False)
        
        super(WSGIApp, self).set_config(config_filename, conf, error, static, publisher)
        self.apps = publisher.apps
        
    def create_root(self):
        """
        Create an ``admin`` object
        
        Return:
          - the admin object
        """
        # Create the ``admin`` object with the list of all the launched application
        return self.root_factory(self.apps)
    
# -------------------------------------------e--------------------------------

# The admin application singleton.
# The given factory creates a component from a ``admin`` object    
app = WSGIApp(lambda apps: component.Component(Admin(apps)))
