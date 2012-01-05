#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Authentication manager for the basic HTTP authentication scheme"""

from webob import exc

from nagare.security import common

class Authentication(common.Authentication):
    """Authentication manager for the basic HTTP authentication scheme
    """
    def __init__(self, realm):
        """Initialization

        In:
          - ``realm`` -- authentication realm
        """
        self.realm = str(realm) if realm is not None else None

    def _get_ids(self, request, response):
        """Return the data associated with the connected user

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - A list with the id of the user and its password
        """
        ids = [None, None]  # The anonymous user by default

        authorization = request.headers.get('authorization')
        if authorization is not None:
            (scheme, data) = authorization.split(' ', 1)
            if scheme == 'Basic':
                encoding = request.accept_charset.best_match(['iso-8859-1', 'utf-8'])
                ids = [s.decode(encoding) for s in data.decode('base64').split(':', 1)]

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
        """Authentication

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
