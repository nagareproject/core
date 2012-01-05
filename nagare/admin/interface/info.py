#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Framework environment administrative view
"""

import sys, time, pkg_resources

from nagare import component, presentation

class Admin(object):
    priority = 1        # Order of the default view, into the administrative interface

    def __init__(self, apps):
        """Initialisation

        In:
          - ``apps`` -- list of tuples (application, application name, application urls)
        """
        pass

@presentation.render_for(Admin)
def render(self, h, *args):
    """Display informations about the running framework environment"""
    return h.div(
        h.h2('Informations'),

        h.p('Nagare - version %s - %s -' % (pkg_resources.get_distribution('nagare').version, time.strftime('%c'))),
        # h.p('Installed options: ', ', '.join(pkg_resources.get_distribution('fw-ng').extras)),

        h.p('Python: ', sys.version.split('\n')[0])
    )
