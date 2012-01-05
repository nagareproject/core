#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
"""Callbacks manager

Manage:

  - id / callbacks association
  - list of the callbacks registered for a componant
"""

import random

from nagare.component import call_wrapper

class CallbackLookupError(LookupError):
    pass


class Callbacks:
    """Callback manager

    ``self.callbacks`` is a list of tuple (component, callbacks dictionary)
    where the callback dictionay associated the id of the callback to the
    callback tuple (action function, render function)
    """
    def __init__(self):
        self.callbacks = []

    def _search_by_component(self, component):
        """Search the callbacks of a component

        In:
          - ``component`` -- the component

        Return:
          - the dictionary of the callbacks or ``None`` if component not found
        """
        for (b, c) in self.callbacks:
            if b == component:
                return c

        return None

    def clear_not_used(self, components):
        """Keep only the callbacks of the given components

        In:
          - ``components`` -- list of the components we want to keep the callbacks
        """
        self.callbacks = [x for x in self.callbacks if x[0] in components]

    def unregister_callbacks(self, component):
        """Clear all the callbacks of a component

        In:
          - ``component`` -- the component
        """
        # Retrieve the dictionary of the callbacks of the component
        callbacks = self._search_by_component(component)
        if callbacks is not None:
            # Clear the dictionary
            callbacks.clear()

    def register_callback(self, component, priority, callback, with_request, render):
        """Register a callback

        In:
          - ``component`` -- the component associated to the callback
          - ``priority`` -- type of the callback

            - 0 : <form>.pre_action
            - 1 : action with value (<textarea>, checkbox ...)
            - 2 : action without value (radio button)
            - 3 : <form>.post_action
            - 4 : action with continuation and without value (<a>, submit button ...)
            - 5 : action with continuation and with value (special case for >input type='image'>)

          - ``callback`` -- the action function or method
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``render`` -- the render function or method

        Return:
          - the callback identifier
        """
        id = random.randint(10000000, 99999999)

        # Retrieve the dictionary of the callbacks of the component
        callbacks = self._search_by_component(component)
        if callbacks is None:
            # Create a new dictionary
            callbacks = {}
            self.callbacks.append((component, callbacks))

        # Remember the action and render functions
        callbacks[id] = (callback, with_request, render)

        return '_action%d%08d' % (priority, id)

    def _search_by_callback_name(self, name):
        """Search a callback among all the component

        In:
          -- ``name`` -- callback identifier

        Return:
          -- the tuple (action function, render function)
             or (``None``, ``None``) is not found
        """
        for (component, callbacks) in self.callbacks:
            r = callbacks.get(name)
            if r is not None:
                return r

        raise CallbackLookupError(name)

    def process_response(self, request, response):
        """Call the actions associated to the callback identifiers received

        In:
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
        callback_type = 0

        for ((callback_type, _), name, param, value) in sorted(actions.values()):
            (f, with_request, render) = self._search_by_callback_name(name)
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
                    call_wrapper(f, request, response)
                elif callback_type == 5:
                    if param.endswith(('.x', '.y')):
                        call_wrapper(f, request, response, param.endswith('.y'), int(value))
                else: # 0, 2, 3
                    f(request, response)
            else:
                if callback_type == 1:
                    f(value)
                elif callback_type == 4:
                    call_wrapper(f)
                elif callback_type == 5:
                    if param.endswith(('.x', '.y')):
                        call_wrapper(f, param.endswith('.y'), int(value))
                else: # 0, 2, 3
                    f()

        return render
