# --
# Copyright (c) 2008-2021 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from webob.multidict import NestedMultiDict

from nagare.services import router
from nagare.server import mvc_application

from nagare.renderers import html5


class Request(mvc_application.Request):
    def __init__(self, *args, **kw):
        super(Request, self).__init__(*args, **kw)
        self.client_params = {}

    @property
    def params(self):
        return NestedMultiDict(super(Request, self).params, self.client_params)


class App(mvc_application.App):
    renderer_factory = html5.Renderer

    @staticmethod
    def create_request(environ, *args, **kw):
        """Parse the REST environment received

        In:
          - ``environ`` -- the WSGI environment

        Return:
          - a ``WebOb`` Request object
        """
        return Request(environ, charset='utf-8', *args, **kw)

    def create_renderer(self, session_id, state_id, request, response, assets_version=None, **params):
        """Create the initial renderer (the root of all the used renderers)

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
        """
        renderer = self.renderer_factory(
            None,
            session_id, state_id,
            request, response,
            self.static_url, self.static_path,
            self.url,
            assets_version=assets_version
        )

        if request.is_xhr:
            renderer = renderer.async_renderer_factory(
                None,
                session_id, state_id,
                request, response,
                self.static_url, self.static_path,
                self.url,
                assets_version=assets_version
            )

        return renderer

    @staticmethod
    def handle_request(chain, response, **params):
        return response

    def create_dispatch_args(self, root, **params):
        return (self,) + self.router.create_dispatch_args(**params) + (root,)

    # ---------------------------------------------------------------------------------------

    def create_root(self, *args, **kw):
        """Create the application root component

        Return:
          - the root component
        """
        raise NotImplementedError()


@router.route_for(App, '', ())
def route_without_url(self, root, url, method, request, response):
    pass


@router.route_for(App, '{url2:.+}', ())
def route(self, root, url, method, request, response, url2):
    return root, url, method, request, response
