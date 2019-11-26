# --
# Copyright (c) 2008-2019 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""If the ``activated`` parameter of the ``[redirect_after_post]``
section is `on`` (the default), conform to the PRG__ pattern

 __ http://en.wikipedia.org/wiki/Post/Redirect/GetPRG
"""

from nagare.services import plugin


class PRGService(plugin.Plugin):
    LOAD_PRIORITY = 120

    @staticmethod
    def handle_request(chain, request, session_id, previous_state_id, **params):
        if (request.method == 'POST') and not request.is_xhr:
            response = request.create_redirect_response(
                _s=session_id,
                _c='%05d' % previous_state_id
            )
            response.use_same_state = True
        else:
            response = chain.next(
                request=request,
                session_id=session_id,
                previous_state_id=previous_state_id,
                **params
            )

        return response
