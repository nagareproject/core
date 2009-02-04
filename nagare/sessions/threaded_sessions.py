#--
# Copyright (c) 2008, 2009 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Sessions managed in memory

This sessions manager keeps:
  - the last recently used ``DEFAULT_NB_SESSIONS`` sessions
  - for each session, the last recently used ``DEFAULT_NB_CONTS`` continuations
"""

from __future__ import with_statement
import threading

from nagare.sessions import common, lru_dict

DEFAULT_NB_SESSIONS = 10000
DEFAULT_NB_CONTS = 20

class Sessions(common.Sessions):
    """Sessions manager for sessions kept in memory
    """
    def __init__(self, nb_sessions=DEFAULT_NB_SESSIONS, nb_continuations=DEFAULT_NB_CONTS):
        """Initialization

        In:
          - ``nb_sessions`` -- maximum number of sessions kept in memory
          - ``nb_continuations`` -- maximum number of continuations, for each sessions kept in memory
        """
        self.nb_continuations = nb_continuations
        self._sessions = lru_dict.ThreadSafeLRUDict(nb_sessions)
        
    def _is_session_exist(self, session_id):
        """Test if a session id is valid
        
        In:
          - ``session_id`` -- id of the session
        
        Return:
           - a boolean
        """
        return session_id in self._sessions        
    
    def _create(self, session_id, secure_id):
        """Create a new session
        
        In:
          - ``session_id`` -- id of the session
          - ``secure_id`` -- the secure number associated to the session
          
        Return:
          - tuple (session_id, cont_id, new_cont_id, lock, secure_id)
        """
        lock = threading.Lock()
        lock.acquire()
        data = [0, lock, secure_id]
        self._sessions[session_id] = data + [None, lru_dict.LRUDict(self.nb_continuations)]
        return [session_id, 0] + data
        
    def __get(self, session_id, cont_id):
        """Return the raw data associated to a session
        
        In:
          - ``session_id`` -- id of the session
          - ``cont_id`` -- id of the continuation
          
        Return:
            - tuple (session_id, cont_id, last_cont_id, lock, secure_id, externals, data)        
        """
        try:
            lock = self._sessions[session_id][1]
        except KeyError:
            raise common.ExpirationError()
        
        lock.acquire()
        session = self._sessions[session_id]

        try:
            cont_id = int(cont_id)
            data = session[-1][cont_id]
        except (KeyError, ValueError, TypeError):
            raise common.ExpirationError()            
    
        return [session_id, cont_id] + session[:-1] + [data]
  
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
        session = self._sessions[session_id]
        
        session[0] += inc_cont_id
        session[3] = externals
        session[4][cont_id] = data

    def _delete(self, session_id):
        """Delete the session
        
        In:
          - ``session_id`` -- id of the session to delete
        """        
        del self._sessions[session_id]


class SessionsFactory(common.SessionsFactory):
    spec = {
            'nb_sessions' : 'integer(default=%d)' % DEFAULT_NB_SESSIONS,
            'nb_continuations' : 'integer(default=%d)' % DEFAULT_NB_CONTS,
           }
    sessions = Sessions
