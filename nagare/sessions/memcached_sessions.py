#--
# Copyright (c) 2008, 2009 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import threading, time

import memcache

from nagare.sessions import common

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
    """Sessions manager for sessions kept in an external memcache server
    """
    def __init__(
                 self,
                 host='127.0.0.1', port=11211,
                 ttl=0,
                 lock_ttl=0, lock_poll_time=0.1, lock_max_wait_time=5,
                 min_compress_len=0,
                 reset=True,
                 debug=True
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
        self.host = '%s:%d' % (host, port)
        self.ttl = ttl
        self.lock_ttl = lock_ttl
        self.lock_poll_time = lock_poll_time
        self.lock_max_wait_time = lock_max_wait_time
        self.min_compress_len = min_compress_len
        self.debug = debug
        self.memcached = threading.local()

    def _get_connection(self):
        """Get the connection to the memcache server
        
        Return:
          - the connection
        """
        # The connection objects are thread local
        connection = self.memcached.__dict__.get('connection')
        
        if connection is None:
            connection = memcache.Client([self.host], debug=self.debug)
            self.memcached.connection = connection
            
        return connection
            
    def _create(self, session_id, secure_id):
        """Create a new session
        
        In:
          - ``session_id`` -- id of the session
          - ``secure_id`` -- the secure number associated to the session
          
        Return:
          - tuple (session_id, cont_id, new_cont_id, lock, secure_id)
        """
        connection = self._get_connection()
        lock = Lock(connection, session_id, self.lock_ttl, self.lock_poll_time, self.lock_max_wait_time)
        lock.acquire()
        
        connection.set_multi({
            '_sess' : (secure_id, None),
            '_cont' : '0',
            '00000' : {}
        }, self.ttl, KEY_PREFIX+session_id, self.min_compress_len)
        
        return (session_id, 0, 0, lock, secure_id)
    
    def __get(self, session_id, cont_id):
        """Return the raw data associated to a session
        
        In:
          - ``session_id`` -- id of the session
          - ``cont_id`` -- id of the continuation
          
        Return:
            - tuple (session_id, cont_id, last_cont_id, lock, secure_id, externals, data)        
        """        
        connection = self._get_connection()
        lock = Lock(connection, session_id, self.lock_ttl, self.lock_poll_time, self.lock_max_wait_time)
        lock.acquire()

        id = cont_id.zfill(5)
        session = connection.get_multi(('_sess', '_cont', id), KEY_PREFIX+session_id)

        if len(session) != 3:
            raise common.ExpirationError()

        last_cont_id = int(session['_cont'])
        (secure_id, externals) = session['_sess']
        data = session[id]

        return (session_id, int(cont_id), last_cont_id, lock, secure_id, externals, data)
    
    def __set(self, session_id, cont_id, secure_id, inc_cont_id, externals, data):
        """Memorize the session data
        
        In:
          - ``session_id`` -- id of the current session
          - ``cont_id`` -- id of the current continuation
          - ``secure_id`` -- the secure number associated to the session           
          - ``inc_cont_id`` -- is the continuation id to increment ? 
          - ``externals`` -- pickle of shared objects across the continuations                    
          - ``data`` -- pickle of the objects in the continuation
        """
        if inc_cont_id:
            self._get_connection().incr(KEY_PREFIX+session_id+'_cont')
        
        self._get_connection().set_multi({
            '_sess' : (secure_id, externals),
            '%05d' % cont_id : data
        }, self.ttl, KEY_PREFIX+session_id, self.min_compress_len)
        
        
    def _delete(self, session_id):
        """Delete the session
        
        In:
          - ``session_id`` -- id of the session to delete
        """
        self._get_connection().delete(KEY_PREFIX+session_id)
 
 
class SessionsFactory(common.SessionsFactory):
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
    sessions = Sessions

    def __init__(self, filename, conf, error):
        super(SessionsFactory, self).__init__(filename, conf, error)

        if self.conf['reset']:
            memcached = memcache.Client(['%s:%d' % (self.conf['host'], self.conf['port'])], debug=self.conf['debug'])
            memcached.flush_all()
