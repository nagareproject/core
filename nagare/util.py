#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Various pre-defined components"""

from nagare import component, presentation, var

class Ask(object):
    """Ask the user to enter a line of text

    The text entered is answered
    """
    def __init__(self, msg):
        """Initialization

        In:
          - ``msg`` -- message to display
        """
        self.msg = msg

@presentation.render_for(Ask)
def render(self, h, comp, *args):
    """The view is a simple form with a text input control

    In:
      - ``h`` -- the renderer
      - ``comp`` -- the component
      - ``model`` -- the name of the view

    Return:
      - a tree
    """
    r = var.Var()

    return h.form(
                  self.msg, ' ',
                  h.input.action(r),
                  h.input(type='submit', value='Send').action(lambda: comp.answer(r()))
                 )

class Confirm(object):
    """Display a confirmation message
    """

    def __init__(self, msg):
        """Initialization

        In:
          - ``msg`` -- message to display
        """
        self.msg = msg

@presentation.render_for(Confirm)
def render(self, h, comp, *args):
    """The view is a simple form with the text and a submit button

    In:
      - ``h`` -- the renderer
      - ``comp`` -- the component
      - ``model`` -- the name of the view

    Return:
      - a tree
    """
    return h.form(
                  self.msg, h.br,
                  h.input(type='submit', value='ok').action(comp.answer)
                 )


class View(object):
    """A differed view

    Can be useful to add a view for a ``component.Task``
    """
    def __init__(self, view):
        """Initialization

        In:
          - ``view`` -- a function that will be called to render this object
        """
        self.view = view

@presentation.render_for(View)
def render(self, h, *args):
    """To render this object, call the differed view function

    In:
      - ``h`` -- the renderer

    Return:
      - a tree
    """
    return self.view(h)
