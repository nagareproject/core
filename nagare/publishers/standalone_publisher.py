#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The HTTP publisher"""

from paste import httpserver

from nagare.publishers import common

class Publisher(common.Publisher):
    """The HTTP publisher"""
    
    # Possible command line options with the default values
    # ------------------------------------------------------
    
    spec = dict(host='string(default=None)', port='integer(default=None)', server_version='string(default=None)',
                protocol_version='string(default=None)', daemon_threads='boolean(default=None)',
                socket_timeout='integer(default=None)', use_threadpool='boolean(default=None)',
                threadpool_workers='integer(default=None)')
    
    def serve(self, filename, conf, error):
        """Run the publisher
        
        In:
          -  ``filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors          
        """
        (host, port, conf) = self._validate_conf(filename, conf, error)
        
        # The puslisher is a threaded server so call once the ``on_new_process()`` method
        self.on_new_process()
        httpserver.serve(self.urls, host, port, **conf)
