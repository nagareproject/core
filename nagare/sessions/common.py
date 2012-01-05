#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Base classes for the sessions management"""

import random, cStringIO, cPickle

import configobj
from stackless import tasklet

from nagare import config
from nagare.admin import util
from nagare.sessions import ExpirationError

class State(object):
    """A state (objects graph serialized / deserialized by a sessions manager)
    """
    def __init__(self, sessions_manager, session_id, state_id, use_same_state):
        """Initialization

        In:
          - ``sessions_manager`` -- the session manager of this state
          - ``session_id`` -- session id of this state
          - ``state_id`` -- id of this state
          - ``use_same_state`` -- is a copy of this state to create ?
        """
        self.sessions_manager = sessions_manager
        self.session_id = session_id
        self.state_id = state_id
        self.use_same_state = use_same_state

        self.is_new = True         # Is the objects graph initialized ?
        self.secure_id = None      # the secure number associated to the session
        self.lock = None            # Session lock
        self.data = None            # Objects graph
        self.back_used = False     # Is this state a snapshot of a previous objects graph ?

    def release(self):
        """Release the session lock
        """
        self.lock.release()

    def sessionid_in_url(self, request, response):
        """Return the session and states ids to put into an URL

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - tuple (session id parameter, state id parameter)
        """
        return self.sessions_manager.sessionid_in_url(self.session_id, self.state_id, request, response)

    def sessionid_in_form(self, h, request, response):
        """Return the DOM tree to merge into a form, to add the session and state hidden ids

        In:
          - ``h`` -- the current renderer
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - the DOM tree
        """
        return self.sessions_manager.sessionid_in_form(self.session_id, self.state_id, h, request, response)

    def create(self, secure_id):
        """Initialized a new state, with an empty objects graph

        In:
         - ``secure_id`` -- the secure number associated to the session
        """
        self.secure_id = secure_id
        (self.state_id, self.lock) = self.sessions_manager.create_state(self.session_id, secure_id)

    def get(self):
        """Retrieve the state

        Return:
         - ``secure_id`` -- the secure number associated to the session
        """
        (new_state_id, self.lock, self.secure_id, self.data) = self.sessions_manager.get_state(self.session_id, self.state_id, self.use_same_state)

        self.back_used = not self.use_same_state and (int(self.state_id) != (new_state_id-1))

        self.is_new = False
        self.state_id = new_state_id

        return self.secure_id

    def set(self, use_same_state, data):
        """Store the state

        In:
          - ``use_same_state`` -- is this state to be stored in the previous snapshot ?
          - ``data`` -- the objects graph
        """
        self.sessions_manager.set_state(self.session_id, self.state_id, self.secure_id, self.use_same_state or use_same_state, data)

    def delete(self):
        """Delete this state
        """
        self.sessions_manager.delete(self.session_id)


def persistent_id(o, session_data, tasklets):
    """The object with a `_persistent_id` attribute are stored into the session
    not into the state snapshot

    In:
      - ``o`` -- object to check

    Out:
      - ``session_data`` -- dict of the objects to store into the session
      - ``tasklets`` -- set of the serialized tasklets
    """
    id = getattr(o, '_persistent_id', None)
    if id is not None:
        session_data[id] = o
        return str(id)

    if type(o) == tasklet:
        tasklets.add(o)


