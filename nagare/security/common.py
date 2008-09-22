#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from peak.rules import when
import webob

# ---------------------------------------------------------------------------

# The application can used anything for the permission objects
# So the following pre-defined permissions are optional helpers

class Permission(object):
    """Base class of all the permissions
    """
    pass

class Private(Permission):
    """To define the ``private`` permission singleton
    
    Nobody has access to objects protected with this permission
    """
    pass

class Public(Permission):
    """To define the ``public`` permission singleton
    
    Every body has access to objects protected with this permission
    """
    pass

# The singleton permissions
private = Private()
public = Public()

# ---------------------------------------------------------------------------

class Denial(Exception):
    """Type of the objects return when an access is denied
    
    In a boolean context, it is evaluated to ``False``
    """
    def __init__(self, message='Access forbidden'):
        """Initialisation
        
        In:
          - ``message`` -- denial description
        """
        self.message = message

    def __nonzero__(self):
        """Evaluated to ``False`` in a boolean context
        """
        return False

    def __str__(self):
        return str(self.message)

    def __unicode__(self):
        return unicode(self.message)

    def __repr__(self):
        return 'security.Denial(%r)' % self.message

# --------------------------------------------------------------

class User(object):
    """Base class for the users object
    
    .. note::    
        An application can used anything for the users object but it's easier to
        inherit from this base class because some pre-defined generic methods
        already use it.
    """
    pass

# ---------------------------------------------------------------------------

class Rules(object):
    """Pre-defined security rules
    
    A rule is an implementation of the ``security.common.Rules.has_permission()``
    generic method.
    """
    def has_permission(self, user, perm, subject):
        """The ``has_permission()`` generic method
        and default implementation: by default all accesses are denied
        
        In:
          - ``user`` -- user to check the permission for
          - ``perm`` -- permission(s) to check
          - ``subject`` -- object to check the permission on
          
        Return:
          - True if the access is granted
          - Else a ``security.common.denial`` object
        """
        return Denial('Access denied')

    @when(has_permission, (object, Private))
    def no_access(self, user, perm, subject):
        """Nobody has access to an object protected with the ``private`` permission
        """
        return Denial()

    @when(has_permission, (object, Public))
    def full_access(self, user, perm, subject):
        """Everybody has access to an object protected with the ``public`` permission
        """
        return True
    
    @when(has_permission, (User, tuple))
    def check_access(self, user, perms, subject):
        """If several permissions are to be checked, the access must be granted
        for at least one permission
        """
        return any((self.has_permission(user, perm, subject) for perm in perms)) or Denial('Access forbidden')

    @when(has_permission, (User, list))
    def check_access(self, user, perms, subject):
        """If several permissions are to be checked, the access must be granted
        for at least one permission
        """
        return self.has_permission(user, tuple(perms), subject)

    @when(has_permission, (User, set))
    def check_access(self, user, perms, subject):
        """If several permissions are to be checked, the access must be granted
        for at least one permission
        """
        return self.has_permission(user, tuple(perms), subject)

# ---------------------------------------------------------------------------

class Authentification(object):
    """An ``Authentification`` object identify, authentify and create the
    user objects
    
    .. note::
        By definition, the user object ``None`` is the anonymous user
    """
    def create_user(self, request, response):
        """Check the user is valid and create it
        """
        # Retrieve the data associated with the connected user
        (username, ids) = self.get_ids(request, response)

        # Retrieve the authentification data
        password = self.get_password(username)
        if not self.check_password(username, password, **ids):
            # Bad authentification of the user, create an anonymous user
            username = None
        
        # Create the user object
        return self._create_user(username)

    def check_password(self, username, password, **kw):
        """Authentification
        
        In:
          - ``username`` -- the user id
          - ``password`` -- the real password of the user
          - ``kw`` -- other data for the user
          
        Return:
          - a boolean
        """
        return (username is None) and (password is None)

    # -----------------------------------------------------------------------

    def get_ids(self, request, response):
        """Return the data associated with the connected user
        
        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          
        Return:
          - A tuple with the id of the user and a dictionary of its data
        """
        return (None, {})

    def logout(self):
        """Deconnection of the current user
        """
        return None

    def denies(self, detail):
        """Method called when a permission is denied

        In:
          - ``detail`` -- a ``security.common.denial`` object
        """
        raise webob.exc.HTTPForbidden(str(detail))
    
    def get_password(self, username):
        """Return the real password of the user
        
        In:
          - ``username`` -- the user id
          
        Return:
          - the password
        """
        return None
    
    def _create_user(self, username):
        """The user is validated, create the user object
        
        In:
          - ``username`` -- the user id
          
        Return:
          - the user object
        """
        return None
