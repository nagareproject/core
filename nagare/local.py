#--
# Copyright (c) 2008, 2009, 2010 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Scoped objects

Currently only for objects scoped to a request
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

request = None
