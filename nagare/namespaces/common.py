#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Base class of all the renderers"""

import random

class Renderer(object):
    def new(self):
        """Create a new renderer from the same type of this renderer
        """
        return self.__class__(self)

    def start_rendering(self, comp, model):
        """Method calls before to render a component

        In:
          - ``comp`` -- the component to render
          - ``model`` -- the view to render
        """
        pass

    def end_rendering(self, output):
        """Method call after the rendering of the component

        In:
          - ``output`` -- the rendering tree
        """
        return output

    def generate_id(self, prefix=''):
        """Generate a random id

        In:
          - ``prefix`` -- prefix of the generated id
        """
        return prefix+str(random.randint(10000000, 99999999))

    def __reduce__(self):
        """Prevent a renderer to be pickled

        Prevent the common error of capturing the renderer into the closure
        of a callback
        """
        raise TypeError("can't pickle Renderer objects (are you using a renderer object in a callback ?)")
