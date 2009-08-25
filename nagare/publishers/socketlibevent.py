from socket import *
from socket import _GLOBAL_DEFAULT_TIMEOUT, create_connection

# -----------------------------------------------------------------------------

import sys
from socket import _fileobject
from socket import socket as stdsocket

import stackless
import event

class socket(object):
    def __init__(self, family=AF_INET, type=SOCK_STREAM, proto=0, _sock=None):
        self.sock = _sock if _sock else stdsocket(family, type, proto)
        self.fileobject = None

        self.read_channel = stackless.channel()
        self.write_channel = stackless.channel()
        self.accept_channel = None

    def __getattr__(self, attr):
        return getattr(self.sock, attr)

    def accept(self):
        if not self.accept_channel:
            self.accept_channel = stackless.channel()
            event.event(self.handle_accept, handle=self.sock, evtype=event.EV_READ | event.EV_PERSIST).add()

        return self.accept_channel.receive()

    def handle_accept(self, ev, sock, *args):
        (s, a) = sock.accept()
        s = socket(_sock=s)

        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        
        self.accept_channel.send((s, a))

    def connect(self, address):
        for i in range(10): # try to connect 10 times!
            if self.sock.connect_ex(address) == 0:
                break
        
            stackless.schedule()
        else:
            # One last try, just to raise an error
            return self.sock.connect(address)

    def send(self, *args):
        event.write(self.sock, self.handle_send, *args)
        return self.write_channel.receive()

    def handle_send(self, *args):
        self.write_channel.send(self.sock.send(*args))

    def sendall(self, data, *args):
        while data:
            sent = self.send(data, *args)
            data = data[sent + 1:]

    def recv(self, *args):
        event.read(self.sock, self.handle_recv, *args)
        return self.read_channel.receive()
    
    def handle_recv(self, *args):
        self.read_channel.send(self.sock.recv(*args))
    
    def recvfrom(self, *args):
        event.read(self.sock, self.handle_recv, *args)
        return self.read_channel.receive()

    def handle_recvfrom(self, *args):
        self.read_channel.send(self.sock.recvfrom(*args))

    def makefile(self, mode='r', bufsize=-1):
        self.fileobject = _fileobject(self, mode, bufsize)
        return self.fileobject

    def _close(self):
        while self.fileobject and (self.fileobject._sock == self):
            print "Waiting close"
            stackless.schedule()
    
        self.sock.close()

    def close(self):
        # Don't close while the fileobject is still using the fakesocket
        # XXX Temporary fix
        if self.accept_channel and (self.accept_channel.balance < 0):
            self.accept_channel.send(None)
        stackless.tasklet(self._close)()


class EventServer(object):
    def __init__(self, server_address, listen_backlog=SOMAXCONN):
        self.server_address = server_address
        
        self.running = False
        event.signal(2, self.die)

        self.sock = socket()
        self.sock.bind(self.server_address)
        self.sock.listen(listen_backlog)

    def die(self):
        self.sock.close()
        self.running = False
    
    def event_loop(self):
        self.running = True

        while self.running:
            event.loop(False)
            stackless.schedule()

    def start_event_loop(self):
        stackless.tasklet(self.event_loop)()

    def handle_request(self, conn, src):
        pass

    def run(self):
        self.start_event_loop()

        while True:
            conn = self.sock.accept()
            if conn is None:
                break
            stackless.tasklet(self.handle_request)(*conn).run()

# -----------------------------------------------------------------------------

from paste import httpserver

class WSGIHandler(httpserver.WSGIHandler):
    def wsgi_setup(self, environ):
        httpserver.WSGIHandler.wsgi_setup(self, { 'wsgi.multithread' : False })      


class WSGIServer(EventServer):
    def __init__(self, wsgi_application, server_address):
        super(WSGIServer, self).__init__(server_address)        
        self.wsgi_application = wsgi_application

    def handle_request(self, conn, src):
        WSGIHandler(conn, src, self)
        conn.close()

# -----------------------------------------------------------------------------

import logging
from flup.server.scgi_base import BaseSCGIServer, NoDefault, Connection

class SCGIServer(BaseSCGIServer):
    def __init__(self, application, scriptName=NoDefault, environ=None,
                 bindAddress=('localhost', 4000), umask=None,
                 allowedServers=None,
                 loggingLevel=logging.INFO, debug=True, **kw):
        super(SCGIServer, self).__init__(application,
                                scriptName=scriptName,
                                environ=environ,
                                bindAddress=bindAddress,
                                umask=umask,
                                allowedServers=allowedServers,
                                loggingLevel=loggingLevel,
                                debug=debug)

    def run(self):
        #self.logger.info('%s starting up', self.__class__.__name__)

        try:
            sock = self._setupSocket()
        except error, e:
            self.logger.error('Failed to bind socket (%s), exiting', e[1])
            return False

        while True:
            (conn, src) = sock.accept()
            #print 'Connection from', src
            stackless.tasklet(self.handle_request)(conn)

        self._cleanupSocket(sock)

        #self.logger.info('%s shutting down%s', self.__class__.__name__, self._hupReceived and ' (reload requested)' or '')
        return True
    
    def handle_request(self, conn):
        Connection(conn, self._bindAddress, self).run()

# -----------------------------------------------------------------------------

import socket as socketmod

#socketmod._realsocket = socketmod.socket = socketmod.SocketType = socketmod._socketobject = socket
sys.modules['socket'] = sys.modules[__name__]

# -----------------------------------------------------------------------------

def test1():
    import urllib
    
    def test(i):
        print 'url read', i
        print urllib.urlopen('http://www.google.com').read(12)
    
    for i in range(5):
        stackless.tasklet(test)(i)
        
    stackless.run()


class EchoServer(EventServer):
    def handle_request(self, conn, src):
        print 'Connection from', src

        while True:
            data = conn.recv(1024)
            if not data.strip():
                break
            
            conn.send(data)
            
        conn.close()

def test2():
    HOST = '0.0.0.0'
    PORT = 10000
    
    EchoServer((HOST, PORT)).run()


def app(environ, start_response):
    """Simplest possible application object"""
    html = '<html><body><h1>Hello world !</h1></body></html>'
    start_response('200 OK', [('Content-Type', 'text/html'), ('Content-Length', str(len(html)))])

    return [html]

def test3():
    HOST = '0.0.0.0'
    PORT = 8080

    WSGIServer(app, (HOST, PORT)).run(SOMAXCONN)
    

if __name__ == '__main__':
    #test1()
    #test2()
    test3()
