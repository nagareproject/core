# --
# Copyright (c) 2008-2025 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Post Redirect Get pattern.

If the ``activated`` parameter of the ``[redirect_after_post]``
section is `on`` (the default), conform to the PRG__ pattern

 __ http://en.wikipedia.org/wiki/Post/Redirect/GetPRG
"""

from nagare.services import plugin


class PRGService(plugin.Plugin):
    LOAD_PRIORITY = 120

    @staticmethod
    def handle_request(chain, request, response, session_id, state_id, **params):
        if (request.method == 'POST') and not request.is_xhr:
            response = request.create_redirect_response(response=response, _s=session_id, _c='%05d' % state_id)
        else:
            response = chain.next(
                request=request, response=response, session_id=session_id, state_id=state_id, **params
            )

        return response
