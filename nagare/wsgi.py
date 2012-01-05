#--
# Copyright (c) 2008-2012 Net-ng.
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

import sys
import os

import webob
from webob import exc, acceptparse

from nagare import component, presentation, serializer, database, top, security, log, comet, i18n, local
from nagare.security import dummy_manager
from nagare.callbacks import Callbacks, CallbackLookupError
from nagare.namespaces import xhtml

from nagare.sessions import ExpirationError

# ---------------------------------------------------------------------------

class Response(webob.Response):
    def __init__(self, accept):
        super(Response, self).__init__(headerlist=[])

        accept = acceptparse.Accept(accept)
        self.xml_output = accept.best_match(('text/html', 'application/xhtml+xml')) == 'application/xhtml+xml'

        self.content_type = ''
        self.doctype = None

# ---------------------------------------------------------------------------

class WSGIApp(object):
    renderer_factory = xhtml.Renderer   # Default renderer

    def __init__(self, root_factory):
        """Initialization

        In:
          - ``root_factory`` -- function to create the application root component
        """
        self.root_factory = root_factory

        self.static_path = ''
        self.static_url = ''
        self.data_path = ''
        self.databases = []
        self.name = ''
        self.project_name = ''
        self.redirect_after_post = False
        self.always_html = True
        self.sessions = None
        self.last_exception = None

        self.security = dummy_manager.Manager()

        self.set_default_locale(i18n.Locale())

    def set_config(self, config_filename, config, error):
        """Read the configuration parameters

        In:
          - ``config_filename`` -- the path to the configuration file
          - ``config`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        self.name = config['application']['name']
        self.redirect_after_post = config['application']['redirect_after_post']
        self.always_html = config['application']['always_html']

    def set_static_path(self, static_path):
        """Register the directory of the static contents

        In:
          - ``static_path`` -- the directory where the static contents of the application
            are located
        """
        self.static_path = static_path

    def set_static_url(self, static_url):
        """Register the url of the static contents

        In:
          - ``static_url`` -- the url of the static contents of the application
        """
        self.static_url = static_url

    def set_data_path(self, data_path):
        """Register the directory of the data

        In:
          - ``data_path`` -- the directory where the data of the application are located
        """
        self.data_path = data_path

    def set_publisher(self, publisher):
        """Register the publisher

        In:
          - ``publisher`` -- the publisher of the application
        """
        pass

    def set_sessions_manager(self, sessions_manager):
        """Register the sessions manager

        In:
          - ``sessions_manager`` -- the sessions manager
        """
        self.sessions = sessions_manager

    def set_databases(self, databases):
        """Register the databases properties

        In:
          - ``databases`` -- the SQLAlchemy metadata objects and the database engines settings
        """
        self.databases = databases

    def set_project(self, name):
        """The application distribution name

        In:
          - ``project_name`` -- name of the distutils distribution where the app is located
        """
        self.project_name = name

    def set_default_locale(self, locale):
        """Register the default locale

        In:
          - ``locale`` -- the default locale
        """
        self.default_locale = locale

    def set_locale(self, locale):
        """Set the locale of the request scope

        In:
          - ``locale`` -- the locale
        """
        if locale.dirname is None:
            locale.dirname = os.path.join(self.data_path, 'locale')

        i18n.set_locale(locale)

    def start(self):
        """Call after each process start
        """
        for database_settings in self.databases:
            database.set_metadata(*database_settings)

    # -----------------------------------------------------------------------

    def on_bad_http_method(self, request, response):
        """A HTTP request other than a GET or PUT was received

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - raise a ``webob.exc`` object, used to generate the response to the browser
        """
        raise exc.HTTPMethodNotAllowed()

    def on_incomplete_url(self, request, response):
        """An URL without an application name was received

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - raise a ``webob.exc`` object, used to generate the response to the browser
        """
        raise exc.HTTPMovedPermanently(add_slash=True)

    def on_session_expired(self, request, response):
        """The session id received is invalid

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - raise a ``webob.exc`` object, used to generate the response to the browser
        """
        raise exc.HTTPMovedPermanently()

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
        return output

    def on_callback_lookuperror(self, request, response, async):
        """A callback was not found

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``async`` -- is an XHR request ?
        """
        if not async:
            raise

        # As the XHR requests use the same continuation, a callback
        # can be not found (i.e deleted by a previous XHR)
        # In this case, do nothing
        return lambda h: ''

    def on_after_post(self, request, response, ids):
        """Generate a redirection after a POST

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``ids`` -- identifiers to put into the generated redirection URL

        Return:
          - a ``webob.exc`` object, used to generate the response to the browser
        """
        return exc.HTTPSeeOther(location=request.path_url + '?' + '&'.join(ids))

    def on_exception(self, request, response):
        """Method called when an exception occurs

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - a ``webob`` response object
        """
        raise

    # -----------------------------------------------------------------------

    def create_root(self, *args, **kw):
        """Create the application root component

        Return:
          - the root component
        """
        return self.root_factory(*args, **kw)

    def create_renderer(self, async, session, request, response, callbacks):
        """Create the initial renderer (the root of all the used renderers)

        In:
          - ``async`` -- is an XHR request ?
          - ``session`` -- the session
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``callbacks`` -- object to register the callbacks
        """
        renderer = self.renderer_factory(
                                            None,
                                            session,
                                            request, response,
                                            callbacks,
                                            self.static_url, self.static_path,
                                            request.script_name
                                        )

        if async:
            renderer = renderer.AsyncRenderer(
                                                None,
                                                session,
                                                request, response,
                                                callbacks,
                                                self.static_url, self.static_path,
                                                request.script_name,
                                                async_header = True
                                             )

        return renderer

    def start_request(self, root, request, response):
        """A new request is received, setup its dedicated environment

        In:
          - ``root`` -- the application root component
          - ``request`` -- the web request object
          - ``response`` -- the web response object
        """
        security.set_manager(self.security) # Set the security manager
        security.set_user(self.security.create_user(request, response)) # Create the User object

        self.set_locale(self.default_locale) # Set the default Locale

    # Processing phase
    def _phase1(self, request, response, callbacks):
        """Phase 1 of the request processing:

          - The callbacks are processed
          - The objects graph can be modified

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``callbacks`` -- the registered callbacks

        Return:
          - function to render the objects graph or ``None``
        """
        return callbacks.process_response(request, response)

    # Rendering phase
    def _phase2(self, output, content_type, doctype, is_xhr, response):
        """Final step of the phase 2

        Phase 2 of the request processing:

          - The object graph is rendered
          - No modification of the objects is allowed

        In:
          - ``output`` -- the rendered content
          - ``content_type`` -- the rendered content type
          - ``doctype`` -- the (optional) doctype
          - ``is_xhr`` -- is the request a XHR request ?

        Out:
          - ``response`` -- the response object
        """
        (response.content_type, response.body) = serializer.serialize(output, content_type, doctype, not is_xhr)
        response.charset = 'utf-8'

    def __call__(self, environ, start_response):
        """WSGI interface

        In:
          - ``environ`` -- dictionary of the received elements
          - ``start_response`` -- callback to send the headers to the browser

        Return:
          - the content to send back to the browser
        """
        local.request.clear()

        # Create the ``WebOb`` request and response objects
        # -------------------------------------------------

        request = webob.Request(environ, charset='utf-8')
        response = Response('text/html' if self.always_html else str(request.accept))

        channel_id = request.params.get('_channel')
        nb = request.params.get('_nb')
        if channel_id and nb:
            if environ['wsgi.multiprocess']:
                response.status = 501 # "Not Implemented"
            else:
                comet.channels.connect(channel_id, int(nb), environ['wsgi.input'].file.fileno(), response)

            return response(environ, start_response)

        xhr_request = request.is_xhr or ('_a' in request.params)

        session = None
        self.last_exception = None

        log.set_logger('nagare.application.'+self.name) # Set the dedicated application logger
        
        # Create a database transaction for each request
        with database.session.begin():
            try:
                # Phase 1
                # -------

                # Test the request validity
                if not request.path_info:
                    self.on_incomplete_url(request, response)

                try:
                    session = self.sessions.get(request, response, xhr_request)
                except ExpirationError:
                    self.on_session_expired(request, response)

                if session.is_new:
                    # A new session is created
                    root = self.create_root()   # Create a new application root component
                    callbacks = Callbacks()     # Create a new callbacks registry
                else:
                    # An existing session is used, retrieve the application root component
                    # and the callbacks registry
                    (root, callbacks) = session.data

                request.method = request.params.get('_method', request.method)
                if not session.is_new and request.method not in ('GET', 'POST'):
                    self.on_bad_http_method(request, response)

                self.start_request(root, request, response)

                url = request.path_info.strip('/')
                if session.is_new and url:
                    # If a URL is given, initialize the objects graph with it
                    presentation.init(root, tuple([u.decode('utf-8') for u in url.split('/')]), None, request.method, request)

                try:
                    render = self._phase1(request, response, callbacks)
                except CallbackLookupError:
                    render = self.on_callback_lookuperror(request, response, xhr_request)
            except exc.HTTPException, response:
                # When a ``webob.exc`` object is raised during phase 1, skip the
                # phase 2 and use it as the response object
                pass
            except Exception:
                self.last_exception = (request,  sys.exc_info())
                response = self.on_exception(request, response)
            else:
                # Phase 2
                # -------

                # If the ``redirect_after_post`` parameter of the ``[application]``
                # section is `True`` (the default), conform to the PRG__ pattern
                #
                # __ http://en.wikipedia.org/wiki/Post/Redirect/GetPRG

                try:
                    if (request.method == 'POST') and not xhr_request and self.redirect_after_post:
                        use_same_state = True
                        response = self.on_after_post(request, response, session.sessionid_in_url(request, response))
                    else:
                        use_same_state = xhr_request

                        # Create a new renderer
                        renderer = self.create_renderer(xhr_request, session, request, response, callbacks)
                        # If the phase 1 has returned a render function, use it
                        # else, start the rendering by the application root component
                        output = render(renderer) if render else root.render(renderer)

                        if session.back_used:
                            output = self.on_back(request, response, renderer, output)

                        if not xhr_request:
                            output = top.wrap(renderer.content_type, renderer, output)

                        self._phase2(output, renderer.content_type, renderer.doctype, render is not None, response)

                        if not xhr_request:
                            # TODO: move it into a ``renderer.end_rendering()`` method
                            callbacks.clear_not_used(renderer._rendered)

                    # Store the session
                    session.set(use_same_state, (root, callbacks))

                    security.get_manager().end_rendering(request, response, session)
                except exc.HTTPException, response:
                    # When a ``webob.exc`` object is raised during phase 2, stop immediately
                    # use it as the response object
                    pass
                except Exception:
                    self.last_exception = (request,  sys.exc_info())
                    response = self.on_exception(request, response)
            finally:
                if session:
                    session.release()

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
