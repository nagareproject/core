# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --


class ExpirationError(LookupError):
    """Raised when a session or a state id is no longer valid
    """
    pass


class SessionSecurityError(LookupError):
    """Raised when the secure id of a session is not valid
    """
    pass
