#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The HTTP multi-threaded publisher"""

import time

from paste import httpserver

from nagare import local
from nagare.publishers import common

class Publisher(common.Publisher):
    """The HTTP publisher"""

    # Possible configuration options
    # ------------------------------

    server_spec = dict(
                        host='string(default=None)', port='integer(default=None)',
                        server_version='string(default=None)', protocol_version='string(default=None)',
                        daemon_threads='boolean(default=None)',
                        socket_timeout='integer(default=None)',
                        use_threadpool='boolean(default=None)', threadpool_workers='integer(default=None)'
                      )

    threadpool_spec = dict(
                            max_requests='integer(default=None)', # threads are killed after this many requests
                            hung_thread_limit='integer(default=None)', # when a thread is marked "hung"
                            kill_thread_limit='integer(default=None)', # when you kill that hung thread
                            dying_limit='integer(default=None)', # seconds that a kill should take to go into effect (longer than this and the thread is a "zombie")
                            spawn_if_under='integer(default=None)', # spawn if there's too many hung threads
                            max_zombie_threads_before_die='integer(default=None)', # when to give up on the process
                            hung_check_period='integer(default=None)' # every 100 requests check for hung workers
                          )

    spec = server_spec.copy()
    spec.update(threadpool_spec)

    def __init__(self):
        """Initialization
        """
        super(Publisher, self).__init__()

        local.worker = local.Thread()
        local.request = local.Thread()

    def serve(self, filename, conf, error):
        """Run the publisher

        In:
          - ``filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        (host, port, conf) = self._validate_conf(filename, conf, error)

        # The publisher is a threaded server so call only once the ``on_new_process()`` method
        self.on_new_process()
        print time.strftime('%x %X -', time.localtime()),

        server_options = dict([(k, v) for (k, v) in conf.items() if k in self.server_spec])
        threadpool_options = dict([(k, v) for (k, v) in conf.items() if k in self.threadpool_spec])

        httpserver.serve(self.urls, host, port, threadpool_options=threadpool_options, **server_options)
