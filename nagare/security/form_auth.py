#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Simple form based authentication manager

The id and password of the user are first searched into the parameters of
the request. So, first, set a form with the fields names ``__ac_name``
and ``__ac_password`` (the prefix ``__ac`` is configurable).

Then the user id and the password are automatically kept into a cookie,
sent back on each request by the browser.

.. warning::

   This simple authentication manager keeps the user id and password in
   clear into the cookie. So this authentication manager is as secure as
   the HTTP basic authentication.
"""
import webob

from nagare import security
from nagare.security import basic_auth

class Authentication(basic_auth.Authentication):
    """Simple form based authentication"""

    def __init__(self, prefix='__ac', key=None, max_age=None,
                 path='/', domain=None, secure=None, httponly=False,
                 comment=None, expires=None, overwrite=False,
                 realm=None):
        """Initialization

        In:
          - ``prefix`` -- prefix of the names of the user id and password fields
            into the form
          - ``realm`` -- is the form based authentication completed by a
            basic HTTP authentication ?
          - all the other keyword parameters are passed to the ``set_cookie()``
            method of the ``WebOb`` response object
            (see http://pythonpaste.org/webob/reference.html#id5)
        """
        super(Authentication, self).__init__(realm)
        self.prefix = prefix

        self.key = key or prefix
        self.max_age = max_age
        self.path = path
        self.domain = domain
        self.secure = secure
        self.httponly = httponly
        self.comment = comment
        self.expires = expires
        self.overwrite = overwrite

    def get_ids_from_params(self, params):
        """Search the data associated with the connected user into the request
        parameter

        In:
          - ``params`` -- the request parameters

        Return:
          - A tuple with the id of the user and its password
        """
        return (params.get(self.prefix+'_name'), params.get(self.prefix+'_password'))

    def cookie_decode(self, cookie):
        """Decode the data of the user cookie

        In:
          - ``cookie`` -- the data of the user cookie

        Return:
          - A list with the id of the user and its password
        """
        return [s.decode('base64').decode('utf-8') for s in cookie.split(':')]

    def get_ids_from_cookie(self, cookies):
        """Search the data associated with the connected user into the cookies

        In:
          - ``cookies`` -- cookies dictionary

        Return:
          - A list with the id of the user and its password
        """
        data = cookies.get(self.key)
        if not data:
            return (None, None)

        return self.cookie_decode(data)

    def cookie_encode(self, username, password):
        """Encode the data of the user cookie

        In:
          - ``username`` -- name (login) of the user
          - ``password`` -- password of the user

        Return:
          - the data to put into the user cookie
        """
        return '%s:%s' % (
                          username.encode('utf-8').encode('base64').rstrip(),
                          password.encode('utf-8').encode('base64').rstrip()
                         )

    def _get_ids(self, request, response):
        """Return the data associated with the connected user

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - A list with the id of the user and its password
        """
        # First, search into the request parameters
        ids = self.get_ids_from_params(request.params)
        if not all(ids):
            # Second, search into the cookies
            ids = self.get_ids_from_cookie(request.cookies)
            if not all(ids) and self.realm:
                # Third, if a realm is set, look into the basic authentication header
                ids = super(Authentication, self)._get_ids(request, response)

        return ids

    def set_user_id(self, user, id, password):
        """Set the credentials of the user

        In:
          - ``user`` -- the user
          - ``id`` -- the user id
          - ``password`` -- the user password
        """
        user.set_id(id, password)

    def end_rendering(self, request, response, session):
        """End of the request processing

        In:
          - ``request`` -- the request object
          - ``response`` -- the response object
          - ``session`` -- the session
        """
        user = security._get_user()

        if user:
            if not user.expired:
                response.set_cookie(
                                self.key, self.cookie_encode(*user.get_id()),
                                max_age=self.max_age,
                                path=self.path,
                                domain=self.domain,
                                secure=self.secure,
                                httponly=self.httponly,
                                comment=self.comment,
                                expires=self.expires,
                                overwrite=self.overwrite
                            )
            else:
                response.delete_cookie(self.key, self.path, self.domain)

                if user.delete_session:
                    session.delete()

                location = user.logout_location
                if location is not None:
                    if not location.startswith(('http', '/')):
                        location = request.application_url + '/' + location

                    response.status = 301
                    response.location = location
                    response.body = ''

    def denies(self, detail):
        """Method called when a permission is denied

        In:
          - ``details`` -- a ``security.common.denial`` object
        """
        if self.realm:
            super(Authentication, self).denies(detail)

        raise webob.exc.HTTPForbidden(str(detail))

    def logout(self, location='', delete_session=True):
        """Deconnection of the current user

        Mark the user object as expired

        In:
          - ``location`` -- location to redirect to
          - ``delete_session`` -- is the session expired too ?
        """
        user = security.get_user()

        user.logout_location = location
        user.delete_session = delete_session
        user.expired = True
