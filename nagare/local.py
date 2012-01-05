#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Scoped objects

Currently:

  - objects scoped to a worker, a handler of a request
  - objects scoped to a request (i.e a scoped cleared on each new request)
"""

import threading

class Thread(threading.local):
    """Objects with attributs scoped to the current thread
    """
    def clear(self):
        self.__dict__.clear()

    def create_lock(self):
        return threading.Lock()


class DummyLock(object):
    acquire = release = lambda self: None


class Process(object):
    """Objects with attributs scoped to the current thread
    """
    def clear(self):
        self.__dict__.clear()

    def create_lock(self):
        return DummyLock()

# ----------------------------------------------------------------------------

worker = None
request = None
