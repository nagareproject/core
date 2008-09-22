#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Applications administration view
"""

import operator

from nagare import presentation

class Admin(object):
    priority = 100        # Order of the default view, into the administrative interface
    
    def __init__(self, apps):
        """Initialization
        
        In;
          - ``apps`` -- a dictionary where the keys are the application objects
            and the keys a tuple (application name, application url)
        """
        self.apps = sorted(apps.values(), key=operator.itemgetter(1))


@presentation.render_for(Admin)
def render(self, h, *args):
    """Display the currently launched application, with their names and their URLs
    """
    return h.div(
        h.h2('Active applications'),
        h.ul([h.li("Application '%s' registered as " % app_name,
                   h.a('/'+name, href='/'+name+ ('/' if name else ''))) for (app_name, name) in self.apps])
    )
