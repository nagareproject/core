#--
# Copyright (c) 2008, 2009 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The FAPWS3__  publisher

__ http://william-os4y.livejournal.com/
"""

"""
import fapws._evwsgi as evwsgi
from fapws import base
"""

from nagare.publishers import common

import sys, logging
from nagare.publishers import socketlibevent

#import stacklesswsgi

"""
from concurrence import dispatch
from concurrence.protocol.http.server import WSGIServer
"""

class Publisher(common.Publisher):
    """The FAPWS3 publisher"""

    # Possible command line options with the default values
    # ------------------------------------------------------
    
    spec = dict(host='string(default=None)', port='integer(default=None)')

    def go(self,host, port):
        WSGIServer(self.urls).serve((host, port))

    def serve(self, filename, conf, error):
        """Run the publisher
        
        In:
          -  ``filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors          
        """
        (host, port, conf) = self._validate_conf(filename, conf, error)
        
        # The puslisher is an events based server so call once the ``on_new_process()`` method
        self.on_new_process()

        """
        evwsgi.start(host, port)
        evwsgi.set_base_module(base)
        evwsgi.wsgi_cb(('', self.urls))
        evwsgi.run()
        """
        
        """
        stacklesswsgi.Server((host, port), self.urls).start()
        """
        
        """
        dispatch(lambda: self.go(host, port))
        """
        
        socketlibevent.WSGIServer(self.urls, (host, port)).run()
