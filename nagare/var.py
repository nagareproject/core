#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Variables with a functional interface:

  - ``v()`` -- return the value of ``v``
  - ``v(x)`` -- set the value of ``v`` to ``x``

For example:

  ``v = v + 1`` becomes ``v(v()+1)``
  
Handy into the lambda expressions
"""

_marker = object()

class Var(object):
    """Functional variables
    """
    def __init__(self, v=None):
        """Initialisation
        
        In:
          - ``v`` -- initial value
        """
        self.value = v

    def __call__(self, v=_marker):
        """Return or set the value
        
        In:
          - ``v` -- if given, ``v`` becomes the new value
          
        Return:
          - the variable value
        """
        if id(v) != id(_marker):
            self.value = v
        
        return self.value
    
    def render(self, renderer):
        """Directly put into a tree, render its value
        
        In:
          - ``renderer`` -- the current renderer
          
        Return:
          - the variable value
        """
        return self.value
    
    def __str__(self):
        return str(self.value)
