# --
# Copyright (c) 2014-2026 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --
import pickle

from nagare import continuation


def f(a):
    b = 100

    return b * continuation.Continuation().suspend() + a


def g(a):
    return f(a) + 10


def h():
    a = 1
    return g(10) + a


def test_multishots():
    """Continuation - multi-shots."""
    cont = continuation.delimit(h)
    assert isinstance(cont, continuation.Continuation)

    assert cont.resume(3) == 321
    assert cont.resume(4) == 421
    assert cont.resume(3) == 321


def test_pickle():
    """Continuation - serialization."""
    cont = continuation.delimit(h)
    assert isinstance(cont, continuation.Continuation)

    assert pickle.loads(pickle.dumps(cont)).resume(3) == 321
    assert pickle.loads(pickle.dumps(cont)).resume(4) == 421
    assert pickle.loads(pickle.dumps(cont)).resume(3) == 321
