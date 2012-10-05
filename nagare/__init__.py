#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import sys

if sys.version_info < (2, 5, 2):
    print 'The version of Stackless Python must be 2.5.2 or more'
    sys.exit(-2)

# -----------------------------------------------------------------------------

import pkg_resources

pkg_resources.declare_namespace(__name__)

# -----------------------------------------------------------------------------

import mimetypes

# Fix issue 5868 in Python 2.6.2 (http://bugs.python.org/issue5868)
mimetypes.init()
