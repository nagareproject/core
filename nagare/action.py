# --
# Copyright (c) 2008-2019 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import os
import json
import base64
import random
import inspect
try:
    from inspect import getfullargspec as getargspec
except ImportError:
    from inspect import getargspec

from webob import exc
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from nagare import partial
from nagare.renderers import xml


class ActionBase(object):
    def __init__(self, action):
        self.action = action

    @staticmethod
    def register(component, view, action, action_type, with_request, render, args, kw):
        k = (view, action, action_type, with_request, args, tuple(kw.items()))

        try:
            action_id = abs(hash(k))
        except TypeError:
            action_id = random.randint(10000000, 99999999)

        component.register_action(
            action_id,
            view,
            action,
            with_request,
            render,
            args,
            kw
        )

        return '_action%d%08d' % (action_type, action_id)


class Action(ActionBase):

    def __init__(self, action):
        super(Action, self).__init__(action)

        self.with_request = False
        self.client_params = frozenset()
        self.key = b''

    @staticmethod
    def pad(buf, l, padding):
        nb = len(buf) % l
        return buf + padding * ((l - nb) if nb else 0)

    def encode_client_params(self, client_params):
        self.key = self.key or os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.ECB(), default_backend())
        encryptor = cipher.encryptor()

        v = json.dumps(client_params).encode('utf-8')
        v = self.pad(v + b'#', 16, b' ')
        v = encryptor.update(v) + encryptor.finalize()
        v = base64.urlsafe_b64encode(v).decode('ascii')

        return v

    def decode_client_params(self, client_params):
        if not client_params:
            return {}

        cipher = Cipher(algorithms.AES(self.key), modes.ECB(), default_backend())
        decryptor = cipher.decryptor()

        v = base64.urlsafe_b64decode(client_params)
        v = decryptor.update(v) + decryptor.finalize()
        v = v.rstrip(b' ')
        if not v.endswith(b'#'):
            raise exc.HTTPNotFound()

        return json.loads(v[:-1])

    def generate_render(self, renderer):
        return None

    @staticmethod
    def set_action(tag, action_id, params):
        tag.set_sync_action(action_id, params)

    def register(self, renderer, component, tag, action_type, view, with_request, args, kw, register_self=False):
        self.with_request = with_request
        client_params = {k: kw.pop(k) for k in list(kw) if k.startswith('c_')}
        self.client_params = frozenset(client_params)

        action_id = super(Action, self).register(
            component,
            view,
            self.action if not register_self and not client_params else self,
            action_type,
            bool(client_params) or with_request,
            self.generate_render(renderer),
            args, kw
        )

        if client_params:
            client_params = self.encode_client_params(client_params)

        return self.set_action(tag, action_id, client_params)

    def __call__(self, request, response, *args, **kw):
        client_params = request.params.get('_p', {})
        if client_params:
            client_params = self.decode_client_params(client_params)
            if set(client_params) != self.client_params:
                raise exc.HTTPNotFound()

        args = ((request, response) if self.with_request else ()) + args
        kw.update(client_params)
        self.action(*args, **kw)


class Remote(ActionBase):

    def __init__(self, action, with_request=False):
        args_spec = getargspec(action)
        if any(args_spec[1:]):
            raise TypeError('only positional parameters allowed in a `{}` action'.format(self.__class__.__name__))

        super(Remote, self).__init__(action)

        self.with_request = with_request

        if inspect.isclass(action):
            action = action.__init__ if inspect.isroutine(action.__init__) else lambda: None

        ignored_params = (2 if with_request else 0) + inspect.ismethod(action)

        self.names = args_spec.args[ignored_params:]

    def render(self, renderer):
        request = renderer.request
        response = renderer.response

        params = json.loads(request.params['_params'])
        args = ([request, response] if self.with_request else []) + [params[name] for name in self.names]

        response.content_type = 'text/plain'
        return json.dumps(self.action(*args))

    def register(self, renderer, component, tag, action_type, view, with_request, args, kw):
        renderer.include_ajax()

        action_id = super(Remote, self).register(
            component,
            view,
            lambda *args, **kw: None,
            action_type,
            True,
            self.render,
            args, kw
        )

        url = renderer.add_sessionid_in_url('', {action_id: ''})
        return 'function (%s) { return nagare_callRemote("%s", {%s}) }' % (
            ', '.join(self.names),
            url,
            ', '.join('"%s": %s' % (name, name) for name in self.names)
        )


class Update(Action):
    """Asynchronous updater object

    Send a XHR request that can do an action, render a component and finally
    update the HTML with the rendered view
    """
    # @partial.max_number_of_args(4)
    def __init__(self, action=lambda *args, **kw: None, render='', component_to_update=None):
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
        async_root = renderer.async_root
        if not self.component_to_update and (async_root is None):
            raise ValueError('no async root found')

        renderer.include_ajax()

        view = ()
        render = self.render

        if not callable(render):
            view = (render if render != '' else async_root.view,)
            render = async_root.component.render

        return partial.Partial(
            self.generate_response if with_header else self.generate_response_body,
            render, view,
            self.component_to_update or async_root.id
        )

    @staticmethod
    def generate_response_body(render, view, component_to_update, renderer):
        html = render(renderer, *view)
        html.set('id', html.get('id', component_to_update))

        return b"nagare_replaceNode('%b', %b)" % (
            component_to_update.encode('ascii'),
            json.dumps(html.tostring().decode('utf-8')).encode('utf-8')
        )

    @staticmethod
    def generate_response_head(head, response):
        response.content_type = 'text/plain'

        return head.render_async().encode(response.charset)

    def generate_response(self, render, view, component_to_update, renderer):
        body = self.generate_response_body(render, view, component_to_update, renderer)
        head = self.generate_response_head(renderer.head, renderer.response)

        return body + b'; ' + head


class Updates(Update):

    @partial.max_number_of_args(1)
    def __init__(self, args, action=lambda *args, **kw: None):
        """Initialization

        In:
          - ``args`` -- the list of ``Update`` objects
          - ``action`` -- global action to execute
          - ``kw`` -- ``action`` parameters
          - ``with_request`` -- will the request and response objects be passed to the global action?
          - ``permissions`` -- permissions needed to execute the global action
          - ``subject`` -- subject to test the permissions on
        """
        super(Updates, self).__init__(action)

        self.updates = args
        self.with_request = False

    def register(self, renderer, component, tag, action_type, view, with_request, args, kw):
        super(Updates, self).register(renderer, component, tag, action_type, view, True, args, kw, True)
        self.with_request = with_request

        for update in self.updates:
            update.with_request = with_request

    def __call__(self, request, response, *args, **kw):
        super(Updates, self).__call__(request, response, *args, **kw)

        for update in self.updates:
            update(request, response, *args, **kw)

    def generate_response(self, renders, renderer):
        body = b'; '.join(render(renderer) for render in renders)
        head = self.generate_response_head(renderer.head, renderer.response)

        return body + b'; ' + head

    def generate_render(self, renderer):
        renders = [update.generate_render(renderer, False) for update in self.updates]
        return partial.Partial(self.generate_response, renders)
