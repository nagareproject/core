# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Sessions managed in memory

These sessions managers keep:
  - the last recently used ``DEFAULT_NB_SESSIONS`` sessions
  - for each session, the last recently used ``DEFAULT_NB_STATES`` states
"""

from nagare import local
from nagare.sessions import ExpirationError, common, lru_dict
from nagare.sessions.serializer import Pickle

DEFAULT_NB_SESSIONS = 10000
DEFAULT_NB_STATES = 20


class Sessions(common.Sessions):
    """Sessions manager for states kept in memory
    """
    spec = dict(
        common.Sessions.spec,
        nb_sessions='integer(default=%d)' % DEFAULT_NB_SESSIONS,
        nb_states='integer(default=%d)' % DEFAULT_NB_STATES
    )

    def __init__(self, nb_sessions=DEFAULT_NB_SESSIONS, nb_states=DEFAULT_NB_STATES, **kw):
        """Initialization

        In:
          - ``nb_sessions`` -- maximum number of sessions kept in memory
          - ``nb_states`` -- maximum number of states, for each sessions, kept in memory
        """
        super(Sessions, self).__init__(**kw)

        self.nb_states = nb_states
        self._sessions = lru_dict.ThreadSafeLRUDict(nb_sessions)

    def set_config(self, filename, conf, error):
        """Read the configuration parameters

        In:
          - ``filename`` -- path to the configuration file
          - ``conf`` -- ``ConfigObj`` object created from the configuration file
          - ``error`` -- function to call in case of configuration errors
        """
        # Let's the super class validate the configuration file
        conf = super(Sessions, self).set_config(filename, conf, error)

        self.nb_states = conf['nb_states']
        self._sessions = lru_dict.ThreadSafeLRUDict(conf['nb_sessions'])

        return conf

    def check_session_id(self, session_id):
        """Test if a session exist

        In:
          - ``session_id`` -- id of a session

        Return:
          - is ``session_id`` the id of an existing session?
        """
        return session_id in self._sessions

    def create_lock(self, session_id):
        """Create a new lock for a session

        In:
          - ``session_id`` -- session id

        Return:
          - the lock
        """
        return local.worker.create_lock()

    def get_lock(self, session_id):
        """Retrieve the lock of a session

        In:
          - ``session_id`` -- session id

        Return:
          - the lock
        """
        try:
            return self._sessions[session_id][1]
        except KeyError:
            raise ExpirationError()

    def create(self, session_id, secure_id, lock):
        """Create a new session

        In:
          - ``session_id`` -- id of the session
          - ``secure_id`` -- the secure number associated to the session
          - ``lock`` -- the lock of the session
        """
        self._sessions[session_id] = [0, lock, secure_id, None, lru_dict.LRUDict(self.nb_states)]

    def delete(self, session_id):
        """Delete a session

        In:
          - ``session_id`` -- id of the session to delete
        """
        del self._sessions[session_id]

    def fetch_state(self, session_id, state_id):
        """Retrieve a state with its associated objects graph

        In:
          - ``session_id`` -- session id of this state
          - ``state_id`` -- id of this state

        Return:
          - id of the latest state
          - secure number associated to the session
          - data kept into the session
          - data kept into the state
        """
        try:
            last_state_id, _, secure_id, session_data, states = self._sessions[session_id]
            state_data = states[state_id]
        except KeyError:
            raise ExpirationError()

        return last_state_id, secure_id, session_data, state_data

    def store_state(self, session_id, state_id, secure_id, use_same_state, session_data, state_data):
        """Store a state and its associated objects graph

        In:
          - ``session_id`` -- session id of this state
          - ``state_id`` -- id of this state
          - ``secure_id`` -- the secure number associated to the session
          - ``use_same_state`` -- is this state to be stored in the previous snapshot?
          - ``session_data`` -- data to keep into the session
          - ``state_data`` -- data to keep into the state
        """
        session = self._sessions[session_id]

        if not use_same_state:
            session[0] += 1

        session[3] = session_data
        session[4][state_id] = state_data


class SessionsWithPickledStates(Sessions):
    """Sessions manager for states pickled / unpickled in memory
    """
    spec = Sessions.spec.copy()
    spec['serializer'] = 'string(default="nagare.sessions.serializer:Pickle")'

    def __init__(self, serializer=None, **kw):
        """Initialization

        In:
          - ``serializer`` -- serializer / deserializer of the states
        """
        super(SessionsWithPickledStates, self).__init__(serializer=serializer or Pickle, **kw)
