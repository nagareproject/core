# --
# Copyright (c) 2008-2019 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --


class ViewError(LookupError):
    pass


def render(o, renderer, comp, view_name, *args, **kw):
    view = getattr(o, 'render_' + (view_name or ''), None)

    if view is None:
        msg = ('No named view "%s"' % view_name) if view_name else 'No default view'
        raise ViewError(msg + ' for ' + repr(o))

    rendering = view(renderer, comp, view_name, *args, **kw)
    if rendering is None:
        msg = ('View "%s"' % view_name) if view_name else 'Default view'
        raise ViewError(msg + ' for ' + repr(o) + ' returns nothing')

    return rendering


def render_for(cls, view=None, model=None):
    def _(f):
        setattr(cls, 'render_' + (view or model or ''), f)
        return f

    return _
