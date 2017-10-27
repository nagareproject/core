# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""A LRU dictionary is a dictionary with a fixed maximum number of keys.

When this maximum is reached, the last recently used key is deleted when a new
key is added.
"""

import threading

from collections import OrderedDict


class LRUDict(object):
    """A LRU dictionary is a dictionary with a fixed maximum number of keys"""

    def __init__(self, size):
        """Initialization

        In:
          -  ``size`` -- maximum number of keys
        """
        self.size = size
        self.items = OrderedDict()

    def __contains__(self, k):
        """Test if a key exists into this dictionary

        In:
          -  ``k`` -- the key

        Return:
          - a boolean
        """
        return k in self.items

    def __getitem__(self, k):
        """Return the value of a key.

        The key becomes the most recently used key.

        In:
          - ``k`` -- the key

        Return:
          - the value
        """
        v = self.items.pop(k)
        self.items[k] = v

        return v

    def __setitem__(self, k, v):
        """Insert a key as the last recently used

        In:
           - ``k`` -- the key
           - ``v`` -- the value
        """
        self.items.pop(k, None)
        self.items[k] = v

        if len(self.items) > self.size:
            self.items.popitem(False)

    def __delitem__(self, k):
        """Delete a key.

        In:
          - ``k`` -- the key
        """
        del self.items[k]

    def __repr__(self):
        return repr(self.items)


class ThreadSafeLRUDict(LRUDict):
    """Tread safe version of a LRU dictionary"""

    def __init__(self, *args, **kw):
        super(ThreadSafeLRUDict, self).__init__(*args, **kw)
        self.lock = threading.RLock()

    def __contains__(self, k):
        """Test if a key exists into this dictionary

        In:
          -  ``k`` -- the key

        Return:
          - a boolean
        """
        with self.lock:
            return super(ThreadSafeLRUDict, self).__contains__(k)

    def __getitem__(self, k):
        with self.lock:
            return super(ThreadSafeLRUDict, self).__getitem__(k)

    def __setitem__(self, k, v):
        with self.lock:
            super(ThreadSafeLRUDict, self).__setitem__(k, v)

    def __delitem__(self, k):
        with self.lock:
            super(ThreadSafeLRUDict, self).__delitem__(k)


# ----------------------------------------------------------------------------

if __name__ == '__main__':
    cache = ThreadSafeLRUDict(3)
    cache['a'] = 1
    print cache
    cache['b'] = 2
    print cache
    cache['a'] = 3
    print cache
    cache['a'] = 4
    print cache
    cache['b'] = 5
    print cache
    x = cache['a']
    print cache

    cache['c'] = 'c'
    print cache

    cache['d'] = 'd'
    print cache

    cache['b'] = 'b'
    print cache

    cache['e'] = 'e'
    print cache
