#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Generic methods to associate views and URLs to objects"""

import types

from peak.rules import when
from webob.exc import HTTPNotFound


class ModelError(LookupError):
    pass

def render(self, renderer, comp, model):
    """Generic method to associate views to an object

    The views are implementation functions of this generic method

    This default implementation raises an exception

    In:
      - ``self`` -- the object
      - ``renderer`` -- the renderer
      - ``comp`` -- the component
      - ``model`` -- the name of the view
    """
    if model is not None:
        raise ModelError('No model "%s" for %r' % (model, self))
    else:
        raise ModelError('No default model for %r' % self)

def render_for(cls, model=None):
    """Decorator helper to register a view for a class of objects

    In:
      - ``cls`` -- the class
      - ``model`` -- the name of the view

    Return:
      - a closure
    """
    if model is not None:
        cond = 'isinstance(self, %s) and (model=="%s")' % (cls.__name__, model)
    else:
        # No name give, dispatch only on the arguments type
        cond = (cls, object, object, types.NoneType)

    return when(render, cond)

@when(render, (object, object, object, int))
def render(self, renderer, comp, model):
    return render(self, renderer, comp, None)

# ---------------------------------------------------------------------------

def init(self, url, comp, http_method, request):
    """Generic method to initialized an object from a URL

    In:
      - ``self`` -- the object
      - ``url`` -- the URL
      - ``comp`` -- the component
      - ``http_method`` -- the HTTP method
      - ``request`` -- the web request object
    """
    raise HTTPNotFound()

def init_for(cls, cond=None):
    """Decorator helper to register an URL for a class of objects

    In:
      - ``cls`` -- the class
      - ``cond`` -- a generic condition

    Return:
      - a closure
    """
    if cond is not None:
        cond = "isinstance(self, %s) and (%s)" % (cls.__name__, cond)
    else:
        # No condition given, dispatch on the class
        cond = (cls,)

    return when(init, cond)
