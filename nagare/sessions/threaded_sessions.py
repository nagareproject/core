#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Sessions managed in memory

This sessions manager removed the oldest session (based on its creation
order) when ``DEFAULT_NB_SESSIONS`` is reached.

TODO:

  - add an other sessions manager that keeps the sessions in a LRU list
  - limit the number of continuations kept in memory, by session
  - check the validity of the ``cont_id``
"""

from __future__ import with_statement
import threading

from nagare.sessions import common

DEFAULT_NB_SESSIONS = 10000

class Sessions(common.Sessions):
    """Sessions manager
    """
    def __init__(self, nb=DEFAULT_NB_SESSIONS):
        """Initialisation

        In:
          - ``nb`` -- maximum number of sessions keep in memory
        """
        self.nb = nb

        self._sessions_lock = threading.Lock()

        self._sessions = {}
        self._lrc_sessions = [None]*nb
        self._lrc = 0
        
    def _is_session_exist(self, session_id):
        """Test if a session id is valid
        
        In:
          - ``session_id`` -- id of the session
        
        Return:
           - a boolean
        """        
        with self._sessions_lock:
            return session_id in self._sessions
    
    def _create_session(self, session_id):
        """Create a new session
        
        In:
          - ``session_id`` -- id of the session
        """        
        with self._sessions_lock:
            # Delete the oldest session
            lrc_id = self._lrc_sessions[self._lrc]
            if lrc_id is not None:
                del self._sessions[lrc_id]
    
            self._sessions[session_id] = [0, None, '', None, {}]
            self._lrc_sessions[self._lrc] = session_id
    
            self._lrc = (self._lrc + 1) % self.nb
        
    def _get(self, session_id, cont_id):
        with self._sessions_lock:
            session = self._sessions.get(session_id)

        if session is None:
            return None
        
        return session[:4]+[session[4][cont_id]]
  
    def _set(self, session_id, cont_id, new_id, secureid, query_string, externals, data):
        with self._sessions_lock:
            session = self._sessions[session_id]
            
            session[0] += new_id
            session[1] = secureid
            session[2] = query_string
            session[3] = externals
            session[4][cont_id] = data
            

class SessionsFactory(common.SessionsFactory):
    spec = { 'nb' : 'integer(default=%d)' % DEFAULT_NB_SESSIONS }
    sessions = Sessions
