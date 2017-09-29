# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import cStringIO
import cPickle

from nagare.continuation import Tasklet
from nagare.component import Component


def persistent_id(o, clean_callbacks, callbacks, session_data, tasklets):
    """An object with a ``_persistent_id`` attribute is stored into the session
    not into the state snapshot

    In:
      - ``o`` -- object to check
      - ``clean_callbacks`` -- do we have to forget the old callbacks?

    Out:
      - ``callbacks`` -- merge of the callbacks from all the components
      - ``session_data`` -- dict persistent_id -> object of the objects to store into the session
      - ``tasklets`` -- set of the serialized tasklets

    Return:
      - the persistent id or ``None``
    """
    r = None

    id_ = getattr(o, '_persistent_id', None)
    if id_ is not None:
        session_data[id_] = o
        r = str(id_)

    elif type(o) is Tasklet:
        tasklets.add(o)

    elif isinstance(o, Component):
        callbacks.update(o.serialize_callbacks(clean_callbacks))

    return r


def set_persistent_id(pickler, persistent_id):
    if 'inst_persistent_id' in dir(pickler):
        pickler.inst_persistent_id = persistent_id
    else:
        pickler.persistent_id = persistent_id


class DummyFile(object):
    """A write-only file that does nothing"""
    def write(self, data):
        pass


class Dummy(object):
    def __init__(self, pickler=None, unpickler=None):
        """Initialization

          - ``pickler`` -- pickler to use
          - ``unpickler`` -- unpickler to use
        """
        self.pickler = pickler or cPickle.Pickler
        self.unpickler = unpickler or cPickle.Unpickler

    def _dumps(self, pickler, data, clean_callbacks):
        """Serialize an objects graph

        In:
          - ``pickler`` -- pickler to use
          - ``data`` -- the objects graph
          - ``clean_callbacks`` -- do we have to forget the old callbacks?

        Out:
          - data to keep into the session
          - data to keep into the state
        """
        session_data = {}
        tasklets = set()
        callbacks = {}

        # Serialize the objects graph and extract all the callbacks
        set_persistent_id(pickler, lambda o: persistent_id(o, clean_callbacks, callbacks, session_data, tasklets))
        pickler.dump(data)

        return session_data, callbacks, tasklets

    def dumps(self, data, clean_callbacks):
        """Serialize an objects graph

        In:
          - ``data`` -- the objects graph
          - ``clean_callbacks`` -- do we have to forget the old callbacks?

        Out:
          - data kept into the session
          - data kept into the state
        """
        pickler = self.pickler(DummyFile(), protocol=-1)
        session_data, callbacks, tasklets = self._dumps(pickler, data, clean_callbacks)

        # This dummy serializer returns the data untouched
        return None, (data, callbacks)

    def loads(self, session_data, state_data):
        """Deserialize an objects graph

        In:
          - ``session_data`` -- data from the session
          - ``state_data`` -- data from the state

        Out:
          - the objects graph
          - the callbacks
        """
        return state_data


class Pickle(Dummy):
    def dumps(self, data, clean_callbacks):
        """Serialize an objects graph

        In:
          - ``data`` -- the objects graph
          - ``clean_callbacks`` -- do we have to forget the old callbacks?

        Out:
          - data kept into the session
          - data kept into the state
        """
        f = cStringIO.StringIO()
        pickler = self.pickler(f, protocol=-1)
        # Pickle the data
        session_data, callbacks, tasklets = self._dumps(pickler, data, clean_callbacks)

        # Pickle the callbacks
        set_persistent_id(pickler, lambda o: None)
        pickler.dump(callbacks)

        # Kill all the blocked tasklets, which are now serialized
        for t in tasklets:
            t.kill()

        # The pickled data are returned
        return session_data, f.getvalue()

    def loads(self, session_data, state_data):
        """Deserialize an objects graph

        In:
          - ``session_data`` -- data from the session
          - ``state_data`` -- data from the state

        Out:
          - the objects graph
          - the callbacks
        """
        p = self.unpickler(cStringIO.StringIO(state_data))
        if session_data:
            p.persistent_load = lambda i: session_data.get(int(i))

        return p.load(), p.load()
