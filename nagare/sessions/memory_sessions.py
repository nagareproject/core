#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Sessions managed in memory

These sessions managers keeps:
  - the last recently used ``DEFAULT_NB_SESSIONS`` sessions
  - for each session, the last recently used ``DEFAULT_NB_STATES`` states
"""

from nagare import local
from nagare.sessions import ExpirationError, common, lru_dict

DEFAULT_NB_SESSIONS = 10000
DEFAULT_NB_STATES = 20

class SessionsBase(common.Sessions):
    """Sessions manager for sessions kept in memory
    """
    spec = {
            'nb_sessions' : 'integer(default=%d)' % DEFAULT_NB_SESSIONS,
            'nb_states' : 'integer(default=%d)' % DEFAULT_NB_STATES
           }

    spec.update(common.Sessions.spec)

    def __init__(self, nb_sessions=DEFAULT_NB_SESSIONS, nb_states=DEFAULT_NB_STATES, **kw):
        """Initialization

        In:
          - ``nb_sessions`` -- maximum number of sessions kept in memory
          - ``nb_states`` -- maximum number of states, for each sessions, kept in memory
        """
        super(SessionsBase, self).__init__(**kw)

        self.nb_states = nb_states
        self._sessions = lru_dict.ThreadSafeLRUDict(nb_sessions)

    def set_config(self, filename, conf, error):
        """Read the configuration parameters

        In:
          - ``filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        # Let's the super class validate the configuration file
        conf = super(SessionsBase, self).set_config(filename, conf, error)

        self.nb_states = conf['nb_states']
        self._sessions = lru_dict.ThreadSafeLRUDict(conf['nb_sessions'])

    def is_session_exist(self, session_id):
        """Test if a session id is invalid

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
          - the tuple:
            - id of this state,
            - session lock
        """
        lock = local.worker.create_lock()
        lock.acquire()

        self._sessions[session_id] = [0, lock, secure_id, None, lru_dict.LRUDict(self.nb_states)]
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
        try:
            lock = self._sessions[session_id][1]
        except KeyError:
            raise ExpirationError()

        lock.acquire()

        try:
            state_id = int(state_id)
            (last_state_id, lock, secure_id, session_data, states) = self._sessions[session_id]
            state_data = states[state_id]
        except (KeyError, ValueError, TypeError):
            raise ExpirationError()

        if not use_same_state:
            state_id = last_state_id

        return (state_id, lock, secure_id, session_data, state_data)

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
        session = self._sessions[session_id]

        if not use_same_state:
            session[0] += 1

        session[3] = session_data
        session[4][state_id] = state_data

    def _delete(self, session_id):
        """Delete the session

        In:
          - ``session_id`` -- id of the session to delete
        """
        del self._sessions[session_id]


class SessionsWithPickledStates(SessionsBase):
    """Sessions managers that pickle / unpickle the objects graph
    """
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
