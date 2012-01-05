#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import component, presentation, callbacks, editor, validator
from nagare.namespaces import xhtml

class MyEditor(editor.Editor):
    fields = ('name', 'age')

    def __init__(self, source):
        super(MyEditor, self).__init__(source, self.fields)

        self.name.validate(lambda v: validator.to_string(v, strip=True).not_empty().to_string())
        self.age.validate(lambda v: validator.to_int(v).lesser_than(50).greater_than(0).to_int())


    def commit(self, comp):
        if super(MyEditor, self).commit(self.fields):
            comp.answer((self.name()))


    def setValues(self, name, age, comp):
        self.name(name)
        self.age(age)
        self.commit(comp)


class MyApp:
    def __init__(self):
        self.name = 'Foo'
        self.age  = 5


def call(o1, o2, model=None):
    component.call_wrapper(lambda: o1.call(o2, model))


def test1():
    """ Form - validation OK """
    o = MyApp()

    app = component.Component(o, model=None)
    assert app().name == 'Foo'
    assert app().age  == 5

    editor = MyEditor(app())

    call(app, editor)
    assert app().name() == 'Foo'
    assert app().age()  == 5
    assert o.name == 'Foo'
    assert o.age  == 5

    # Validation OK
    editor.setValues('Bar', 4, app)
    assert o.name == 'Bar'
    assert o.age  == 4


def test2():
    """ Form - validation KO """
    o = MyApp()

    app = component.Component(o, model=None)

    editor = MyEditor(o)
    call(app, editor)

    # Validation KO
    editor.setValues('Bar', 1000, app)
    # Editor values changes
    assert app().name() == 'Bar'
    assert app().age()  == 1000
    # App values doesn't changes
    assert o.name == 'Foo'
    assert o.age  == 5

    # Validation OK
    editor.setValues('Bar', 10, app)
    assert o.name == 'Bar'
    assert o.age  == 10


def test3():
    """ Form - validation KO & Cancel """
    o = MyApp()

    app = component.Component(o, model=None)

    editor = MyEditor(app())
    call(app, editor)

    # Validation KO
    editor.setValues('Bar', 1000, app)
    # Editor values changes
    assert app().name() == 'Bar'
    assert app().age()  == 1000
    # App values doesn't changes
    assert o.name == 'Foo'
    assert o.age  == 5

    # Cancel
    app.answer()
    assert o.name == 'Foo'
    assert o.age  == 5



class MyStringEditor(editor.Editor):
    fields = ('name',)

    def __init__(self, source):
        super(MyStringEditor, self).__init__(source, self.fields)


    def commit(self, comp):
        if super(MyStringEditor, self).commit(self.fields):
            comp.answer((self.name()))


    def setValues(self, name, comp):
        self.name(name)
        self.commit(comp)


class MyStringEditor1(MyStringEditor):

    def __init__(self, source):
        super(MyStringEditor1, self).__init__(source)
        self.name.validate(lambda v: validator.to_string(v, strip=True).not_empty())



def test4():
    """ Form - test string validators - not_empty """
    o = MyApp()

    app = component.Component(o, model=None)

    editor = MyStringEditor1(app())
    call(app, editor)

    # Validation KO
    editor.setValues('', app)
    assert editor.name.error == "Can't be empty"

    editor.setValues('abcd', app)
    assert editor.name.error is None



class MyStringEditor2(MyStringEditor):

    def __init__(self, source):
        super(MyStringEditor2, self).__init__(source)
        self.name.validate(lambda v: validator.to_string(v, strip=True).match(r'^[a-d]+$', msg="test5 - Incorrect format"))


def test5():
    """ Form - test string validators - match """
    o = MyApp()

    app = component.Component(o, model=None)

    editor = MyStringEditor2(app())
    call(app, editor)

    # Validation KO
    editor.setValues('abrab', app)
    assert editor.name.error == "test5 - Incorrect format"

    editor.setValues('abab', app)
    assert editor.name.error is None


class MyStringEditor3(MyStringEditor):

    def __init__(self, source):
        super(MyStringEditor3, self).__init__(source)
        self.name.validate(lambda v: validator.to_string(v, strip=True).shorter_than(5, msg="test6 - Length must be shorter than %(max)d characters"))


def test6():
    """ Form - test string validators - shorter_than """
    o = MyApp()

    app = component.Component(o, model=None)

    editor = MyStringEditor3(app())
    call(app, editor)

    # Validation KO
    editor.setValues('123456', app)
    assert editor.name.error == "test6 - Length must be shorter than 5 characters"

    editor.setValues('1234', app)
    assert editor.name.error is None


class MyStringEditor4(MyStringEditor):

    def __init__(self, source):
        super(MyStringEditor4, self).__init__(source)
        self.name.validate(lambda v: validator.to_string(v, strip=True).length_equal(5, msg="test7 - Length must be %(len)d characters"))


def test7():
    """ Form - test string validators - length_equal  """
    o = MyApp()

    app = component.Component(o, model=None)

    editor = MyStringEditor4(app())
    call(app, editor)

    # Validation KO
    editor.setValues('123456', app)
    assert editor.name.error == "test7 - Length must be 5 characters"

    editor.setValues('1234', app)
    assert editor.name.error == "test7 - Length must be 5 characters"

    editor.setValues('12345', app)
    assert editor.name.error is None


class MyStringEditor5(MyStringEditor):

    def __init__(self, source):
        super(MyStringEditor5, self).__init__(source)
        self.name.validate(lambda v: validator.to_string(v, strip=True).longer_than(5).shorter_or_equal_than(8).not_empty().match(r'^[1-9]+$'))


def test8():
    """ Form - test string validators - multiple validators """
    o = MyApp()

    app = component.Component(o, model=None)

    editor = MyStringEditor5(app())
    call(app, editor)

    # Validation KO
    editor.setValues('', app)
    assert editor.name.error is not None

    editor.setValues('1234', app)
    assert editor.name.error is not None

    editor.setValues('123456789', app)
    assert editor.name.error is not None

    editor.setValues('abcdefg', app)
    assert editor.name.error is not None

    editor.setValues('123456', app)
    assert editor.name.error is None

def test9():
    p = editor.Property()
    assert (p.input is None) and (p.value is None) and (p.error is None)

def test10():
    p = editor.Property(5)
    assert (p.input == p.value == 5) and (p.error is None)

def check(v):
    if v > 10:
        raise ValueError('invalid')
    return v

def test11():
    p = editor.Property(5).validate(check)
    assert (p.input == p.value == 5) and (p.error is None)

def test12():
    p = editor.Property(15).validate(check)
    assert (p.input == 15) and (p.value == 15) and (p.error is None)

def test13():
    p = editor.Property().validate(check)
    p.set(5)
    assert (p.input == p.value == 5) and (p.error is None)

def test14():
    p = editor.Property().validate(check)
    p.set(15)
    assert (p.input == 15) and (p.value is None) and (p.error == 'invalid')
