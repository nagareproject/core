# -- # Copyright (c) 2008-2023 Net-ng.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from nagare.renderers import html
from nagare.component import Component
from nagare.continuation import call_wrapper
from nagare.presentation import render_for, CURRENT_VIEW, ANON_VIEW


class C(object):
    pass


@render_for(C)
def render(*args):
    return 'default'


@render_for(C, 'view1')
def render_view1(*args):
    return 'view1'


@render_for(C, 'view2')
def render_view2(*args):
    return 'view2'


@render_for(C, 'view3')
def render_view3(*args):
    return 'view3'


def test_view_at_creation():
    h = html.Renderer()

    comp = Component(C)
    assert comp.render(h) == 'default'

    comp = Component(C, None)
    assert comp.render(h) == 'default'

    comp = Component(C, 'view1')
    assert comp.render(h) == 'view1'


def test_view_at_rendering():
    h = html.Renderer()

    comp = Component(C)
    assert comp.render(h, CURRENT_VIEW) == 'default'
    assert comp.render(h, ANON_VIEW) == 'default'
    assert comp.render(h, 'view1') == 'view1'

    comp = Component(C, 'view1')
    assert comp.render(h, CURRENT_VIEW) == 'view1'
    assert comp.render(h, ANON_VIEW) == 'default'
    assert comp.render(h, 'view2') == 'view2'


def test_view_in_becomes():
    h = html.Renderer()

    comp = Component(C)
    assert comp.render(h) == 'default'
    comp.becomes(view=CURRENT_VIEW)
    assert comp.render(h) == 'default'
    comp.becomes(view=ANON_VIEW)
    assert comp.render(h) == 'default'

    comp = Component(C, 'view1')
    assert comp.render(h) == 'view1'
    comp.becomes(view=CURRENT_VIEW)
    assert comp.render(h) == 'view1'
    comp.becomes(view=ANON_VIEW)
    assert comp.render(h) == 'default'

    comp = Component(C, 'view1')
    comp.becomes(view='view2')
    assert comp.render(h) == 'view2'
    comp.becomes(view=CURRENT_VIEW)
    assert comp.render(h) == 'view2'
    comp.becomes(view=ANON_VIEW)
    assert comp.render(h) == 'default'

    comp = Component(C)
    comp.becomes(view=ANON_VIEW)
    assert comp.render(h, 'view3') == 'view3'
    assert comp.render(h) == 'default'
    comp.becomes(view=CURRENT_VIEW)
    assert comp.render(h, 'view3') == 'view3'
    assert comp.render(h) == 'default'

    comp = Component(C, 'view1')
    comp.becomes(view=ANON_VIEW)
    assert comp.render(h, 'view2') == 'view2'
    assert comp.render(h) == 'default'
    comp.becomes(view=CURRENT_VIEW)
    assert comp.render(h, 'view2') == 'view2'
    assert comp.render(h) == 'default'

    comp = Component(C, 'view1')
    comp.becomes(view='view2')
    assert comp.render(h, 'view3') == 'view3'
    assert comp.render(h) == 'view2'
    comp.becomes(view=CURRENT_VIEW)
    assert comp.render(h, 'view3') == 'view3'
    assert comp.render(h) == 'view2'
    comp.becomes(view=ANON_VIEW)
    assert comp.render(h, 'view3') == 'view3'
    assert comp.render(h) == 'default'

    comp = Component(C, 'view1')
    comp.becomes(view='view2')
    assert comp.render(h) == 'view2'
    assert comp.render(h, ANON_VIEW) == 'default'
    assert comp.render(h) == 'view2'
    assert comp.render(h, CURRENT_VIEW) == 'view2'
    assert comp.render(h) == 'view2'


def test_view_in_call():
    h = html.Renderer()

    comp = Component(C)
    call_wrapper(comp.call, view=ANON_VIEW)
    assert comp.render(h) == 'default'
    comp.answer()
    assert comp.render(h) == 'default'

    comp = Component(C)
    call_wrapper(comp.call, view='view1')
    assert comp.render(h) == 'view1'
    comp.answer()
    assert comp.render(h) == 'default'

    comp = Component(C, 'view1')
    call_wrapper(comp.call)
    assert comp.render(h) == 'default'
    comp.answer()
    assert comp.render(h) == 'view1'

    comp = Component(C, 'view1')
    call_wrapper(comp.call, view='view2')
    assert comp.render(h) == 'view2'
    comp.answer()
    assert comp.render(h) == 'view1'

    comp = Component(C, 'view1')
    call_wrapper(comp.call, view='view2')
    assert comp.render(h, 'view3') == 'view3'
    comp.answer()
    assert comp.render(h) == 'view1'
