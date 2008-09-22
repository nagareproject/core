#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Simple form based authentification manager

The id and password of the user are first searched into the parameters of
the request. So, first, set a form with the fields names ``__ac_name``
and ``__ac_password`` (the prefix ``__ac`` is configurable).

Then the user id and the password are automatically keeped into a cookie,
sent back on each request by the browser.

.. warning::

   This simple authentification manager keeps the user id and password in
   clear into the cookie. So this authentification manager is as secure as
   the HTTP basic authentification. 
"""

import base64

import webob

from nagare.security import basic_auth

class HTTPRefresh(webob.exc.HTTPMovedPermanently):
    """An HTTP exception that refreshs the current page
    """
    def __call__(self, environ, start_response):
        """Act as a WSGI application
        
        In:
          - ``environ`` -- the WSGI environment
          - ``start_response`` -- the WSGI response call-back
        """
        location = webob.Request(environ).url
        i = location.find('&_action')
        self.location = location[:(i if i != -1 else None)]
        
        # Return an empty response with a redirect header
        return super(HTTPRefresh, self).__call__(environ, start_response)


class Authentification(basic_auth.Authentification):
    """Simple from based authentification"""

    def __init__(self, prefix='__ac', realm=None):
        """Initialisation
        
        In:
          - ``prefix`` -- prefix of the names of the user id and password fields
            into the form
          - ``realm`` -- is the form based authentification completed by a
            basic HTTP authentification ?
        """        
        super(Authentification, self).__init__(realm)        
        self.prefix = prefix

    def get_ids_from_params(self, params):
        """Search the data associated with the connected user into the request
        parameter
        
        In:
          - ``params`` -- the request parameter
          
        Return:
          - A tuple with the id of the user and its password
        """                
        return (params.get(self.prefix+'_name'), params.get(self.prefix+'_password'))

    def get_ids_from_cookie(self, cookies):
        """Search the data associated with the connected user into the cookies
        
        In:
          - ``cookies`` -- cookies dictionary
          
        Return:
          - A tuple with the id of the user and its password
        """                
        data = cookies.get(self.prefix)
        if data is not None:
            return base64.b64decode(data).split(':')
        
        return (None, None)

    def _get_ids(self, request, response):
        """Return the data associated with the connected user
        
        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          
        Return:
          - A tuple with the id of the user and its password
        """
        # First, search into the request parameters                
        (username, password) = self.get_ids_from_params(request.params)
        if username:
            # Copy the user id and the password into a cookie
            response.set_cookie(self.prefix, base64.b64encode(('%s:%s' % (username, password))))
        else:
            # Second, search into the cookies
            (username, password) = self.get_ids_from_cookie(request.cookies)
            if not username and self.realm:
                # Third, is a realm is set, look into the basic authentification header
                (username, password) = super(Authentification, self)._get_ids(request, response)

        return (username, password)
    
    def denies(self, detail):
        """Method called when a permission is denied
        
        In:
          - ``details`` -- a ``security.common.denial`` object
        """        
        if self.realm:
            super(Authentification, self).denies(detail)

        raise webob.exc.HTTPForbidden(str(detail)) 

    def logout(self):
        """Deconnection of the current user
        
        Delete the cookie
        """
        exc = HTTPRefresh()
        exc.delete_cookie(self.prefix)
        raise exc
