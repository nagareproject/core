#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Applications administration view
"""

from __future__ import with_statement
import operator

from nagare import presentation

class Admin(object):
    priority = 100        # Order of the default view, into the administrative interface

    def __init__(self, apps):
        """Initialization

        In:
          - ``apps`` -- list of tuples (application, application name, application urls)
        """
        self.apps = sorted([(app_name, names) for (_, app_name, names) in apps])

@presentation.render_for(Admin)
def render(self, h, *args):
    """Display the currently launched application, with their names and their URLs
    """
    with h.div:
        h << h.h2('Active applications')

        with h.ul:
            for (app_name, names) in self.apps:
                with h.li("Application '%s' registered as " % app_name):
                   for (i, name) in enumerate(sorted(names)):
                       if i:
                           h << ' and '
                       h << h.a('/'+name, href='/'+name+('/' if name else ''))

    return h.root
