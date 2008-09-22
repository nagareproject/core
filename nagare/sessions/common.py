#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Base classes for the sessions management"""

import random, cStringIO, cPickle

import configobj

from nagare import config

class Session(object):
    """Base class of the session objects
    """
    def __init__(self, request, response, sessions_manager):
        """Initialisation
        
        In:
          - ``request`` -- the web request object
          - ``response`` -- the web request object
          - ``sessions_manager`` -- the sessions manager that created this session
        """
        self.sessions_manager = sessions_manager

        (session_id, cont_id) = self._get_ids(request)
        
        self.session_id = session_id
        self.cont_id = cont_id
        self.is_xhr = request.is_xhr or ('_a' in request.params)
        
        self.refresh_used = self.back_used = self.is_expired = self.is_new = False

        # -------------------------------------------------------------------

        # Ask the session manager to retrieve the data for the current session and continuation
        (self.data, new_cont_id, self.secureid, query_string) = self.sessions_manager.get(session_id, cont_id)

        c = request.cookies.get('_nagare')
        if not self.data or not c or (c != self.secureid):
            # A new session is created
            # ------------------------
            
            self.is_new = True            
            self.is_expired = bool(session_id)
            (self.session_id, self.new_cont_id) = self.sessions_manager.create()
            
            self.secureid = c or str(random.randint(1000000000000000, 9999999999999999))
            response.set_cookie('_nagare', self.secureid, path=request.script_name + '/')
        else:
            # A previous session is used
            # --------------------------
            
            self.refresh_used = ((request.method == 'GET') and (query_string == request.query_string))
            self.back_used = query_string and (cont_id != (new_cont_id-1))

            # Save the data into the same session / continuation if the request is a XHR one
            self.new_cont_id = new_cont_id if not self.is_xhr else cont_id

    def _get_ids(self, request):
        """Search the session id and the continuation id into the request parameters

        In:
          - ``request`` -- the web request object
          
        Return:
          - a tuple (session id, continuation id) or ('', 0) if no session found
        """
        #return (str(request.cookies.get('_s', '')), int(request.params.get('_c', 0)))
        return (str(request.str_params.get('_s', '')), int(request.str_params.get('_c', 0)))

    def set(self, data, query_string, inc_cont_id=True):
        """Memorize the session data
        
        In:
          - ``data`` -- the data
          - ``query_string`` -- the complete URL
          - ``inc_cont_id`` -- create a new continuation id or save the data
            under the same continuation id ?
        """
        # Forward the call to the sessions manager
        self.sessions_manager.set(
                                  self.session_id, self.new_cont_id,
                                  data, self.secureid, query_string,
                                  inc_cont_id and not self.is_xhr and not self.refresh_used
                                 )

    def sessionid_in_url(self, request, response):
        """Return the session and continuation ids to put into an URL
        
        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          
        Return:
          - tuple (session id, continuation id)
        """
        #response.set_cookie('_s', self.session_id)
        #return ('_c=%05d' % self.new_cont_id,)
        return ('_s='+self.session_id, '_c=%05d' % self.new_cont_id)

    def sessionid_in_form(self, h, request, response):
        """Return the tree to merge into a form to add the session and continuation
        hidden ids
        
        In:
          - ``h`` -- the current renderer
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          
        Return:
          - a tree
        """
        return (
                h.input(name='_s', value=self.session_id, type='hidden'),
                h.input(name='_c', value='%05d' % self.new_cont_id, type='hidden')
               )


class Sessions(object):
    """Base class of the session manager objects
    """
    sessions = Session  # The sessions factory

    def __call__(self, request, response):
        """Create a new session
        
        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          
        Return:
          - the new session object
        """
        return self.sessions(request, response, self)
       
    def _is_session_exist(self, session_id):
        """Test if a session id is valid
        
        In:
          - ``session_id`` -- id of the session
        
        Return:
           - a boolean
        """
        return False
    
    def _create_session(self, session_id):
        """Create a new session
        
        In:
          - ``session_id`` -- id of the session
        """
        pass
    
    def create(self):
        """Create a new session
        
        Return:
          - tuple (session id, continuation id)
        """
        
        # Generate a new id for the session
        while True:
            session_id = str(random.randint(1000000000000000, 9999999999999999))
            if not self._is_session_exist(session_id):
                break
        
        self._create_session(session_id)
        
        return (session_id, 0)
    
    def _get(self, session_id, cont_id):
        """Return the raw data associated to a session
        
        In:
          - ``session_id`` -- id of the session
          - ``cont_id`` -- id of the continuation
          
        Return:
          - ... or ``None`` if the session id or the continuation id are not valid
        """
        return None

    def _loads(self, externals, data):
        """
        """
        p = cPickle.Unpickler(cStringIO.StringIO(data))
        if externals:
            p.persistent_load = lambda i: externals.get(int(i))
            
        return p.load()
        
    def get(self, session_id, cont_id):
        """Return the data associated to a session

        In:
          - ``session_id`` -- id of the session
          - ``cont_id`` -- id of the continuation
          
        Return:
          - a tuple:
            - externals objects dictionary
            - the current cont_id
            - the secure id of the session
            - the query string of the session
        """
        if not session_id:
            return (None,)*4

        session = self._get(session_id, cont_id)
        if session is None:
            return (None,)*4
        
        (last_cont_id, secureid, query_string, externals, cont) = session
        
        p = cPickle.Unpickler(cStringIO.StringIO(cont))
        if externals:
            p.persistent_load = lambda i: externals.get(int(i))

        return (self._loads(externals, cont), last_cont_id, secureid, query_string)

    def _set(id, session_id, cont_id, new_id, secureid, query_string, externals, data):
            pass
    
    def _persistent_id(self, o, externals):
        id = getattr(o, '_persistent_id', None)
        if id is not None:
            externals[id] = o
            return str(id)
    
    def _dumps(self, data):
        f = cStringIO.StringIO()
        p = cPickle.Pickler(f, protocol=-1)
        
        externals = {}
        p.persistent_id = lambda o: self._persistent_id(o, externals)        
        p.dump(data)

        return (externals, f.getvalue())

    def set(self, session_id, cont_id, data, secureid, query_string, new_id):
        f = cStringIO.StringIO()
        p = cPickle.Pickler(f, protocol=-1)
        
        externals = {}
        p.persistent_id = lambda o: self._persistent_id(o, externals)        
        p.dump(data)
        
        self._set(session_id, cont_id, new_id, secureid, query_string, *self._dumps(data))
    

class SessionsFactory(object):
    spec = {}
    sessions = None
    
    def __init__(self, filename, conf, error):
        self.conf = self._validate_conf(filename, conf, error)

    def _validate_conf(self, filename, conf, error):
        conf = dict([(k, v) for (k, v) in conf.items() if k in self.spec])
        conf = configobj.ConfigObj(conf, configspec=self.spec, interpolation='Template')
        config.validate(filename, conf, error)
        
        return conf

    def __call__(self):
        return self.sessions(**self.conf)
