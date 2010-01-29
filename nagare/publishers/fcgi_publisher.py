#--
# Copyright (c) 2008, 2009, 2010 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The FastCGI publisher"""

import time
from flup.server import fcgi_fork

from nagare.publishers import common

class Publisher(common.Publisher, fcgi_fork.WSGIServer):
    """The FastCGI publisher"""

    default_port = 9000 # Default FastCGI port

    # Possible command line options with the default values
    # ------------------------------------------------------

    spec = dict(
                host='string(default=None)', port='integer(default=9000)',
                multiplexed='boolean(default=None)', minSpare='integer(default=None)',
                maxSpare='integer(default=None)', maxChildren='integer(default=None)',
                maxRequests='integer(default=None)',
               )

    def _sanitizeEnv(self, environ):
        super(Publisher, self)._sanitizeEnv(environ)
        environ['SCRIPT_NAME'] = ''

    def _child(self, sock, parent):
        """A new process is created

        In:
          - ``sock`` -- the inherited socket
          - ``parent`` -- the parent process
        """
        # Call each time the ``on_new_process()`` method
        self.on_new_process()
        super(Publisher, self)._child(sock, parent)

    def register_static(self, name, get_file):
        """Register a WSGI application to serve static contents

        In:
          - ``name`` -- the URL of the contents will be prefix by ``/static/<name>/``
          - ``get_file`` -- function that will received the URL of the static content
            and will return its filename

        Return:
          - URL prefix (``/static/<name>/``)

        .. warning::
           **Dummy method**

           The front HTTP server must be configurated to serve the static contents

           (you can use the administrative command ``nagare-admin create-rules`` to generate
           the rewrite rules if you are using the lighttpd or nginx servers)
        """
        return '/static/'+name+'/'

    def serve(self, filename, conf, error):
        """Run the publisher

        In:
          -  ``filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        (host, port, conf) = self._validate_conf(filename, conf, error)

        fcgi_fork.WSGIServer.__init__(self, self.urls, bindAddress=(host, port), debug=False, **conf)
        print time.strftime('%x %X -', time.localtime()), 'serving on fastcgi://%s:%d' % (host, port)
        self.run()
