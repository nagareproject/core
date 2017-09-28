# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import sys
import mimetypes

import pkg_resources


if sys.version_info < (2, 5, 2):
    print 'The version of Python must be 2.5.2 or more'
    sys.exit(-2)

# -----------------------------------------------------------------------------

pkg_resources.declare_namespace(__name__)

# -----------------------------------------------------------------------------

# Fix issue 5868 in Python 2.6.2 (http://bugs.python.org/issue5868)
mimetypes.init()
