# --
# Copyright (c) 2008-2025 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import json
import random

from nagare import partial, component
from nagare.services import callbacks
from nagare.renderers import xml


def no_action(*args, **kw):
    return b''


class Action:
    def __init__(self, action=no_action):
        self.action = action

    @staticmethod
    def _register(component, action_type, with_request, args, kw, action, render):
        callbacks_service = callbacks.callbacks_service
        if callbacks_service is not None:
            client_params = {k[:-2]: kw.pop(k) for k in list(kw) if k.endswith('_c')}
            client_params = callbacks_service.encode_client_params(client_params)
        else:
            client_params = ''

        action_id = component.register_action(action, with_request, render, args, kw)
        action_id = '_action%02X%08d' % (action_type, action_id)

        return action_id, client_params

    @staticmethod
    def generate_render(renderer):
        return None

    def register(self, renderer, component, tag, action_type, with_request, args, kw, action=None):
        action_id, client_params = self._register(
            component, action_type, with_request, args, kw, action or self.action, self.generate_render(renderer)
        )

        tag.set_action(action_id, client_params)


class Update(Action):
    """Asynchronous updater object.

    Send a XHR request that can do an action, render a component and finally
    update the HTML with the rendered view
    """

    JS_CALL = 'nagare.getAndEval'

    def __init__(self, action=no_action, render='', component_to_update=None):
        """Initialisation.

        In:
          - ``render`` -- can be:

            - a string -- name of the view that will be rendered on the current
              component
            - a function -- this function will be called and the result sent
              back to the client

          - ``action`` -- action to call
          - ``args``, ``kw`` -- ``action`` parameters

          - ``component_to_update`` -- can be:

            - ``None`` -- the current view will be updated
            - a string -- the DOM id of the HTML to update
            - a tag -- this tag will be updated

          - ``with_request`` -- will the request and response objects be passed to the action?

          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on
        """
        super().__init__(action)
        self._render = render

        if isinstance(component_to_update, xml.Tag):
            self.component_to_update = component_to_update.get('id') or (
                'update_%s' % random.randint(10000000, 99999999)
            )
            component_to_update.set('id', self.component_to_update)
        else:
            self.component_to_update = component_to_update

    def generate_render(self, renderer, with_header=True):
        """Generate the rendering function.

        In:
          - ``renderer`` -- the current renderer

        Return:
          - the rendering function
        """
        render = self._render
        if render is None:
            return no_action

        async_root, (view, args, kw) = renderer.async_root
        if not self.component_to_update and (async_root is None):
            raise ValueError('no async root found and no `component_to_update` defined')

        if callable(render):
            view = ()
            params = {}
        else:
            view = (render if render != '' else view,) + (args or ())
            render = async_root.component.render if async_root is not None else lambda h, view: None
            params = kw or {}

        return partial.Partial(
            self.generate_response if with_header else self.generate_response_body,
            render,
            view,
            self.component_to_update or async_root.id,
            tuple(params.items()),
        )

    @staticmethod
    def generate_response_body(render, view, component_to_update, params, renderer):
        html = render(renderer, *view, **dict(params))
        if html is None:
            return b''

        if callable(component_to_update):
            component_to_update = component_to_update()

        html.set('id', html.get('id', component_to_update))

        return b"nagare.replaceNode('%s', %s)" % (
            component_to_update.encode('ascii'),
            json.dumps(html.tostring().decode('utf-8')).encode('utf-8'),
        )

    @staticmethod
    def generate_response_head(head, response):
        response.content_type = 'text/plain'

        return head.render_async().encode(response.charset)

    @classmethod
    def generate_response(cls, render, view, component_to_update, params, renderer):
        if callable(component_to_update):
            component_to_update = component_to_update()

        body = cls.generate_response_body(render, view, component_to_update, params, renderer)
        head = cls.generate_response_head(renderer.head, renderer.response)

        return body + b'; ' + head

    def url(self, renderer, with_input=False, **kw):
        return (renderer.link if with_input else renderer.a).action(self, **kw).get('href')

    def javascript(self, renderer, with_field=False, **kw):
        return '{}("{}"{})'.format(
            self.JS_CALL, self.url(renderer, with_field, **kw), ' + nagare.getField(this)' if with_field else ''
        )

    js = javascript

    def render(self, renderer, *args, **kw):
        return self.javascript(renderer, *args, **kw)

    def register(self, renderer, component, tag, action_type, with_request, args, kw, action=None):
        tag.set_action_async()

        return super().register(renderer, component, tag, action_type, with_request, args, kw, action)


class Updates(Update):
    @partial.max_number_of_args(1)
    def __init__(self, args, action=no_action):
        """Initialization.

        In:
          - ``args`` -- the list of ``Update`` objects
          - ``action`` -- global action to execute
        """
        super().__init__(action)
        self.updates = args

    @staticmethod
    def execute_actions(request, response, action_type, actions, with_request, *args, **kw):
        callbacks_service = callbacks.callbacks_service

        for action in actions:
            if with_request:
                action = partial.Partial(action, request, response)

            callbacks_service.execute_callback(action_type, action, args, kw)

    def register(self, renderer, component, tag, action_type, with_request, args, kw):
        actions = [self.action] + [update.action for update in self.updates]

        return super().register(
            renderer,
            component,
            tag,
            action_type & ~callbacks.WITH_CONTINUATION_CALLBACK,
            True,
            (action_type, tuple(actions), with_request) + args,
            kw,
            self.execute_actions,
        )

    def generate_render(self, renderer):
        renders = [update.generate_render(renderer, False) for update in self.updates]
        return partial.Partial(self.generate_response, tuple(renders))

    @classmethod
    def generate_response(cls, renders, renderer):
        body = b'; '.join(render(renderer) for render in renders)
        head = cls.generate_response_head(renderer.head, renderer.response)

        return body + b'; ' + head


class Remote(Update, xml.Renderable):
    JS_CALL = 'nagare.callRemote'

    def __init__(self, action, *args, with_request=False, **kw):
        super().__init__(no_action, action, ' ')

        self.with_request = with_request
        self.args = args
        self.kw = kw

    def generate_response(self, render, view, component_to_update, params, renderer):
        request = renderer.request
        response = renderer.response

        if self.with_request:
            render = partial.Partial(render, request, response)

        params = json.loads(request.params.get('_params', '[]'))

        try:
            r = callbacks.callbacks_service.execute_callback(
                callbacks.WITH_CONTINUATION_CALLBACK, render, list(self.args) + params, self.kw
            )
        except component.CallAnswered:
            r = None

        response.content_type = 'application/json'
        return json.dumps(r)

    def javascript(self, renderer, name=None):
        js = super().javascript(renderer)
        if name:
            renderer.head.javascript('nagare-js-' + name, 'var {} = {};'.format(name, js))
            js = ''

        return js


class Delay(Remote):
    JS_CALL = 'nagare.delay'

    def __call__(self, renderer, delay, *args):
        params = ', '.join(json.dumps(arg) for arg in args)
        return self.javascript(renderer) + '({}{})'.format(delay, (', ' + params) if params else '')


class Repeat(Delay):
    JS_CALL = 'nagare.repeat'
