# --
# Copyright (c) 2008-2025 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --


from nagare.component import Component
from nagare.services.http_session import SessionService


def persistent_id(o, clean_callbacks, result):
    """An object with a ``_persistent_id`` attribute is stored into the session not into the state snapshot.

    In:
    - ``o`` -- object to check
    - ``clean_callbacks`` -- do we have to forget the old callbacks?

    Out:
    - ``result`` -- object with attributes:
      - ``callbacks`` -- merge of the callbacks from all the components
      - ``session_data`` -- dict persistent_id -> object of the objects to store into the session

    Return:
    - the persistent id or ``None``
    """
    r = None

    id_ = getattr(o, '_persistent_id', None)
    if id_ is not None:
        result.session_data[id_] = o
        r = str(id_)

    return r


class StateService(SessionService):
    LOAD_PRIORITY = SessionService.LOAD_PRIORITY + 1
    CONFIG_SPEC = SessionService.CONFIG_SPEC | {
        'states_history': 'boolean(default=True)',
        'session_cookie': {'name': 'string(default="")'},
        'send_response': 'boolean(default=True)',
    }

    def __init__(self, name, dist, send_response, services_service, session_service, **config):
        services_service(super().__init__, name, dist, send_response=send_response, **config)

        session_service.set_persistent_id(persistent_id)
        session_service.set_dispatch_table(self.set_dispatch_table)

        self.send_response = send_response

    def set_dispatch_table(self, clean_callbacks, result):
        return {Component: lambda comp: comp.reduce(clean_callbacks, result)}

    def _handle_request(self, request, start_response, response, **params):
        write = start_response(response.status, response.headerlist)

        if self.send_response and (write is not None):
            write(response.body)
            return lambda environ, start_response: []

        return lambda environ, start_response: [response.body]
