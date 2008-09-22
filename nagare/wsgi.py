#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""A ``WSGIApp`` object is an intermediary object between a publisher and the
root component of the application

A ``WSGIApp`` conforms to the WSGI interface and has a component factory. So,
each time the ``WSGIApp`` receives a request without a session id or with an
expired session id, it creates a new root component and a new session.
"""

from __future__ import with_statement

import webob
from webob import exc, acceptparse

from nagare import component, presentation, serializer, database, top, security
from nagare.security import dummy_manager
from nagare.callbacks import Callbacks
from nagare.namespaces import xhtml

# ---------------------------------------------------------------------------

class MIMEAcceptWithoutWildcards(acceptparse.Accept):
    def _match(self, item, match):
        if '*' in item:
            return False
        return super(MIMEAcceptWithoutWildcards, self)._match(item, match)

# ---------------------------------------------------------------------------

class WSGIApp(object):
    def __init__(self, root_factory):
        """Initialization

        In:
          -  ``root_factory`` -- function to create the application root component
        """
        self.root_factory = root_factory

        self.static = ''
        self.redirect_after_post = False
        self.always_html = True

        self.security = dummy_manager.Manager()

    def set_config(self, config_filename, config, error, static, publisher):
        """Read the configuration parameters

        In:
          -  ``config_filename`` -- the path to the configuration file
          - ``config`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
          - ``static`` -- the directory where the static contents of the application
            are located
          - ``publisher`` -- the publisher of the application
        """
        self.static = static

        self.redirect_after_post = config['application']['redirect_after_post']
        self.always_html = config['application']['always_html']

    def start(self, sessions):
        """Call after each process start

        In:
          - ``sessions`` -- the sessions manager for this application
        """
        self.sessions = sessions

    # -----------------------------------------------------------------------

    def on_bad_http_method(self, request, response):
        """A HTTP request other than a GET or PUT was received

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - a WSGI object, used to generate the response to the browser
        """
        return exc.HTTPMethodNotAllowed()

    def on_not_found(self, request, response):
        """A incorrect URL was received

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - a WSGI object, used to generate the response to the browser
        """
        return exc.HTTPNotFound()

    def on_incomplete_url(self, request, response):
        """An URL without an application name was received

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - a WSGI object, used to generate the response to the browser
        """
        return exc.HTTPMovedPermanently(add_slash=True)

    def on_session_expired(self, request, response):
        """The session id received is invalid

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - a WSGI object, used to generate the response to the browser
        """
        print 'Warning: expired session, creating a new one'
        return exc.HTTPMovedPermanently()

    def on_after_post(self, request, response, ids):
        """Generate a redirection after a POST

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``ids`` -- identifiers to put into the generated redirection URL

        Return:
          - a WSGI object, used to generate the response to the browser
        """
        return exc.HTTPSeeOther(
                                  headers=response.headers,
                                  location=request.path_url + '?' + '&'.join(ids)
                               )

    def on_refresh(self, request, response, h, output):
        """The user has asked for a page refresh

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``h`` -- the current renderer
          - ``output`` -- the tree for the refreshed page

        Return:
          - a tree
        """
        #print 'Warning: refresh used'
        return output

    def on_back(self, request, response, h, output):
        """The user used the back button

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``h`` -- the current renderer
          - ``output`` -- the tree for the refreshed page

        Return:
          - a tree
        """
        #print 'Warning: back used'
        return output

    # -----------------------------------------------------------------------

    def start_request(self, request, response):
        """A new request is received, set up its dedicated environment

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
        """
        security.set_manager(self.security) # Set the security manager
        security.set_user(self.security.create_user(request, response)) # Create the User object

    def create_root(self):
        """Create the application root component

        Return:
          - the root component
        """
        return self.root_factory()

    def create_renderer(self, session, request, response, callbacks):
        """Create the initial renderer (the root of all the renderers used)

        In:
          - ``session`` -- the session
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``callbacks`` -- object to register the callbacks
        """
        return xhtml.Renderer(xhtml.DummyRenderer(
                                                  session,
                                                  request, response,
                                                  callbacks,
                                                  self.static, request.script_name
                                                 ))

    # Processing phase
    def _phase1(self, params, callbacks):
        """Phase 1 of the request processing:

          - The callbacks are processed
          - The objects graph can be modified

        In:
          - ``params`` -- parameters received into the request
          - ``callbacks`` -- the registered callbacks

        Return:
          - a tuple:
            - function to render the objects graph or ``None``
            - is the objects graph modified ?
        """
        return callbacks.process_response(params)

    # Rendering phase
    def _phase2(self, request, response, output, is_xhr):
        """Final step of the phase 2

        Phase 2 of the request processing:

          - The object graph is rendered
          - No modification of the objects is allowed

        In:
          - ``session`` -- the session
          - ``request`` -- the web request object
          - ``output`` -- the rendered tree
          - ``is_xhr`` -- is the request a XHR request ?

        Return:
          - the content to send back to the browser
        """
        output = serializer.serialize(output, request, response,not is_xhr)

        response.content_length = len(output)
        response.charset = 'utf-8'
        response.body_file.write(output)

        return output

    def __call__(self, environ, start_response):
        """WSGI interface

        In:
          - ``environ`` -- dictionary of the received elements
          - ``start_response`` -- callback to send the headers to the browser

        Return:
          - the content to send back to the browser
        """

        # Create the ``WebOb`` request and response objects
        # -------------------------------------------------

        request = webob.Request(environ, charset='utf-8')
        response = webob.Response(headerlist=[])
        
        accept = MIMEAcceptWithoutWildcards('Accept', 'text/html' if self.always_html else str(request.accept))
        request.xhtml_output = accept.best_match(('text/html', 'application/xhtml+xml')) == 'application/xhtml+xml'

        self.start_request(request, response)

        xhr_request = request.is_xhr or ('_a' in request.params)

        # Test the request validity
        # -------------------------

        if request.method not in ('GET', 'POST'):
            return self.on_bad_http_method(request, response)(environ, start_response)

        if len(request.path_info) == 0:
            return self.on_incomplete_url(request, response)(environ, start_response)

        session = self.sessions(request, response)
        if session.is_expired:
            return self.on_session_expired(request, response)(environ, start_response)

        if session.is_new:
            # A new session is created, create a new application root component too
            root = self.create_root()

            # If a URL is given, initialize the objects graph with it
            url = request.path_info.strip('/')
            if url and presentation.init(root, [u.decode('utf-8') for u in url.split('/')], request, None) == presentation.NOT_FOUND:
                return self.on_not_found(request, response)(environ, start_response)

            # Create a new callbacks registry
            callbacks = Callbacks()
        else:
            # An existing session is used, retrieve the application root component
            # and the callbacks registry
            (root, callbacks) = session.data

        try:
            # Phase 1
            # -------

            # Create a database transaction for each request
            database.session.clear()
            with database.session.begin():
                (render, store_session) = self._phase1(request.params, callbacks)

            # If the ``redirect_after_post`` parameter of the ``[application``
            # section is `True`` (the default), conform to the PRG__ pattern
            #
            # __ http://en.wikipedia.org/wiki/Post/Redirect/GetPRG
            if (request.method == 'POST') and not xhr_request and self.redirect_after_post:
                session.set((root, callbacks), None, False)
                return self.on_after_post(request, response, session.sessionid_in_url(request, response))(environ, start_response)

            # Phase 2
            # -------

            # Create a new renderer
            renderer = self.create_renderer(session, request, response, callbacks)
            # If the phase 1 has returned a render function, use it
            # else, start the rendering by the application root component
            output = render(renderer) if render else root.render(renderer)
        except exc.HTTPException, e:
            return e(environ, start_response)

        if session.refresh_used:
            output = self.on_refresh(request, response, renderer, output)
        elif session.back_used:
            output = self.on_back(request, response, renderer, output)

        if not xhr_request:
            output = top.wrap(response.content_type, renderer, output)

        self._phase2(request, response, output, render is not None)

        if not xhr_request:
            callbacks.clear_not_used(renderer._rendered)

        # Store the session
        if store_session:
            session.set((root, callbacks), request.query_string)

        callbacks.end_rendering()

        return response(environ, start_response)

# ---------------------------------------------------------------------------

def create_WSGIApp(app, with_component=True):
    """Helper function to create a WSGIApp

    If ``app`` is not a ``WSGIApp``, it's wrap into a ``WSGIApp``. And, if
    ``with_component`` is True, each time a new root object is created, it's
    automatically wrap into a ``component.Component``.

    In:
      - ``app`` -- the application root component factory
      - ``with_component`` -- wrap a new root object into a component
    """
    if not isinstance(app, WSGIApp):
        if with_component:
            def wrap_in_component(factory):
                o = factory()
                if not isinstance(o, component.Component):
                    o = component.Component(o)
                return o
            app = lambda app=app: wrap_in_component(app)

        app = WSGIApp(app)

    return app
