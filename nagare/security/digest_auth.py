#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Authentication manager for the digest HTTP authentication scheme"""

import time
import hashlib

import webob

from nagare.security import common

class Authentication(common.Authentication):
    """Authentication manager for the digest HTTP authentication scheme
    """
    def __init__(self, realm, private_key):
        """Initialization

        In:
          - ``realm`` -- authentication realm
          - ``private_key`` -- will be hashed to generate the digest
        """
        self.realm = str(realm)
        self.private_key = private_key

    def get_ids(self, request, response):
        """Return the data associated with the connected user

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - A tuple with the id of the user and all the challenge response parameters
        """
        authorization = request.headers.get('authorization')
        if authorization is not None:
            (scheme, data) = authorization.split(' ', 1)
            if scheme == 'Digest':
                data = [x.split('=', 1) for x in data.split(',')]
                data = dict([(k.lstrip(), v.strip('"')) for (k, v) in data])

                encoding = request.accept_charset.best_match(['iso-8859-1', 'utf-8'])
                data['encoding'] = encoding
                return (data.pop('username').decode(encoding), data)

        return (None, { 'response' : None, 'encoding' : None })

    def check_password(self, username, password, response, encoding, realm='', uri='', nonce='', nc='', cnonce='', qop='', **kw):
        """Authentication

        In:
          - ``username`` -- user id
          - ``password`` -- real password of the user
          - ``encoding`` -- encoding of username and password on the client
          - ``response``, ``realm``, ``uri``, ``nonce``, ``nc``, ``cnonce``,
            ``qop`` -- elements of the challenge response

        Return:
          - a boolean
        """
        if (username is None) and (response is None):
            # Anonymous user
            return None

        # Make our side hash
        hda1 = hashlib.md5('%s:%s:%s' % (username.encode(encoding), realm, password.encode(encoding))).hexdigest()
        hda2 = hashlib.md5('GET:' + uri).hexdigest()
        sig = '%s:%s:%s:%s:%s:%s' % (hda1, nonce, nc, cnonce, qop, hda2)

        # Compare our hash with the response
        return hashlib.md5(sig).hexdigest() == response

    def denies(self, detail):
        """Method called when a permission is denied

        In:
          - ``details`` -- a ``security.common.denial`` object
        """
        nonce = hashlib.md5('%s:%s' % (str(time.time()), self.private_key)).hexdigest()

        raise webob.exc.HTTPUnauthorized(
                                         str(detail),
                                         [('WWW-Authenticate', 'Digest realm="%s", nonce="%s", qop="auth"' % (self.realm, nonce))]
                                        )
