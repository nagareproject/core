#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``info`` administrative command

Display informations about the framework environment
"""

import sys, pkg_resources

from nagare.admin import util

class Info(util.Command):
    """Display informations about the framework environment"""

    desc = 'Display various informations'

    @staticmethod
    def run(parser, options, args):
        """Display the informations

        In:
          - ``parser`` -- the optparse.OptParser object used to parse the configuration file
          - ``options`` -- options in the command lines
          - ``args`` -- arguments in the command lines
        """
        # For the moment, just diplay the Python version
        print sys.version
        print
        print 'Nagare version', pkg_resources.get_distribution('nagare').version

