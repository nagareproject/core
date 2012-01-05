#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import component, presentation, callbacks
from nagare.namespaces import xhtml

class Foo:

    def __init__(self):
        self.myProperty_1 = "I'm foo"

    def set_myProperty_1(self, newProperty):
        self.myProperty_1 = newProperty

class Bar:

    def __init__(self):
        self.myProperty_2 = "I'm bar"

    def set_myProperty_2(self, newProperty):
        self.myProperty_2 = newProperty

class Foobar:

    def __init__(self):
        self.myProperty = component.Component(Foo())

# -------------------------------------------------------------------------------------------------------

class App1:
    def __init__(self):
        self.foo = component.Component(Foo())

        self.bar = component.Component(Bar())
        self.bar.on_answer(self.foo().set_myProperty_1)


def test1():
    """ MVC - test onAnswer/answer """
    app = App1()
    assert app.foo().myProperty_1 == "I'm foo"
    assert isinstance(app.foo(), Foo)
    assert isinstance(app.foo, component.Component)

    app.bar.answer(app.bar().myProperty_2)
    assert app.foo().myProperty_1 == "I'm bar"

    app.bar.answer("I'm foo again")
    assert app.foo().myProperty_1 == "I'm foo again"


# -------------------------------------------------------------------------------------------------------

def test2():
    """ MVC - becomes """
    app = Foobar()
    assert isinstance(app.myProperty(), Foo)
    assert not bool(app.myProperty.model)
    assert app.myProperty().myProperty_1 == "I'm foo"
    assert not hasattr(app.myProperty(), 'myProperty_2')

    app.myProperty.becomes(Bar(), model='bar')
    assert isinstance(app.myProperty(), Bar)
    assert app.myProperty.model == 'bar'
    assert not hasattr(app.myProperty(), 'myProperty_1')
    assert app.myProperty().myProperty_2 == "I'm bar"

    app.myProperty.becomes(Foo())
    assert isinstance(app.myProperty(), Foo)
    assert not bool(app.myProperty.model)
    assert app.myProperty().myProperty_1 == "I'm foo"
    assert not hasattr(app.myProperty(), 'myProperty_2')


# -------------------------------------------------------------------------------------------------------


def call(o1, o2, model=None):
    component.call_wrapper(lambda: o1().set_myProperty_1(o1.call(o2, model)))


def test3():
    """ MVC - call """
    app = Foobar()

    app.myProperty.becomes(Foo(), model='foo')
    assert app.myProperty.model == 'foo'

    call(app.myProperty, Bar(), model='bar')
    assert app.myProperty.model == 'bar'
    assert isinstance(app.myProperty(), Bar)

    app.myProperty.answer(app.myProperty().myProperty_2)
    assert app.myProperty.model == 'foo'
    assert isinstance(app.myProperty(), Foo)
    assert app.myProperty().myProperty_1 == "I'm bar"


# -------------------------------------------------------------------------------------------------------

@presentation.render_for(Bar)
def render(self, h, *args):
    return h.table(h.tr(h.td("I'm Bar")))


@presentation.render_for(Bar, model='foo')
def render(self, h, *args):
    return h.h1("I'm bar in foo")


def test4():
    """ MVC - render """
    app = Foobar()

    h = xhtml.Renderer()
    try:
        app.myProperty.render(h)
    except:
        pass
    else:
        assert False

    app.myProperty.becomes(Bar())
    assert app.myProperty.render(h).write_htmlstring(pretty_print=True).strip() == "<table><tr><td>I'm Bar</td></tr></table>"

    app.myProperty.becomes(Bar(), model='foo')
    assert app.myProperty.render(h).write_htmlstring(pretty_print=True).strip() == "<h1>I'm bar in foo</h1>"

