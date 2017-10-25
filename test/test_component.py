# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from nagare import component, presentation, continuation, var
from nagare.namespaces import xhtml


class Foo(object):
    def __init__(self):
        self.my_property = "I'm foo"

    def set_my_property(self, v):
        self.my_property = v


class Bar(Foo):
    def __init__(self):
        self.set_my_property("I'm bar")


class Foobar:
    def __init__(self):
        self.my_property = component.Component(Foo())


# -------------------------------------------------------------------------------------------------------

class App1:
    def __init__(self):
        self.foo = Foo()

        self.bar = component.Component(Bar())
        self.bar.on_answer(self.foo.set_my_property)


def test1():
    """Component - test on_answer/answer"""
    app = App1()

    assert app.foo.my_property == "I'm foo"

    app.bar.answer("I'm bar")
    assert app.foo.my_property == "I'm bar"

    app.bar.answer("I'm foo again")
    assert app.foo.my_property == "I'm foo again"


# -------------------------------------------------------------------------------------------------------

def test2():
    """Component - becomes"""
    app = Foobar()

    assert isinstance(app.my_property(), Foo)
    assert not bool(app.my_property.model)
    assert app.my_property().my_property == "I'm foo"

    app.my_property.becomes(Bar(), model='bar')

    assert isinstance(app.my_property(), Bar)
    assert app.my_property.model == 'bar'
    assert app.my_property().my_property == "I'm bar"

    app.my_property.becomes(Foo())
    assert isinstance(app.my_property(), Foo)
    assert not bool(app.my_property.model)
    assert app.my_property().my_property == "I'm foo"


# -------------------------------------------------------------------------------------------------------

if continuation.has_continuation:
    def test3():
        """Component - call"""
        v = var.Var(42)
        app = Foobar()

        app.my_property.becomes(Foo(), model='foo')
        assert isinstance(app.my_property(), Foo)
        assert app.my_property.model == 'foo'

        continuation.call_wrapper(lambda: v(app.my_property.call(Bar(), model='bar')))

        assert isinstance(app.my_property(), Bar)
        assert app.my_property.model == 'bar'

        app.my_property.answer("I'm bar")

        assert isinstance(app.my_property(), Foo)
        assert app.my_property.model == 'foo'
        assert v() == "I'm bar"


# -------------------------------------------------------------------------------------------------------

@presentation.render_for(Bar)
def render(self, h, *args):
    return h.table(h.tr(h.td("I'm Bar")))


@presentation.render_for(Bar, model='foo')
def render_bar(self, h, *args):
    return h.h1("I'm bar in foo")


def test4():
    """Component - render"""
    foo = component.Component(Foo())

    h = xhtml.Renderer()
    try:
        # No default model for Foo() objects
        foo.render(h)
    except:
        pass
    else:
        assert False

    foo.becomes(Bar())
    assert foo.render(h).write_htmlstring(pretty_print=True).strip() == "<table><tr><td>I'm Bar</td></tr></table>"

    foo.becomes(model='foo')
    assert foo.render(h).write_htmlstring(pretty_print=True).strip() == "<h1>I'm bar in foo</h1>"
