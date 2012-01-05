#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import time

import memcache

from nagare import local
from nagare.sessions import ExpirationError, common

KEY_PREFIX = 'nagare_'

class Lock(object):
    def __init__(self, connection, lock_id, ttl, poll_time, max_wait_time):
        """Distributed lock in memcache

        In:
          - ``connection`` -- connection object to the memcache server
          - ``lock_id`` -- unique lock identifier
          - ``ttl`` -- session locks timeout, in seconds (0 = no timeout)
          - ``poll_time`` -- wait time between two lock acquisition tries, in seconds
          - ``max_wait_time`` -- maximum time to wait to acquire the lock, in seconds
        """
        self.connection = connection
        self.lock = '%slock_%s' % (KEY_PREFIX, lock_id)
        self.ttl = ttl
        self.poll_time = poll_time
        self.max_wait_time = max_wait_time

    def acquire(self):
        """Acquire the lock
        """
        t0 = time.time()
        while not self.connection.add(self.lock, 1, self.ttl) and (time.time() < (t0+self.max_wait_time)):
            time.sleep(self.poll_time)

    def release(self):
        """Release the lock
        """
        self.connection.delete(self.lock)


class Sessions(common.Sessions):
    """Sessions manager for sessions kept in an external memcached server
    """
    spec = dict(
                host='string(default="127.0.0.1")',
                port='integer(default=11211)',
                ttl='integer(default=0)',
                lock_ttl='float(default=0.)',
                lock_poll_time='float(default=0.1)',
                lock_max_wait_time='float(default=5.)',
                min_compress_len='integer(default=0)',
                reset='boolean(default=True)',
                debug='boolean(default=False)',
               )
    spec.update(common.Sessions.spec)

    def __init__(
                 self,
                 host='127.0.0.1', port=11211,
                 ttl=0,
                 lock_ttl=0, lock_poll_time=0.1, lock_max_wait_time=5,
                 min_compress_len=0,
                 reset=False,
                 debug=True,
                 **kw
                ):
        """Initialization

        In:
          - ``host`` -- address of the memcache server
          - ``port`` -- port of the memcache server
          - ``ttl`` -- sessions and continuations timeout, in seconds (0 = no timeout)
          - ``lock_ttl`` -- session locks timeout, in seconds (0 = no timeout)
          - ``lock_poll_time`` -- wait time between two lock acquisition tries, in seconds
          - ``lock_max_wait_time`` -- maximum time to wait to acquire the lock, in seconds
          - ``min_compress_len`` -- data longer than this value are sent compressed
          - ``reset`` -- do a reset of all the sessions on startup ?
          - ``debug`` -- display the memcache requests / responses
        """
        super(Sessions, self).__init__(**kw)

        self.host = ['%s:%d' % (host, port)]
        self.ttl = ttl
        self.lock_ttl = lock_ttl
        self.lock_poll_time = lock_poll_time
        self.lock_max_wait_time = lock_max_wait_time
        self.min_compress_len = min_compress_len
        self.debug = debug

        if reset:
            self.flush_all()

    def set_config(self, filename, conf, error):
        """Read the configuration parameters

        In:
          - ``filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        # Let's the super class validate the configuration file
        conf = super(Sessions, self).set_config(filename, conf, error)

        self.host = ['%s:%d' % (conf['host'], conf['port'])]

        for arg_name in (
                            'ttl', 'lock_ttl', 'lock_poll_time', 'lock_max_wait_time',
                            'min_compress_len', 'debug'
                          ):
            setattr(self, arg_name, conf[arg_name])

        if conf['reset']:
            self.flush_all()

    def _get_connection(self):
        """Get the connection to the memcache server

        Return:
          - the connection
        """
        # The connection objects are local to the workers
        connection = getattr(local.worker, 'memcached_connection', None)

        if connection is None:
            connection = memcache.Client(self.host, debug=self.debug)
            local.worker.memcached_connection = connection

        return connection

    def flush_all(self):
        """Delete all the contents in the memcached server
        """
        memcached = memcache.Client(self.host, debug=self.debug)
        memcached.flush_all()

    def _create(self, session_id, secure_id):
        """Create a new session

        In:
          - ``session_id`` -- id of the session
          - ``secure_id`` -- the secure number associated to the session

        Return:
          - the tuple:
            - id of this state,
            - session lock
        """
        connection = self._get_connection()
        lock = Lock(connection, session_id, self.lock_ttl, self.lock_poll_time, self.lock_max_wait_time)
        lock.acquire()

        connection.set_multi({
            '_sess' : (secure_id, None),
            '_state' : '0',
            '00000' : {}
        }, self.ttl, KEY_PREFIX+session_id, self.min_compress_len)

        return (0, lock)

    def _get(self, session_id, state_id, use_same_state):
        """Retrieve the state

        In:
          - ``session_id`` -- session id of this state
          - ``state_id`` -- id of this state
          - ``use_same_state`` -- is a copy of this state to create ?

        Return:
          - the tuple:
            - id of this state,
            - session lock,
            - secure number associated to the session,
            - data keept into the session
            - data keept into the state
        """
        connection = self._get_connection()
        lock = Lock(connection, session_id, self.lock_ttl, self.lock_poll_time, self.lock_max_wait_time)
        lock.acquire()

        state_id = state_id.zfill(5)
        session = connection.get_multi(('_sess', '_state', state_id), KEY_PREFIX+session_id)

        if len(session) != 3:
            raise ExpirationError()

        (secure_id, session_data) = session['_sess']
        last_state_id = int(session['_state'])
        state_data = session[state_id]

        if not use_same_state:
            state_id = last_state_id

        return (int(state_id), lock, secure_id, session_data, state_data)

    def _set(self, session_id, state_id, secure_id, use_same_state, session_data, state_data):
        """Store the state

        In:
          - ``session_id`` -- session id of this state
          - ``state_id`` -- id of this state
          - ``secure_id`` -- the secure number associated to the session
          - ``use_same_state`` -- is this state to be stored in the previous snapshot ?
          - ``session_data`` -- data keept into the session
          - ``state_data`` -- data keept into the state
        """
        if not use_same_state:
            self._get_connection().incr(KEY_PREFIX+session_id+'_state')

        self._get_connection().set_multi({
            '_sess' : (secure_id, session_data),
            '%05d' % state_id : state_data
        }, self.ttl, KEY_PREFIX+session_id, self.min_compress_len)


    def _delete(self, session_id):
        """Delete the session

        In:
          - ``session_id`` -- id of the session to delete
        """
        self._get_connection().delete(KEY_PREFIX+session_id)

    def serialize(self, data):
        """Pickle an objects graph

        In:
          - ``data`` -- the objects graphs

        Return:
          - the tuple:
            - data to keep into the session
            - data to keep into the state
        """
        return self.pickle(data)

    def deserialize(self, session_data, state_data):
        """Unpickle an objects graph

        In:
          - ``session_data`` -- data from the session
          - ``state_data`` -- data from the state

        Out:
          - the objects graph
        """
        return self.unpickle(session_data, state_data)
