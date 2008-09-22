#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Authentification manager for the basic HTTP authentification scheme"""

import base64

from webob import exc

from nagare.security import common

class Authentification(common.Authentification):
    """Authentification manager for the basic HTTP authentification scheme
    """
    def __init__(self, realm):
        """Initialisation
        
        In:
          - ``realm`` -- authentification realm
        """
        self.realm = realm

    def _get_ids(self, request, response):
        """Return the data associated with the connected user
        
        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          
        Return:
          - A tuple with the id of the user and its password
        """        
        ids = (None, None)  # The anonymous user by default
        
        authorization = request.headers.get('authorization')
        if authorization is not None:
            (scheme, data) = authorization.split()
            if scheme == 'Basic':
                ids = base64.b64decode(data).split(':')
    
        return ids

    def get_ids(self, request, response):
        """Return the data associated with the connected user
        
        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          
        Return:
          - A tuple with the id of the user and its password as a dictionary
        """        
        (username, password) = self._get_ids(request, response)    
        return (username, { 'password' : password })

    def check_password(self, username, real_password, password):
        """Authentification
        
        In:
          - ``username`` -- user id
          - ``real_password`` -- real password of the user
          - ``password`` -- password received
          
        Return:
          - a boolean
        """        
        return real_password == password

    def denies(self, detail):
        """Method called when a permission is denied
        
        In:
          - ``details`` -- a ``security.common.denial`` object
        """
        raise exc.HTTPUnauthorized(
                                   str(detail),
                                   [('WWW-Authenticate', 'Basic realm="%s"' % self.realm)]
                                  ) 
