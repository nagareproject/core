# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --
"""Callbacks manager

Manage the dictionary of the ids / callbacks associations
"""

import random

from nagare.continuation import Continuation


class CallbackLookupError(LookupError):
    pass


def register(model, priority, callback, with_request, render, callbacks):
    """Register a callback

    In:
      - ``model`` -- name of the view which registers this callback (``None`` for the default view)
      - ``priority`` -- type of the callback

        - 0 : <form>.pre_action
        - 1 : action with value (<textarea>, checkbox ...)
        - 2 : action without value (radio button)
        - 3 : <form>.post_action
        - 4 : action with continuation and without value (<a>, submit button ...)
        - 5 : action with continuation and with value (special case for >input type='image'>)

      - ``callback`` -- the action function or method
      - ``with_request`` -- will the request and response objects be passed to the action?
      - ``render`` -- the render function or method

    Out:
      - ``callbacks`` -- dictionary where the keys are the callback ids and the
        values are tuples (callback, with_request, render)

    Return:
      - the callback identifier
    """
    id_ = random.randint(10000000, 99999999)

    # Remember the model, the action and the rendering function
    callbacks[id_] = (model, callback, with_request, render)

    return '_action%d%08d' % (priority, id_)


def clean(old, new):
    """Keep the old callbacks registered by a view only if this view has not registered new callbacks

    In:
      - ``old`` -- the old registered callbacks
      - ``new`` -- the new registered callbacks
    """
    # Retrieve all views which has registered new callbacks
    models = set(callback[0] for callback in new.itervalues())

    # Keep only the old callbacks of a view if no new callbacks were registered
    return dict((k, v) for k, v in old.iteritems() if v[0] not in models)


def process(callbacks, request, response):
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
    actions = {}

    try:
        for (name, value) in request.params.items():
            if isinstance(value, basestring) and value.startswith('_action'):
                # For the radio buttons, the callback identifier is the value,
                # not the name
                name = value

            if name and name.startswith('_action'):
                v = actions.get(name)
                if v is not None:
                    # Multiple values for the same callback are put into a tuple
                    v = v[3]
                    value = (v if isinstance(v, tuple) else (v,)) + (value,)

                actions[name] = ((int(name[7]), len(actions)), int(name[8:16]), name, value)
    except ValueError:
        raise CallbackLookupError(name[8:])

    render = None

    for ((callback_type, _), name, param, value) in sorted(actions.values()):
        try:
            (model, f, with_request, render) = callbacks[name]
        except KeyError:
            raise CallbackLookupError(name)

        if f is None:
            continue

        # ``callback_type``:
        #
        # 0 : <form>.pre_action
        # 1 : action with value (<textarea>, checkbox ...)
        # 2 : action without value (radio button)
        # 3 : <form>.post_action
        # 4 : action with continuation and without value (<a>, submit button ...)
        # 5 : action with continuation and with value (special case for <input type='image'>)

        if with_request:
            if callback_type == 1:
                f(request, response, value)
            elif callback_type == 4:
                Continuation(f, request, response)
            elif callback_type == 5:
                if param.endswith(('.x', '.y')):
                    Continuation(f, request, response, param.endswith('.y'), int(value))
            else:  # 0, 2, 3
                f(request, response)
        else:
            if callback_type == 1:
                f(value)
            elif callback_type == 4:
                Continuation(f)
            elif callback_type == 5:
                if param.endswith(('.x', '.y')):
                    Continuation(f, param.endswith('.y'), int(value))
            else:  # 0, 2, 3
                f()

    return render
