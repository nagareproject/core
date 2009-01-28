#--
# Copyright (c) 2008, 2009 Net-ng.
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

class ExpirationError(LookupError):
    pass


class Session(object):
    """Base class of the session objects
    """
    def __init__(self, session_id, cont_id, new_cont_id, lock, secure_id, data=None):
        """Initialization
        
        In:
          - `session_id` -- id of the current session
          - `cont_id` -- id of the current continuation
          - `new_cont_id` -- id of the next continuation
          - `lock` -- session thread lock
          - `secure_id` -- the secure number associated to the session          
          - `data` -- data of the session
        """
        self.session_id = session_id
        self.cont_id = cont_id
        self.new_cont_id = new_cont_id
        self.lock = lock
        self.secure_id = secure_id
        self.data = data
        
        self.is_new = data is None
        self.back_used = not self.is_new and new_cont_id and (cont_id != (new_cont_id-1))

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
    def get(self, request, response):
        """Create a new session or return an existing one
        
        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          
        Return:
          - the session object
        """
        (session_id, cont_id) = self._get_ids(request)

        c = request.cookies.get('_nagare')

        if session_id:
            # Existing session
            # ----------------
            
            data = self._get(session_id, cont_id)
            if data[-2] != c:
                raise ExpirationError()
        else:
            # New session
            # -----------
            
            secure_id = c or str(random.randint(1000000000000000, 9999999999999999))
            response.set_cookie('_nagare', secure_id, path=request.script_name + '/')
            data = self.create(secure_id)
            
        session = Session(*data)

        if request.is_xhr or ('_a' in request.params):
            # Save the data into the same session / continuation if the request is a XHR one
            session.new_cont_id = data[1]

        return session

    def set(self, session, inc_cont_id):
        """Memorize the session data
        
        In:
          - `session` -- the session object
          - `inc_cont_id` -- is the continuation id to increment ?
        """
        self._set(
                  session.session_id, session.new_cont_id,
                  session.secure_id, session.data,
                  inc_cont_id
                 )
    
    def _get_ids(self, request):
        """Search the session id and the continuation id into the request parameters

        In:
          - ``request`` -- the web request object
          
        Return:
          - a tuple (session id, continuation id) or (None, None) if no session found
        """
        #return (str(request.cookies.get('_s', '')), int(request.params.get('_c', 0)))
        return (request.str_params.get('_s'), request.str_params.get('_c'))
    
    def create(self, secure_id):
        """Create a new session
        
        In:
          - `secure_id` -- the secure number associated to the session
          
        Return:
          - tuple (session_id, cont_id, new_cont_id, lock)
        """
        # Generate a new id for the session
        while True:
            session_id = str(random.randint(1000000000000000, 9999999999999999))
            if not self._is_session_exist(session_id):
                break
        
        return self._create(session_id, secure_id)
    
    def _get(self, session_id, cont_id):
        """Return the data associated to a session

        In:
          - ``session_id`` -- id of the session
          - ``cont_id`` -- id of the continuation
          
        Return:
          - tuple (session_id, cont_id, new_cont_id, lock, secure_id, data)
        """
        (session_id, cont_id, last_cont_id, lock, secure_id, externals, data) = self.__get(session_id, cont_id)
        
        p = cPickle.Unpickler(cStringIO.StringIO(data))
        if externals:
            p.persistent_load = lambda i: externals.get(int(i))

        return (session_id, cont_id, last_cont_id, lock, secure_id, p.load())

    def _persistent_id(self, o, externals):
        id = getattr(o, '_persistent_id', None)
        if id is not None:
            externals[id] = o
            return str(id)
    
    def _set(self, session_id, cont_id, secure_id, data, inc_cont_id):
        """Memorize the session data
        
        In:
          - `session_id` -- id of the current session
          - `cont_id` -- id of the current continuation
          - `secure_id` -- the secure number associated to the session          
          - `data` -- data of the session
          - `inc_cont_id` -- is the continuation id to increment ?          
        """
        f = cStringIO.StringIO()
        p = cPickle.Pickler(f, protocol=-1)
        
        externals = {}
        p.persistent_id = lambda o: self._persistent_id(o, externals)        
        p.dump(data)
        
        self.__set(session_id, cont_id, secure_id, inc_cont_id, externals, f.getvalue())
        
    # -------------------------------------------------------------------------
    
    def _is_session_exist(self, session_id):
        """Test if a session id is valid
        
        In:
          - ``session_id`` -- id of the session
        
        Return:
           - a boolean
        """
        return False
    
    def _create(self, session_id, secure_id):
        """Create a new session
        
        In:
          - ``session_id`` -- id of the session
          - `secure_id` -- the secure number associated to the session
          
        Return:
          - tuple (session_id, cont_id, new_cont_id, lock)
        """
        pass

    def __get(self, session_id, cont_id):
        """Return the raw data associated to a session
        
        In:
          - ``session_id`` -- id of the session
          - ``cont_id`` -- id of the continuation
          
        Return:
            - tuple (session_id, cont_id, last_cont_id, lock, secure_id, externals, data)        
        """
        return None

    def __set(self, session_id, cont_id, secure_id, inc_cont_id, externals, data):
        """Memorize the session data
        
        In:
          - `session_id` -- id of the current session
          - `cont_id` -- id of the current continuation
          - `secure_id` -- the secure number associated to the session            
          - `inc_cont_id` -- is the continuation id to increment ? 
          - `externals` -- pickle of shared objects across the continuations                    
          - `data` -- pickle of the objects in the continuation
        """
        pass
    

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
