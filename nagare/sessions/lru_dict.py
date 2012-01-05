#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""A LRU dictionary is a dictionary with a fixed maximum number of keys.

When this maximum is reached, the last recently used key is deleted when a new
key is added.
"""

from __future__ import with_statement

import threading

class LRUDict(object):
    """A LRU dictionary is a dictionary with a fixed maximum number of keys"""

    def __init__(self, size):
        """Initialization

        In:
          -  ``size`` -- maximum number of keys
        """
        self.size = size

        self.oldest = self.newest = 0 # Age of the oldest key / age of the last recently used key
        self.age_to_items = {}        # Dict: key_age -> key
        self.items = {}               # Dict: key -> (key_age, value)

    def __contains__(self, k):
        """Test if a key exists into this dictionary

        In:
          -  ``k`` -- the key

        Return:
          - a boolean
        """
        return k in self.items

    def _set_newest(self, k, o):
        """Insert a key as the last recently used

        In:
           - ``k`` -- the key
           -- ``o`` -- the value
        """
        self.age_to_items[self.newest] = k
        self.items[k] = (self.newest, o)
        self.newest += 1

    def __getitem__(self, k):
        """Return the value of a key.

        The key becomes the most recently used key.

        In:
          - ``k`` -- the key

        Return:
          - the value
        """
        (age, item) = self.items[k]
        del self.age_to_items[age]

        self._set_newest(k, item)
        return item

    def __setitem__(self, k, o):
        """Set the value of a key.

        The key becomes the most recently used key.

        In:
          - ``k`` -- the key
          - ``o`` -- the value
        """
        try:
            (age, item) = self.items[k]
            del self.age_to_items[age]
        except KeyError:
            pass

        self._set_newest(k, o)

        if len(self.items) > self.size:
            # Maximum number of keys reached
            # Delete the last recently used key
            while not self.oldest in self.age_to_items:
                self.oldest += 1

            del self.items[self.age_to_items.pop(self.oldest)]

    def __delitem__(self, k):
        """Delete a key.

        In:
          - ``k`` -- the key
        """
        (age, item) = self.items.pop(k)
        del self.age_to_items[age]

    def debug(self):
        print self.oldest, self.newest, self.age_to_items, self.items


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
            return k in self.items

    def __getitem__(self, k):
        with self.lock:
            return super(ThreadSafeLRUDict, self).__getitem__(k)

    def __setitem__(self, k, o):
        with self.lock:
            super(ThreadSafeLRUDict, self).__setitem__(k, o)

# ----------------------------------------------------------------------------

if __name__ == '__main__':
    cache = ThreadSafeLRUDict(3)
    cache['a'] = 1
    cache.debug()
    cache['b'] = 2
    cache.debug()
    cache['a'] = 3
    cache.debug()
    cache['a'] = 4
    cache.debug()
    cache['b'] = 5
    cache.debug()
    x = cache['a']
    cache.debug()

    cache['c'] = 'c'
    cache.debug()

    cache['d'] = 'd'
    cache.debug()

    cache['b'] = 'b'
    cache.debug()

    cache['e'] = 'e'
    cache.debug()
