# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Base classes for the sessions management"""

import random

import configobj

from nagare import config
from nagare.admin import reference
from nagare.sessions import SessionSecurityError, serializer


class State(object):
    """A state (objects graph serialized / de-serialized by a sessions manager)
    """
    def __init__(self, sessions_manager, session_id, state_id, secure_id, use_same_state):
        """Initialization

        In:
          - ``sessions_manager`` -- the manager of this state
          - ``session_id`` -- session id of this state
          - ``state_id`` -- id of this state (``None`` to create a new state)
          - ``secure_id`` -- the secure number associated to the session
          - ``use_same_state`` -- is a copy of this state to create?
        """
        self.sessions_manager = sessions_manager
        self.session_id = session_id
        self.state_id = state_id
        self.secure_id = secure_id
        self.use_same_state = use_same_state

        self.back_used = False  # Is this state a snapshot of a previous objects graph?
        self.lock = (sessions_manager.create_lock if state_id is None else sessions_manager.get_lock)(self.session_id)

    def sessionid_in_url(self, request, response):
        """Return the session and states ids to put into an URL

        In:
          - ``request`` -- the web request
          - ``response`` -- the web response

        Return:
          - session id parameter
          - state id parameter
        """
        return self.sessions_manager.sessionid_in_url(self.session_id, self.state_id, request, response)

    def sessionid_in_form(self, h, request, response):
        """Return the DOM tree to merge into a form, to add the session and state hidden ids

        In:
          - ``h`` -- the current renderer
          - ``request`` -- the web request
          - ``response`` -- the web response

        Return:
          - the DOM tree
        """
        return self.sessions_manager.sessionid_in_form(self.session_id, self.state_id, h, request, response)

    def acquire(self):
        """Lock the state
        """
        self.lock.acquire()  # Lock the session

    def release(self):
        """Release the state
        """
        self.lock.release()  # Release the session

    def get_root(self):
        """Retrieve the objects graph of this state

        Return:
         - the objects graph (``None`` if this state is new)
        """
        if self.state_id is None:
            # New state
            self.sessions_manager.create(self.session_id, self.secure_id, self.lock)
            self.state_id = 0
            data = None
        else:
            # Existing state
            new_state_id, secure_id, data = self.sessions_manager.get_root(self.session_id, self.state_id)
            if secure_id != self.secure_id:
                raise SessionSecurityError

            if not self.use_same_state:
                self.back_used = (self.state_id != new_state_id - 1)
                self.state_id = new_state_id

        return data

    def set_root(self, use_same_state, data):
        """Store the objects graph of this state

        In:
          - ``use_same_state`` -- is the objects graph to be stored in this state or in a new one?
          - ``data`` -- the objects graph
        """
        self.sessions_manager.set_root(self.session_id, self.state_id, self.secure_id, self.use_same_state or use_same_state, data)

    def delete(self):
        """Delete the session of this state
        """
        self.sessions_manager.delete(self.session_id)


