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


def render(o, renderer, comp, view_name):
    view = getattr(o, 'render_' + (view_name or ''), None)

    if view is None:
        msg = ('No named view "%s"' % view_name) if view_name else 'No default view'
        raise ViewError(msg + ' for ' + repr(o))

    return view(renderer, comp, view_name)


def render_for(cls, view=None, model=None):
    return lambda f: setattr(cls, 'render_' + (view or model or ''), f)
