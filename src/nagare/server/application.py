# --
# Copyright (c) 2008-2025 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from webob.multidict import MultiDict, NestedMultiDict

from nagare.server import mvc_application
from nagare.services import router
from nagare.renderers import html5


class Request(mvc_application.Request):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.client_params = {}

    @property
    def POST(self):
        if 'webob._parsed_post_vars' in self.environ:
            vars = super().POST
        else:
            vars = MultiDict()

            for names, values in super().POST.items():
                if names.startswith('|_action'):
                    names = names.strip('|').split('|')
                    complement = names.pop(-1) if (names[-1] == '.x') or (names[-1] == '.y') else ''
                    for name in names:
                        vars.add(name + complement, values)
                elif isinstance(values, str) and values.startswith('|_action'):
                    for value in values.strip('|').split('|'):
                        vars.add(names, value)
                else:
                    vars.add(names, values)

            self.environ['webob._parsed_post_vars'] = (vars, self.body_file_raw)

        return vars

    @property
    def params(self):
        return NestedMultiDict(super().params, self.client_params)


class App(mvc_application.App):
    renderer_factory = html5.Renderer

    @staticmethod
    def create_request(environ, *args, **kw):
        """Parse the REST environment received.

        In:
          - ``environ`` -- the WSGI environment

        Return:
          - a ``WebOb`` Request object
        """
        return Request(environ, charset='utf-8', *args, **kw)

    def create_renderer(
        self, session_id=None, state_id=None, request=None, response=None, assets_version=None, **params
    ):
        """Create the initial renderer (the root of all the used renderers).

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
        """
        renderer = self.renderer_factory(
            None,
            session_id,
            state_id,
            request,
            response,
            self.static_url,
            self.static_path,
            self.url,
            assets_version=assets_version,
        )

        if (request is not None) and request.is_xhr:
            renderer = renderer.async_renderer_factory(
                None,
                session_id,
                state_id,
                request,
                response,
                self.static_url,
                self.static_path,
                self.url,
                assets_version=assets_version,
            )

        return renderer

    @staticmethod
    def handle_request(chain, response, **params):
        return response

    def create_dispatch_args(self, root, **params):
        return (self,) + self.router.create_dispatch_args(**params) + (root,)

    # ---------------------------------------------------------------------------------------

    def create_root(self, *args, **kw):
        """Create the application root component.

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
