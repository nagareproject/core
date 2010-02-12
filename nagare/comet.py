#--
# Copyright (c) 2008, 2009, 2010 Net-ng.
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

from nagare import presentation, ajax

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
        self.clients = []

    def connect(self, nb, response):
        """A browser wants to be connected to this channel

        In:
          - ``nb`` -- identifier of the next wanted message
          - ``response`` -- ``webob`` response object
        """
        with self.lock:
            # Is a msg already available to send ?
            (new_nb, msg) = self.get_old_msg(nb)
            if not msg:
                event = threading.Event()
                self.clients.append((event, response))

        if msg:
            # Msg found into the history
            # Send it directly
            self._send(new_nb, msg, response)
        else:
            # No msg found
            # Wait for a new msg to be sent
            event.wait()

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

            clients, self.clients = self.clients, []

        # Send the msg to all the waiting clients
        for (event, response) in clients:
            self._send(self.history_nb+len(self.history), msg, response)
            event.set()

    def close(self):
        """Close a channel
        """
        with self.lock:
            clients, self.clients = self.clients, []

        # Send a "Service Unavailable" status to all the connected clients
        for (event, response) in clients:
            response.status = 503   # "Service Unavailable"
            event.set()

    def _send(self, nb, msg, response):
        """Build the message to send
        """
        # The raw message sent contains the msg identifier and the data
        response.body = '%09d%s' % (nb, msg.encode('utf-8'))

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

    def connect(self, multiprocess, id, nb, response):
        """A browser wants to be connected to a channel

        In:
          - ``multiprocess`` -- are we running in a multi-processes environment ?
          - ``id`` -- the channel identifier
          - ``nb`` -- identifier of the next message wanted
          - ``response`` -- ``webob`` response object
        """
        if multiprocess:
            response.status = 501 # "Not Implemented"
        else:
            channel = self.get(id)

            if channel is None:
                response.status = 404 # "Not Found"
            else:
                channel.connect(nb, response)

    def send(self, id, msg):
        """Send a message to all the connected clients of a channel

        In:
          - ``id`` -- the channel identifier
          - ``msg`` -- message to send
        """
        self[id].send(msg)

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

# ----------------------------------------------------------------------------

if __name__ == '__main__':
    class Response: pass
    response = Response()
    response.body = None

    channel = TextChannel('42', 'f')

    channel.send('aaa')
    channel.send('bbb')
    channel.send('ccc')

    channel.connect(response, 0)
    print response.body

    response.body = None
    channel.send('ddd')
    print response.body

    channel.send('eee')
    response.body = None
    channel.connect(response, 4)
    print response.body

    channel.send('eee')
    print response.body

    # -----------------

    channel = TextChannel('42', 'f', 3)

    channel.send('aaa')
    channel.send('bbb')
    channel.send('ccc')

    channel.connect(response, 0)
    print response.body

    channel.connect(response, 1)
    print response.body

    channel.connect(response, 2)
    print response.body

    response.body = None
    channel.connect(response, 3)
    print response.body

    response.body = None
    channel.connect(response, 4)
    print response.body

    channel = TextChannel('42', 'f', 3)

    channel.send('aaa')
    channel.send('bbb')
    channel.send('ccc')
    channel.send('ddd')
    channel.send('eee')

    channel.connect(response, 0)
    print response.body

    channel.connect(response, 4)
    print response.body

    response.body = None
    channel.connect(response, 5)
    print response.body

    channel = TextChannel('42', 'f')

    channel.send('aaa')
    channel.send('bbb')
    channel.send('ccc')

    channel.connect(response, 0)
    print response.body

    response.body = None
    channel.send('ddd')
    print response.body

    channel.send('eee')
    response.body = None
    channel.connect(response, 4)
    print response.body

    channel.send('eee')
    print response.body

    # -----------------

    channel = Channel('42', 'f', 3)

    channel.send('aaa')
    channel.send('bbb')
    channel.send('ccc')

    channel.connect(response, 0)
    print response.body

    channel.connect(response, 1)
    print response.body

    channel.connect(response, 2)
    print response.body

    response.body = None
    channel.connect(response, 3)
    print response.body

    response.body = None
    channel.connect(response, 4)
    print response.body

    channel = Channel('42', 'f', 3)

    channel.send('aaa')
    channel.send('bbb')
    channel.send('ccc')
    channel.send('ddd')
    channel.send('eee')

    channel.connect(response, 0)
    print response.body

    channel.connect(response, 4)
    print response.body

    response.body = None
    channel.connect(response, 5)
    print response.body
