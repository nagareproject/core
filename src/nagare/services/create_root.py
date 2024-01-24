# --
# Copyright (c) 2008-2024 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from nagare.services import plugin


class RootService(plugin.Plugin):
    LOAD_PRIORITY = 109

    def create_root(self, app, **params):
        root = app.create_root()

        # Initialize the objects graph from the URL
        args = app.create_dispatch_args(root=root, **params)
        app.route(args)

        return root

    def handle_request(self, chain, session, **params):
        if session:
            root = session['nagare.root']
        else:
            root = session['nagare.root'] = self.create_root(**params)

        return chain.next(session=session, root=root, **params)
