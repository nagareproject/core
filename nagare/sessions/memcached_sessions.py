#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import threading

import memcache

from nagare.sessions import common

KEY_PREFIX = 'nagare_'

class Sessions(common.Sessions):
    def __init__(self, host='127.0.0.1', port=11211, ttl=0, reset=True, debug=True):
        self.host = '%s:%d' % (host, port)
        self.ttl = 0
        self.debug = debug
        self.memcached = threading.local()

    def _get_connection(self):
        connection = self.memcached.__dict__.get('connection')
        
        if connection is None:
            connection = memcache.Client([self.host], debug=self.debug)
            self.memcached.connection = connection
            
        return connection
            
    def _create_session(self, session_id):
        self._get_connection().set_multi({
            KEY_PREFIX+session_id : [None, None],
            KEY_PREFIX+session_id+'_cont' : '0',
            KEY_PREFIX+session_id+'00000' : {}
        })

    def _get(self, session_id, cont_id):
        id = session_id + '%05d' % cont_id
        
        session = self._get_connection().get_multi((
                      KEY_PREFIX+session_id,
                      KEY_PREFIX+session_id+'_cont',
                      KEY_PREFIX+id
        ))

        if len(session) != 3:
            return None
        
        last_cont_id = int(session[KEY_PREFIX+session_id+'_cont'])
        (query_string, externals) = session[KEY_PREFIX+session_id]
        cont = session[KEY_PREFIX+id]
        
        return (last_cont_id, query_string, externals, cont)
    
    def _set(self, session_id, cont_id, new_id, query_string, externals, data):
        if new_id:
            self._get_connection().incr(KEY_PREFIX+session_id+'_cont')
        
        self._get_connection().set_multi({
            KEY_PREFIX+session_id : (query_string, externals),
            KEY_PREFIX+session_id+'%05d' % cont_id : data
        }, self.ttl)
 
 
class SessionsFactory(common.SessionsFactory):
    spec = dict(
                host='string(default="127.0.0.1")',
                port='integer(default=11211)',
                ttl='integer(default=0)',
                reset='boolean(default=True)',
                debug='boolean(default=False)',
               )
    sessions = Sessions

    def __init__(self, filename, conf, error):
        super(SessionsFactory, self).__init__(filename, conf, error)

        if conf['reset']:
            memcached = memcache.Client(['%s:%d' % (self.conf['host'], self.conf['port'])], debug=self.conf['debug'])
            memcached.flush_all()
