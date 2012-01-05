#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

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
