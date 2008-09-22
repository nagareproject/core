#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Empty security manager"""
 
from nagare.security import common

class Manager(common.Authentification, common.Rules):
    """A security manager is typically a mix-in of an authentification
    manager and security rules
    """
    pass
