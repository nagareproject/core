#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Empty security manager"""

from nagare.security import common

class Manager(common.Authentication, common.Rules):
    """A security manager is typically a mix-in of an authentication
    manager and security rules
    """
    pass
