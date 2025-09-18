# --
# Copyright (c) 2008-2025 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --
"""Callbacks manager.

Manage the dictionary of the ids / callbacks associations
"""

import os
import re
import json
import base64
import contextlib
from collections import defaultdict

from webob import exc
from tinyaes import AES

from nagare import partial
from nagare.services import plugin
from nagare.component import CallAnswered, call_wrapper

PRE_ACTION_CALLBACK = 0  # <form>.pre_action
WITH_VALUE_CALLBACK = 1  # <textarea>, <input type="text">
WITHOUT_VALUE_CALLBACK = 2  # <input type="radio">, <input type="checkbox">, single select
WITH_VALUES_CALLBACK = 3  # # multiple select
POST_ACTION_CALLBACK = 4  # <form>.post_action
LINK_CALLBACK = 5  # <a>
SUBMIT_CALLBACK = 6  # <input type="submit">, <button>
IMAGE_CALLBACK = 7  # <input type='image'>

WITH_CONTINUATION_CALLBACK = 1 << 4

ACTION_PREFIX = '_action'
ACTION_SYNTAX = re.compile(ACTION_PREFIX + r'((0|1)(\d))(\d+)((.x)|(.y))?(#(.*))?$')

callbacks_service = None


class CallbackLookupError(LookupError):
    pass


class CallbacksService(plugin.Plugin):
    LOAD_PRIORITY = 110

    def __init__(self, name, dist, **config):
        global callbacks_service
        super().__init__(name, dist, **config)

        self.key = os.urandom(16)
        callbacks_service = self

    @staticmethod
    def pad(buf, length, padding):
        nb = len(buf) % length
        return buf + padding * (nb and (length - nb))

    def encode_client_params(self, client_params):
        if not client_params:
            return ''

        v = json.dumps(client_params).encode('utf-8')
        v = self.pad(v + b'#', 16, b' ')
        AES(self.key).CBC_encrypt_buffer_inplace_raw(v)
        v = base64.urlsafe_b64encode(v).decode('ascii')

        return v

    def decode_client_params(self, client_params):
        if not client_params:
            return {}

        v = base64.urlsafe_b64decode(client_params)
        AES(self.key).CBC_decrypt_buffer_inplace_raw(v)
        v = v.rstrip(b' ')
        if not v.endswith(b'#'):
            raise exc.HTTPNotFound()

        return json.loads(v[:-1])

    @staticmethod
    def execute_callback(callback_type, callback, args, kw):
        with contextlib.suppress(CallAnswered):
            if callback_type & WITH_CONTINUATION_CALLBACK:
                return call_wrapper(callback, *args, **kw)
            else:
                return callback(*args, **kw)

    def handle_request(self, chain, callbacks, request, response, root, **params):
        """Call the actions associated to the callback identifiers received.

        In:
          - ``callbacks`` -- dictionary where the keys are the callback ids and the
            values are tuples (callback, with_request, render)
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - the render function
        """
        # The structure of a callback identifier is
        # '_action<with continuation on 1 char><priority on 1 chars><key into the callbacks dictionary>'
        actions = defaultdict(list)

        for name, value in request.params.items():
            if isinstance(value, str) and value.startswith(ACTION_PREFIX):
                name = value  # For the radio buttons, the callback identifier is the value, not the name

            m = ACTION_SYNTAX.match(name)
            if m:
                groups = m.groups()
                actions[(int(groups[2]), int(groups[0], 16), groups[3], groups[4], groups[-1])].append(value)

        render = None

        for (type_, callback_type, callback_id, complement, client_params), values in sorted(
            actions.items(), key=lambda e: (e[0][0], e[0][1])
        ):
            try:
                f, with_request, render, callback_args, kw = callbacks[int(callback_id)]
            except KeyError:
                exc = CallbackLookupError(callback_id)
                exc.__cause__ = None
                raise exc

            if f is None:
                continue

            callback_params = self.decode_client_params(client_params) | kw

            if with_request:
                f = partial.Partial(f, request, response)

            if type_ == WITH_VALUES_CALLBACK:
                self.execute_callback(callback_type, f, callback_args + (tuple(values),), callback_params)
            else:
                for value in values:
                    args = callback_args

                    if type_ == LINK_CALLBACK:
                        callback_params = self.decode_client_params(value) | kw
                    elif type_ == WITH_VALUE_CALLBACK:
                        args += (value,)
                    elif (type_ == IMAGE_CALLBACK) and complement:
                        args += (complement == '.y', int(values[0]))

                    self.execute_callback(callback_type, f, args, callback_params)

        return chain.next(
            callbacks=callbacks,
            request=request,
            response=response,
            root=root,
            render=(render or (lambda h: '')) if request.is_xhr or render else root.render,
            **params,
        )
