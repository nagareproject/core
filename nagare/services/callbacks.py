# --
# Copyright (c) 2008-2020 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --
"""Callbacks manager

Manage the dictionary of the ids / callbacks associations
"""

import os
import re
import json
import base64
from collections import defaultdict

from webob import exc

from nagare import partial
from nagare.services import plugin
from nagare.continuation import Continuation

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ACTION_PREFIX = '_action'
ACTION_SYNTAX = re.compile(ACTION_PREFIX + r'(\d)(\d+)((.x)|(.y))?(#(.*))?$')

callbacks_service = None


class CallbackLookupError(LookupError):
    pass


class CallbacksService(plugin.Plugin):
    LOAD_PRIORITY = 110

    def __init__(self, name, dist, **config):
        global callbacks_service
        super(CallbacksService, self).__init__(name, dist, **config)

        key = os.urandom(16)
        self.cipher = Cipher(algorithms.AES(key), modes.ECB(), default_backend())
        callbacks_service = self

    @staticmethod
    def pad(buf, l, padding):
        nb = len(buf) % l
        return buf + padding * (nb and (l - nb))

    def encode_client_params(self, client_params):
        if not client_params:
            return ''

        encryptor = self.cipher.encryptor()

        v = json.dumps(client_params).encode('utf-8')
        v = self.pad(v + b'#', 16, b' ')
        v = encryptor.update(v) + encryptor.finalize()
        v = base64.urlsafe_b64encode(v).decode('ascii')

        return v

    def decode_client_params(self, client_params):
        if not client_params:
            return {}

        decryptor = self.cipher.decryptor()

        v = base64.urlsafe_b64decode(client_params)
        v = decryptor.update(v) + decryptor.finalize()
        v = v.rstrip(b' ')
        if not v.endswith(b'#'):
            raise exc.HTTPNotFound()

        return json.loads(v[:-1])

    def handle_request(self, chain, callbacks, request, response, root, **params):
        """Call the actions associated to the callback identifiers received

        In:
          - ``callbacks`` -- dictionary where the keys are the callback ids and the
            values are tuples (callback, with_request, render)
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - the render function
        """
        # The structure of a callback identifier is
        # '_action<priority on 1 char><key into the callbacks dictionary>'
        actions = defaultdict(list)

        for name, value in request.params.items():
            if isinstance(value, (str, type(u''))) and value.startswith(ACTION_PREFIX):
                name = value  # For the radio buttons, the callback identifier is the value, not the name

            m = ACTION_SYNTAX.match(name)
            if m:
                groups = m.groups()
                actions[(groups[0], groups[1], groups[2], groups[-1])].append(value)

        render = None

        for (callback_type, callback_id, complement, client_params), values in sorted(actions.items()):
            try:
                _, f, with_request, render, callback_args, kw = callbacks[int(callback_id)]
            except KeyError:
                raise CallbackLookupError(callback_id)

            if f is None:
                continue

            callback_params = self.decode_client_params(client_params or request.params.get('_p'))
            callback_params.update(kw)

            # ``callback_type``:
            #
            # 0 : <form>.pre_action
            # 1 : action with value (<textarea> ...)
            # 2 : action without value (radio button, checkbox ..)
            # 3 : action with multiple values (multiple select)
            # 4 : <form>.post_action
            # 5 : action with continuation and without value (<a>)
            # 6 : action with continuation and without value (submit button)
            # 7 : action with continuation and with value (special case for <input type='image'>)

            if with_request:
                f = partial.Partial(f, request, response)

            if callback_type == '3':
                f(*(callback_args + (tuple(values),)), **callback_params)
            else:
                for value in values:
                    if callback_type in ('0', '2'):
                        f(*callback_args, **callback_params)
                    elif callback_type == '1':
                        f(*(callback_args + (value,)), **callback_params)
                    elif callback_type in ('4', '5', '6'):
                        Continuation(f, *callback_args, **callback_params)
                    elif (callback_type == '7') and complement:
                        callback_args += (complement == '.y', int(values[0]))
                        Continuation(f, *callback_args, **callback_params)

        return chain.next(
            callbacks=callbacks,
            request=request, response=response,
            root=root, render=render or root.render,
            **params
        )
