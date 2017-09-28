# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Helper to mark an object as stateless"""

import random


def stateless(o):
    """Mark an object as stateless

    In:
      - ``o`` -- the object

    Return:
      - ``o``
    """
    if not hasattr(o, '_persistent_id'):
        # A stateless object has a unique oid
        o._persistent_id = random.randint(0, 99999999)

    return o


def stateful(o):
    """Mark an object as stateful

    In:
      - ``o`` -- the object

    Return:
      - ``o``
    """
    if hasattr(o, '_persistent_id'):
        del o._persistent_id

    return o
