#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import sys

import pkg_resources

try:
    import stackless
except ImportError:
    print 'You must use Python Stackless !'
    print 'Get it at http://www.stackless.com'
    sys.exit(-1)

if sys.version_info < (2, 5, 2):
    print 'The version of Stackless Python must be 2.5.2 or more'
    sys.exit(-2)

pkg_resources.declare_namespace('nagare')
