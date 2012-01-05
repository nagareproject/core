#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import local, wsgi
from nagare.sessions import ExpirationError, common

local.request = local.Process()

def create_environ():
    return {
            'REQUEST_METHOD' : 'GET',
            'SCRIPT_NAME' : '/app',
            'PATH_INFO' : '/',
            'QUERY_STRING' : '_s=10&_c=42',
            'SERVER_PROTOCOL' : 'HTTP/1.0',
            'SERVER_NAME' : 'localhost',
            'SERVER_PORT' : 8080,
            'wsgi.url_scheme' : 'http'
            }

class Response(dict):
    def __init__(self):
        self.status_code = None
        self.status = None

    def __call__(self, status, headers):
        (self.status_code, self.status) = status.split(' ', 1)
        self.status_code = int(self.status_code)

        self.update(dict(headers))
        assert len(self) == len(headers)

    def __repr__(self):
        return '%d %s - %s' % (self.status_code, self.status, super(Response, self).__repr__())

class Session(object):
    def is_new(self):
        return True

class SessionManager(common.Sessions):
    def get(self, request, response):
        assert self._get_ids(request) == ('10', '42')

class ExpiredSessionManager(common.Sessions):
    def get(self, request, response, use_same_state):
        assert self._get_ids(request) == ('10', '42')
        raise ExpirationError()

class App(wsgi.WSGIApp):
    def __init__(self, session_manager=SessionManager(local.DummyLock)):
        super(App, self).__init__(lambda: None)
        self.sessions = session_manager

def process_request(app=None, environ={}, **kw):
    if app is None:
        app = App()

    env = create_environ()
    env.update(environ)
    env.update(kw)

    r = Response()
    app(env, r)
    return r

def test_request_validity2():
    """Request - invalid url"""
    r = process_request(PATH_INFO='')
    print r.keys()
    assert (r.status_code == 301) and r['Location'] == 'http://localhost:8080/app/?_s=10&_c=42'

def test_bad_session():
    """Request - session expired"""
    r = process_request(App(session_manager=ExpiredSessionManager(local.DummyLock)))
    assert (r.status_code == 301) and r['Location'] == 'http://localhost:8080/app/'