class Sessions(object):
    """The sessions managers
    """
    spec = {
        'security_cookie_httponly': 'boolean(default=True)',
        'security_cookie_name': 'string(default="_nagare")',
        'security_cookie_secure': 'boolean(default=False)',
        'states_history': 'boolean(default=True)',
        'pickler': 'string(default="cPickle:Pickler")',
        'unpickler': 'string(default="cPickle:Unpickler")',
        'serializer': 'string(default="nagare.sessions.serializer:Dummy")'
    }

    def __init__(
        self,
        states_history=True,
        security_cookie_httponly=True,
        security_cookie_name='_nagare',
        security_cookie_secure=False,
        serializer=serializer.Dummy, pickler=None, unpickler=None
    ):
        """Initialization

        In:
          - ``states_history`` -- are all the states kept or only the latest?
          - ``security_cookie_name`` -- name of the cookie where the session secure id is stored
          - ``serializer`` -- serializer / deserializer of the states
          - ``pickler`` -- pickler used by the serializer
          - ``unpickler`` -- unpickler used by the serializer
        """
        self.states_history = states_history
        self.security_cookie_httponly = security_cookie_httponly
        self.security_cookie_name = security_cookie_name
        self.security_cookie_secure = security_cookie_secure
        self.serializer = serializer(pickler, unpickler)

    def set_config(self, filename, conf, error):
        """Read the configuration parameters

        In:
          - ``filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        conf = dict([(k, v) for k, v in conf.items() if k in self.spec])
        conf = configobj.ConfigObj(conf, configspec=self.spec)
        config.validate(filename, conf, error)

        self.states_history = conf['states_history']
        self.security_cookie_name = conf['security_cookie_name']

        pickler = reference.load_object(conf['pickler'])[0]
        unpickler = reference.load_object(conf['unpickler'])[0]
        serializer = reference.load_object(conf['serializer'])[0]
        self.serializer = serializer(pickler, unpickler)

        return conf

    def sessionid_in_url(self, session_id, state_id, request, response):
        """Return the session and states ids to put into an URL

        In:
          - ``request`` -- the web request
          - ``response`` -- the web response

        Return:
          - session id parameter
          - state id parameter (optional, only if ``states_history`` is ``True``)
        """
        ids = ('_s=%d' % session_id,)
        if self.states_history:
            ids += ('_c=%05d' % state_id,)

        return ids

    def sessionid_in_form(self, session_id, state_id, h, request, response):
        """Return the DOM tree to merge into a form to add the session and state
        hidden ids

        In:
          - ``h`` -- the current renderer
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - a DOM tree
        """
        return (
            h.input(name='_s', value=session_id, type='hidden'),
            h.input(name='_c', value='%05d' % state_id, type='hidden')
        )

    def _get_ids(self, request):
        """Search the session id and the state id into the request parameters

        In:
          - ``request`` -- the web request

        Return:
          - session id
          - state id
        """
        return (
            int(request.params['_s']),
            int(request.params['_c']) if self.states_history else 0
        )

    def check_session_id(self, session_id):
        """Test if a session exist

        In:
          - ``session_id`` -- id of a session

        Return:
          - is ``session_id`` the id of an existing session?
        """
        return False

    def get_state(self, request, response, use_same_state):
        """Create a new state or return an existing one

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``use_same_state`` -- is a copy of the state to created?

        Return:
          - the state
        """
        try:
            session_id, state_id = self._get_ids(request)
        except (KeyError, ValueError, TypeError):
            state_id = None

            # Create a new session id
            while True:
                session_id = random.randint(1000000000000000, 9999999999999999)
                if not self.check_session_id(session_id):
                    break

        secure_id = None
        if self.security_cookie_name:
            secure_id = request.cookies.get(self.security_cookie_name)
            if not secure_id:
                secure_id = str(random.randint(1000000000000000, 9999999999999999))
                response.set_cookie(self.security_cookie_name, secure_id, path=request.script_name + '/',
                                    secure=self.security_cookie_secure,
                                    httponly=self.security_cookie_httponly)

        return State(self, session_id, state_id, secure_id, use_same_state or not self.states_history)

    def get_root(self, session_id, state_id):
        """Retrieve the objects graph of a state

        In:
          - ``session_id`` -- session id of this state
          - ``state_id`` -- id of this state

        Return:
          - id of the latest state
          - secure number associated to the session
          - objects graph
        """
        new_state_id, secure_id, session_data, state_data = self.fetch_state(session_id, state_id)
        return new_state_id, secure_id, self.serializer.loads(session_data, state_data)

    def set_root(self, session_id, state_id, secure_id, use_same_state, data):
        """Store the state

        In:
          - ``session_id`` -- session id of this state
          - ``state_id`` -- id of this state
          - ``secure_id`` -- the secure number associated to the session
          - ``use_same_state`` -- is a copy of this state to be created?
          - ``data`` -- the objects graph
        """
        session_data, state_data = self.serializer.dumps(data, not use_same_state)
        self.store_state(session_id, state_id, secure_id, use_same_state, session_data, state_data)

    # -------------------------------------------------------------------------

    def create_lock(self, session_id):
        """Create a new lock for a session

        In:
          - ``session_id`` -- session id

        Return:
          - the lock
        """
        return self.get_lock(session_id)

    def get_lock(self, session_id):
        """Retrieve the lock of a session

        In:
          - ``session_id`` -- session id

        Return:
          - the lock
        """
        raise NotImplementedError()

    def create(self, session_id, secure_id, lock):
        """Create a new session

        In:
          - ``session_id`` -- id of the session
          - ``secure_id`` -- the secure number associated to the session
          - ``lock`` -- the lock of the session
        """
        raise NotImplementedError()

    def delete(self, session_id):
        """Delete a session

        In:
          - ``session_id`` -- id of the session to delete
        """
        raise NotImplementedError()

    def fetch_state(self, session_id, state_id):
        """Retrieve a state with its associated objects graph

        In:
          - ``session_id`` -- session id of this state
          - ``state_id`` -- id of this state

        Return:
          - id of the more recent stored state
          - secure number associated to the session
          - data kept into the session
          - data kept into the state
        """
        raise NotImplementedError()

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
        raise NotImplementedError()
