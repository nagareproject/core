#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Comet-style channels i.e HTTP push channels

This implementation is only working with a multi-threaded publisher
"""

from __future__ import with_statement

import threading
import select

from nagare import presentation, ajax

class Client(object):
    """A connected client"""
    
    def __init__(self, fileno, response):
        """Initialization

        In:
          - ``fileno`` -- the I/O file handle
          - ``response`` -- ``webob`` response object
        """
        self._fileno = fileno
        self._response = response

        self._event = threading.Event()

    def block(self):
        self._event.wait()

    def release(self):
        self._event.set()

    def is_blocked(self):
        return self._event.is_set()

    def fileno(self):
        return self._fileno

    def send(self, msg=None, status=None):
        if status is not None:
            self._response.status = status

        if msg is not None:
            self._response.body = msg

        if not self.is_blocked():
            self.release()


class Channel(object):
    """A comet-style channel i.e XHR long polling channel"""

    def __init__(self, id, js, history_size=0, poll_time=1000):
        """Initialization

        In:
          - ``id`` -- the channel identifier
          - ``js`` -- the javascript function to call when a message is received
          - ``history_size`` -- number of messages kept on the server
          - ``poll_time`` -- time the brower waits, before to retry to reconnect, after an error occurs
        """
        self.id = id
        self.js = js
        self.poll_time = poll_time

        self.history_size = history_size
        self.history_nb = 0
        self.history = []

        self.lock = threading.Lock()
        self.clients = set()

    def connect(self, nb, fileno, response):
        """A browser wants to be connected to this channel

        In:
          - ``nb`` -- identifier of the next wanted message
          - ``fileno`` -- the I/O file handle
          - ``response`` -- ``webob`` response object
        """
        client = Client(fileno, response)

        with self.lock:
            self.discard_disconnected_clients()

            # Is a msg already available to send ?
            (new_nb, msg) = self.get_old_msg(nb)
            if not msg:
                self.clients.add(client)

        if msg:
            # Msg found into the history
            # Send it directly
            self._send(client, new_nb, msg)
        else:
            # No msg found
            # Wait for a new msg to be sent
            client.block()

    def discard_disconnected_clients(self):
        """Forgot about the disconnected clients
        """
        clients_to_discard = select.select(self.clients, [], [], 0)[0]

        for client in clients_to_discard:
            client.release()

        self.clients = self.clients - set(clients_to_discard)

    def send(self, msg):
        """Send a message to all the connected clients

        In:
          - ``msg`` -- message to send
        """
        with self.lock:
            # Keep the msg into the history
            self.history.append(msg)

            if len(self.history) > self.history_size:
                self.history.pop(0)
                self.history_nb += 1

            clients, self.clients = self.clients, set()

        # Send the msg to all the waiting clients
        for client in clients:
            self._send(client, self.history_nb+len(self.history), msg)

    def close(self):
        """Close a channel
        """
        with self.lock:
            clients, self.clients = self.clients, set()

        # Send a "Service Unavailable" status to all the connected clients
        for client in clients:
            client.send(status=503)   # "Service Unavailable"

    def _send(self, client, nb, msg):
        """Build the message to send

        In:
          - ``client`` -- client to send the message to
          - ``nb`` -- message id
          - ``msg`` -- the message
        """
        # The raw message sent contains the msg identifier and the data
        client.send('%09d%s' % (nb, msg.encode('utf-8')))

    def get_old_msg(self, nb):
        """Check if a message in the history is ready to be sent

        In:
          - ``nb`` -- identifier of the next message wanted by the client

        Return:
          - the tuple:
            - identifier of the next msg to ask for
            - the msg if available or ``None``
        """
        if nb >= self.history_nb+len(self.history):
            return (None, None)

        if nb < self.history_nb:
            nb = self.history_nb

        # Return only one message
        return (nb+1, self.history[nb-self.history_nb])

    def __len__(self):
        return len(self.clients)


class TextChannel(Channel):
    def get_old_msg(self, nb):
        """Check if a message in the history is ready to be sent

        In:
          - ``nb`` -- identifier of the next message wanted by the client

        Return:
          - the tuple:
            - identifier of the next msg to ask for
            - the msg if available or ``None``
        """
        # Concatenate all the available msgs
        msgs = self.history[max(nb, self.history_nb)-self.history_nb:]
        return (len(self.history)+self.history_nb, ''.join(msgs) if msgs else None)

# ----------------------------------------------------------------------------

@presentation.render_for(Channel)
def render(self, h, *args):
    ajax.javascript_dependencies(h)
    h.head.javascript_url('/static/nagare/comet.js')

    return h.script('setTimeout(function () { comet_getAndEval("%s", 0, %s, %d) }, 300)' % (self.id, self.js, self.poll_time))

# ----------------------------------------------------------------------------

class Channels(dict):
    """Channels manager
    """
    channel_factory = Channel

    def create(self, id, *args, **kw):
        """Create a new channel

        In:
          - ``id`` -- the channel identifier
        """
        if id not in self:
            self[id] = self.channel_factory(id, *args, **kw)

    def connect(self, id, nb, fileno, response):
        """A browser wants to be connected to a channel

        In:
          - ``id`` -- the channel identifier
          - ``nb`` -- identifier of the next message wanted
          - ``fileno`` -- the I/O file handle
          - ``response`` -- ``webob`` response object
        """
        channel = self.get(id)

        if channel is None:
            response.status = 404 # "Not Found"
        else:
            self.discard_disconnected_clients()

            channel.connect(nb, fileno, response)

    def discard_disconnected_clients(self):
        for channel in self.values():
            channel.discard_disconnected_clients()

    def send(self, id, msg):
        """Send a message to all the connected clients of a channel

        In:
          - ``id`` -- the channel identifier
          - ``msg`` -- message to send
        """
        self[id].send(msg)

    def has_clients(self, id):
        self.discard_disconnected_clients()
        return len(self[id])

    def __delitem__(self, id):
        """Close a channel

        In:
          - ``id`` -- the channel identifier
        """
        channel = self.pop(id)
        channel.close()


class TextChannels(Channels):
    channel_factory = TextChannel

channels = TextChannels()
