# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import sys

import pkg_resources


if sys.version_info < (2, 7, 0):
    print 'The Python version must be 2.7'
    sys.exit(-2)

# -----------------------------------------------------------------------------

pkg_resources.declare_namespace(__name__)
