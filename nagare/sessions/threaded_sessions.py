#--
# Copyright (c) 2008, Net-ng.
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

from nagare.sessions import common, lru_dict

DEFAULT_NB_SESSIONS = 10000
DEFAULT_NB_CONTS = 20

class Sessions(common.Sessions):
    """Sessions manager
    """
    def __init__(self, nb_sessions=DEFAULT_NB_SESSIONS, nb_conts=DEFAULT_NB_CONTS):
        """Initialization

        In:
          - ``nb_sessions`` -- maximum number of sessions kept in memory
          - ``nb_conts`` -- maximum number of continuations, for each sessions kept in memory
        """
        self.nb_conts = nb_conts
        self._sessions = lru_dict.ThreadSafeLRUDict(nb_sessions)
        
    def _is_session_exist(self, session_id):
        """Test if a session id is valid
        
        In:
          - ``session_id`` -- id of the session
        
        Return:
           - a boolean
        """
        return session_id in self._sessions        
    
    def _create_session(self, session_id):
        """Create a new session
        
        In:
          - ``session_id`` -- id of the session
        """
        self._sessions[session_id] = [0, None, None, lru_dict.ThreadSafeLRUDict(self.nb_conts)]        
        
    def _get(self, session_id, cont_id):
        with self._sessions:
            try:
                session = self._sessions[session_id]
                cont = session[3][cont_id]
            except KeyError:
                return None
        
            return session[:3]+[cont]
  
    def _set(self, session_id, cont_id, new_id, secureid, externals, data):
        with self._sessions:
            session = self._sessions[session_id]
            
            session[0] += new_id
            session[1] = secureid
            session[2] = externals
            session[3][cont_id] = data
            

class SessionsFactory(common.SessionsFactory):
    spec = { 'nb' : 'integer(default=%d)' % DEFAULT_NB_SESSIONS }
    sessions = Sessions
