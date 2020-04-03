# --
# Copyright (c) 2008-2020 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import sys

from nagare.component import Component
from nagare.continuation import Tasklet
from nagare.services.http_session import SessionService

from webob import exc


PY2 = (sys.version_info.major == 2)


def persistent_id(o, clean_callbacks, callbacks, session_data, tasklets):
    """An object with a ``_persistent_id`` attribute is stored into the session
    not into the state snapshot

    In:
    - ``o`` -- object to check
    - ``clean_callbacks`` -- do we have to forget the old callbacks?

    Out:
    - ``callbacks`` -- merge of the callbacks from all the components
    - ``session_data`` -- dict persistent_id -> object of the objects to store into the session
    - ``tasklets`` -- set of the serialized tasklets

    Return:
    - the persistent id or ``None``
    """
    r = None

    id_ = getattr(o, '_persistent_id', None)
    if id_ is not None:
        session_data[id_] = o
        r = str(id_)

    elif (Tasklet is not None) and (type(o) is Tasklet):
        tasklets.add(o)

    elif PY2 and isinstance(o, Component):
        callbacks.update(o.serialize_actions(clean_callbacks))

    return r


class EmptyResponse(exc.HTTPOk):

    def __call__(self, environ, start_response):
        return []


class StateService(SessionService):
    LOAD_PRIORITY = SessionService.LOAD_PRIORITY + 1
    CONFIG_SPEC = dict(
        SessionService.CONFIG_SPEC,
        states_history='boolean(default=True)',
        session_cookie={'name': 'string(default="")'}
    )

    def __init__(self, name, dist, services_service, session_service, **config):
        services_service(super(StateService, self).__init__, name, dist, **config)

        session_service.set_persistent_id(persistent_id)
        session_service.set_dispatch_table(self.set_dispatch_table)

    def set_dispatch_table(self, clean_callbacks, callbacks):
        return {Component: lambda comp: comp.reduce(clean_callbacks, callbacks)}

    @staticmethod
    def _handle_request(request, start_response, response, **params):
        start_response(response.status, response.headerlist)(response.body)

        return EmptyResponse()
