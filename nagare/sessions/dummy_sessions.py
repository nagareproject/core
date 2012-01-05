#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Dummy sessions manager

A new session is always created
"""

class State(object):
    is_new = True
    back_used = False
    release = sessionid_in_url = sessionid_in_form = set = delete = lambda *args, **kw: ()

class Sessions(object):
    def set_config(self, filename, conf, error):
        pass

    def get(self, request, response, use_same_state):
        return State()
