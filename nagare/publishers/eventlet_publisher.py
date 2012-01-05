#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The eventlet__ publisher

__ http://wiki.secondlife.com/wiki/Eventlet
"""

from eventlet import api, wsgi

from nagare.publishers import common

class Publisher(common.Publisher):
    """The eventlet publisher"""

    # Possible command line options with the default values
    # ------------------------------------------------------

    spec = dict(host='string(default=None)', port='integer(default=None)')

    def serve(self, filename, conf, error):
        """Run the publisher

        In:
          -  ``filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        (host, port, conf) = self._validate_conf(filename, conf, error)

        # The publisher is an events based server so call once the ``on_new_process()`` method
        self.on_new_process()

        wsgi.server(api.tcp_listener((host, port)), self.urls)
