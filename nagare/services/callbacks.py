# --
# Copyright (c) 2008-2019 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --
"""Callbacks manager

Manage the dictionary of the ids / callbacks associations
"""

import re
from collections import defaultdict

from nagare import partial
from nagare.services import plugin
from nagare.continuation import Continuation

ACTION_PREFIX = '_action'
ACTION_SYNTAX = re.compile(ACTION_PREFIX + r'(\d)(\d+)((.x)|(.y))?(#(.*))?$')


class CallbackLookupError(LookupError):
    pass


class CallbacksService(plugin.Plugin):
    LOAD_PRIORITY = 110

    @classmethod
    def handle_request(cls, chain, callbacks, request, response, root, **params):
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

        for (callback_type, callback_id, param, client_params), values in sorted(actions.items()):
            request.client_params['_p'] = client_params or {}

            try:
                _, f, with_request, render, args, kw = callbacks[int(callback_id)]
            except KeyError:
                raise CallbackLookupError(callback_id)

            if f is None:
                continue

            # ``callback_type``:
            #
            # 0 : <form>.pre_action
            # 1 : action with value (<textarea> ...)
            # 2 : action without value (radio button, checkbox ..)
            # 3 : action with multiple values (multiple select)
            # 4 : <form>.post_action
            # 5 : action with continuation and without value (<a> and submit button)
            # 6 : action with continuation and with value (special case for <input type='image'>)

            if with_request:
                f = partial.Partial(f, request, response)

            if callback_type == '3':
                f(*(args + (tuple(values),)), **kw)
            else:
                for value in values:
                    if callback_type == '1':
                        f(*(args + (value,)), **kw)
                    elif (callback_type == '4') or (callback_type == '5'):
                        Continuation(f, *args, **kw)
                    elif (callback_type == '6') and param:
                        args += (param == '.y', int(values[0]))
                        Continuation(f, *args, **kw)
                    elif callback_type in ('0', '2'):
                        f(*args, **kw)

        return chain.next(
            callbacks=callbacks,
            request=request, response=response,
            root=root, render=render or root.render,
            **params
        )