class Sessions(object):
    """The sessions managers
    """
    spec = {
            'security_cookie_name' : 'string(default="_nagare")',
            'states_history' : 'boolean(default=True)',
            'pickler' : 'string(default="cPickle:Pickler")',
            'unpickler' : 'string(default="cPickle:Unpickler")',
           }

    def __init__(
                    self,
                    states_history=True,
                    pickler=cPickle.Pickler, unpickle=cPickle.Unpickler,
                    security_cookie_name='_nagare'
                ):
        """Initialization

        In:
          - ``security_cookie_name`` -- name of the cookie where the session secure id is stored
        """
        self.states_history = True
        self.pickler = cPickle.Pickler
        self.unpickler = cPickle.Unpickler
        self.security_cookie_name = security_cookie_name

    def set_config(self, filename, conf, error):
        """Read the configuration parameters

        In:
          - ``filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        conf = dict([(k, v) for (k, v) in conf.items() if k in self.spec])
        conf = configobj.ConfigObj(conf, configspec=self.spec)
        config.validate(filename, conf, error)

        self.security_cookie_name = conf['security_cookie_name']
        self.states_history = conf['states_history']

        self.pickler = util.load_object(conf['pickler'])[0]
        self.unpickler = util.load_object(conf['unpickler'])[0]

        return conf

    def get(self, request, response, use_same_state):
        """Create a new state or return an existing one

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``use_same_state`` -- is a copy of the state to create ?

        Return:
          - the state object
        """
        (session_id, state_id) = self._get_ids(request)
        is_new = not session_id or not state_id

        if is_new:
            # New session: create a new session id
            while True:
                session_id = str(random.randint(1000000000000000, 9999999999999999))
                if not self.is_session_exist(session_id):
                    break

        state = State(self, session_id, state_id, use_same_state or not self.states_history)

        if self.security_cookie_name:
            secure_id = request.cookies.get(self.security_cookie_name) or str(random.randint(1000000000000000, 9999999999999999))
        else:
            secure_id = None

        if is_new:
            # New state
            # ---------

            state.create(secure_id)

            if self.security_cookie_name:
                response.set_cookie(self.security_cookie_name, secure_id, path=request.script_name + '/')
        else:
            # Existing state
            # --------------

            session_secure_id = state.get()

            if session_secure_id != secure_id:
                raise ExpirationError()

        return state

    def _get_ids(self, request):
        """Search the session id and the state id into the request parameters

        In:
          - ``request`` -- the web request object

        Return:
          - a tuple (session id, state id) or ('', '') if no session found
        """
        return (
                    str(request.params.get('_s', '')),
                    str(request.params.get('_c', '')) if self.states_history else '0'
                )

    def sessionid_in_url(self, session_id, state_id, request, response):
        """Return the session and states ids to put into an URL

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - tuple (session id parameter, state id parameter)
        """
        ids = ('_s='+session_id,)
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

    def get_state(self, session_id, state_id, use_same_state):
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
            - objects graph
        """
        (state_id, lock, secure_id, session_data, state_data) = self._get(session_id, state_id, use_same_state)
        data = self.deserialize(session_data, state_data)
        return (state_id, lock, secure_id, data)

    def create_state(self, session_id, secure_id):
        """Initialized a new state, with an empty objects graph

        In:
          - ``session_id`` -- session id of this state
          - ``secure_id`` -- the secure number associated to the session

        Return:
          - the tuple:
            - id of this state,
            - session lock
        """
        return self._create(session_id, secure_id)

    def set(self, state, use_same_state):
        """Store the state

        In:
          - ``state`` -- the state object
          - ``use_same_state`` -- is a copy of this state to create ?
        """
        state.set(self, use_same_state)

    def set_state(self, session_id, state_id, secure_id, use_same_state, data):
        """Store the state

        In:
          - ``session_id`` -- session id of this state
          - ``state_id`` -- id of this state
          - ``secure_id`` -- the secure number associated to the session
          - ``use_same_state`` -- is this state to be stored in the previous snapshot ?
          - ``data`` -- the objects graph
        """
        (session_data, state_data) = self.serialize(data)
        self._set(session_id, state_id, secure_id, use_same_state, session_data, state_data)

    def delete(self, session_id):
        """Delete the session

        In:
          - ``session_id`` -- session id of this state
        """
        self._delete(session_id)

    def is_session_exist(self, session_id):
        """Test if a session id is invalid

        In:
          - ``session_id`` -- id of the session

        Return:
          - a boolean
        """
        return False

    def pickle(self, data):
        """Pickle an objects graph

        In:
          - ``data`` -- the objects graph

        Out:
          - the tuple:
            - data to keep into the session
            - data to keep into the state
        """
        f = cStringIO.StringIO()
        p = self.pickler(f, protocol=-1)

        session_data = {}
        tasklets = set()
        p.persistent_id = lambda o: persistent_id(o, session_data, tasklets)
        p.dump(data)

        # Kill all the blocked tasklets, which are now serialized
        for t in tasklets:
            t.kill()

        return (session_data, f.getvalue())

    def unpickle(self, session_data, state_data):
        """Unpickle an objects graph

        In:
          - ``session_data`` -- data from the session
          - ``state_data`` -- data from the state

        Out:
          - the objects graph
        """
        p = self.unpickler(cStringIO.StringIO(state_data))
        if session_data:
            p.persistent_load = lambda i: session_data.get(int(i))

        return p.load()
