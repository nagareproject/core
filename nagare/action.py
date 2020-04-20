# --
# Copyright (c) 2008-2020 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import json
import random

from nagare import partial
from nagare.renderers import xml
from nagare.services.callbacks import callbacks_service


def no_action(*args, **kw):
    return b''


class ActionBase(object):

    @staticmethod
    def register(component, action_type, view, with_request, args, kw, action, render):
        client_params = {k[:-2]: kw.pop(k) for k in list(kw) if k.endswith('_c')}
        client_params = callbacks_service.encode_client_params(client_params)

        action_id = component.register_action(view, action, with_request, render, args, kw)
        action_id = '_action%d%08d' % (action_type, action_id)

        return action_id, client_params


class Action(ActionBase):

    def __init__(self, action=no_action):
        super(Action, self).__init__()
        self.action = action

    @staticmethod
    def generate_render(renderer):
        return None

    @staticmethod
    def set_action(tag, action_id, params):
        tag.set_sync_action(action_id, params)

    def register(self, renderer, component, tag, action_type, view, with_request, args, kw, action=None):
        action_id, client_params = super(Action, self).register(
            component,
            action_type,
            view,
            with_request,
            args, kw,
            action or self.action, self.generate_render(renderer)
        )

        self.set_action(tag, action_id, client_params)

        return action_id, client_params


class Update(Action):
    """Asynchronous updater object

    Send a XHR request that can do an action, render a component and finally
    update the HTML with the rendered view
    """
    def __init__(self, action=no_action, render='', component_to_update=None):
        """Initialisation

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
        super(Update, self).__init__(action)
        self.render = render

        if isinstance(component_to_update, xml.Tag):
            self.component_to_update = component_to_update.get('id') or ('update_%s' % random.randint(10000000, 99999999))
            component_to_update.set('id', self.component_to_update)
        else:
            self.component_to_update = component_to_update

    @staticmethod
    def set_action(tag, action_id, params):
        tag.set_async_action(action_id, params)

    def generate_render(self, renderer, with_header=True):
        """Generate the rendering function

        In:
          - ``renderer`` -- the current renderer

        Return:
          - the rendering function
        """
        renderer.include_nagare_js()

        render = self.render
        if render is None:
            return no_action

        async_root, (args, kw) = renderer.async_root
        if not self.component_to_update and (async_root is None):
            raise ValueError('no async root found and no `component_to_update` defined')

        if callable(render):
            view = ()
            params = {}
        else:
            view = (render if render != '' else async_root.view,) + args
            render = async_root.component.render
            params = kw

        return partial.Partial(
            self.generate_response if with_header else self.generate_response_body,
            render, view,
            self.component_to_update or async_root.id,
            params
        )

    @staticmethod
    def generate_response_body(render, view, component_to_update, params, renderer):
        html = render(renderer, *view, **params)
        html.set('id', html.get('id', component_to_update))

        return b"nagare.replaceNode('%s', %s)" % (
            component_to_update.encode('ascii'),
            json.dumps(html.tostring().decode('utf-8')).encode('utf-8')
        )

    @staticmethod
    def generate_response_head(head, response):
        response.content_type = 'text/plain'

        return head.render_async().encode(response.charset)

    @classmethod
    def generate_response(cls, render, view, component_to_update, params, renderer):
        body = cls.generate_response_body(render, view, component_to_update, params, renderer)
        head = cls.generate_response_head(renderer.head, renderer.response)

        return body + b'; ' + head


class Updates(Update):

    @partial.max_number_of_args(1)
    def __init__(self, args, action=no_action):
        """Initialization

        In:
          - ``args`` -- the list of ``Update`` objects
          - ``action`` -- global action to execute
        """
        super(Updates, self).__init__(action)
        self.updates = args

    def register(self, renderer, component, tag, action_type, view, with_request, args, kw):
        actions = [self.action] + [update.action for update in self.updates]

        def action(request, response, *args, **kw):
            for action in actions:
                if with_request:
                    action(request, response, *args, **kw)
                else:
                    action(*args, **kw)

        return super(Updates, self).register(renderer, component, tag, action_type, view, True, args, kw, action)

    def generate_render(self, renderer):
        renders = [update.generate_render(renderer, False) for update in self.updates]
        return partial.Partial(self.generate_response, renders)

    @classmethod
    def generate_response(cls, renders, renderer):
        body = b'; '.join(render(renderer) for render in renders)
        head = cls.generate_response_head(renderer.head, renderer.response)

        return body + b'; ' + head
