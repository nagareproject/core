# --
# Copyright (c) 2008-2020 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from nagare import editor, validator


class MyEditor(editor.Editor):
    fields = ('name', 'age')

    def __init__(self, source):
        super(MyEditor, self).__init__(source, self.fields)

        self.name.validate(lambda v: validator.to_string(v, strip=True).not_empty().to_string())
        self.age.validate(lambda v: validator.to_int(v).lesser_than(50).greater_than(0).to_int())

    def commit(self):
        super(MyEditor, self).commit(self.fields)

    def set_values(self, name, age):
        self.name(name)
        self.age(age)


class MyApp:
    def __init__(self):
        self.name = 'Foo'
        self.age = 5


def test1():
    """ Form - validation OK """
    o = MyApp()

    assert o.name == 'Foo'
    assert o.age == 5

    editor = MyEditor(o)

    assert o.name == 'Foo'
    assert o.age == 5

    editor.set_values('Bar', '4')

    # Editor values are changed
    assert editor.name.input == editor.name() == 'Bar'
    assert editor.age.input == editor.age() == '4'
    assert editor.age.value == 4

    # App values aren't changed
    assert o.name == 'Foo'
    assert o.age == 5

    editor.commit()

    # App values are changed
    assert o.name == 'Bar'
    assert o.age == 4


def test2():
    """ Form - validation KO """
    o = MyApp()

    assert o.name == 'Foo'
    assert o.age == 5

    editor = MyEditor(o)

    assert o.name == 'Foo'
    assert o.age == 5

    editor.set_values('Bar', '1000')

    # Editor values are changed
    assert editor.name.input == editor.name() == 'Bar'
    assert editor.age.input == editor.age() == '1000'
    assert editor.age.value == 5

    # App values aren't changed
    assert o.name == 'Foo'
    assert o.age == 5

    editor.commit()

    # App values aren't changed
    assert o.name == 'Foo'
    assert o.age == 5


class MyStringEditor(editor.Editor):
    fields = ('name',)

    def __init__(self, source):
        super(MyStringEditor, self).__init__(source, self.fields)

    def commit(self):
        super(MyStringEditor, self).commit(self.fields)

    def set_values(self, name):
        self.name(name)


class MyStringEditor1(MyStringEditor):
    def __init__(self, source):
        super(MyStringEditor1, self).__init__(source)

        self.name.validate(lambda v: validator.to_string(v, strip=True).not_empty())


def test4():
    """ Form - test string validators - not_empty """
    editor = MyStringEditor1(MyApp())

    # Validation OK
    editor.set_values('abcd')
    assert editor.name.error is None
    assert editor.name.input == editor.name() == 'abcd'
    assert editor.name.value == 'abcd'

    # Validation KO
    editor.set_values('')
    assert editor.name.error == "Can't be empty"
    assert editor.name.input == editor.name() == ''
    assert editor.name.value == 'abcd'


class MyStringEditor2(MyStringEditor):
    def __init__(self, source):
        super(MyStringEditor2, self).__init__(source)
        self.name.validate(lambda v: validator.to_string(v, strip=True).match(r'^[a-d]+$', msg="test5 - Incorrect format"))


def test5():
    """ Form - test string validators - match """
    editor = MyStringEditor2(MyApp())

    # Validation OK
    editor.set_values('abab')
    assert editor.name.error is None
    assert editor.name.input == editor.name() == 'abab'
    assert editor.name.value == 'abab'

    # Validation KO
    editor.set_values('abrab')
    assert editor.name.error == "test5 - Incorrect format"
    assert editor.name.input == editor.name() == 'abrab'
    assert editor.name.value == 'abab'


class MyStringEditor3(MyStringEditor):
    def __init__(self, source):
        super(MyStringEditor3, self).__init__(source)
        self.name.validate(lambda v: validator.to_string(v, strip=True).shorter_than(5, msg="test6 - Length must be shorter than %(max)d characters"))


def test6():
    """ Form - test string validators - shorter_than """
    editor = MyStringEditor3(MyApp())

    # Validation OK
    editor.set_values('1234')
    assert editor.name.error is None
    assert editor.name.input == editor.name() == '1234'
    assert editor.name.value == '1234'

    # Validation KO
    editor.set_values('123456')
    assert editor.name.error == "test6 - Length must be shorter than 5 characters"
    assert editor.name.input == editor.name() == '123456'
    assert editor.name.value == '1234'


class MyStringEditor4(MyStringEditor):
    def __init__(self, source):
        super(MyStringEditor4, self).__init__(source)
        self.name.validate(lambda v: validator.to_string(v, strip=True).length_equal(5, msg="test7 - Length must be %(len)d characters"))


def test7():
    """ Form - test string validators - length_equal  """
    editor = MyStringEditor4(MyApp())

    # Validation OK
    editor.set_values('12345')
    assert editor.name.error is None
    assert editor.name.input == editor.name() == '12345'
    assert editor.name.value == '12345'

    # Validation KO
    editor.set_values('123456')
    assert editor.name.error == "test7 - Length must be 5 characters"
    assert editor.name.input == editor.name() == '123456'
    assert editor.name.value == '12345'

    # Validation KO
    editor.set_values('1234')
    assert editor.name.error == "test7 - Length must be 5 characters"
    assert editor.name.input == editor.name() == '1234'
    assert editor.name.value == '12345'


class MyStringEditor5(MyStringEditor):
    def __init__(self, source):
        super(MyStringEditor5, self).__init__(source)
        self.name.validate(lambda v: validator.to_string(v, strip=True).longer_than(5).shorter_or_equal_than(8).not_empty().match(r'^[1-9]+$'))


def test8():
    """ Form - test string validators - multiple validators """
    editor = MyStringEditor5(MyApp())

    # Validation OK
    editor.set_values('123456')
    assert editor.name.error is None
    assert editor.name.input == editor.name() == '123456'
    assert editor.name.value == '123456'

    # Validation KO
    editor.set_values('')
    assert editor.name.error is not None
    assert editor.name.input == editor.name() == ''
    assert editor.name.value == '123456'

    # Validation KO
    editor.set_values('1234')
    assert editor.name.error is not None
    assert editor.name.input == editor.name() == '1234'
    assert editor.name.value == '123456'

    # Validation KO
    editor.set_values('123456789')
    assert editor.name.error is not None
    assert editor.name.input == editor.name() == '123456789'
    assert editor.name.value == '123456'

    # Validation KO
    editor.set_values('abcdefg')
    assert editor.name.error is not None
    assert editor.name.input == editor.name() == 'abcdefg'
    assert editor.name.value == '123456'


def test9():
    p = editor.Property()
    assert (p.input is None) and (p() is None) and (p.value is None) and (p.error is None)


def test10():
    p = editor.Property(5)
    assert (p.input == p() == p.value == 5) and (p.error is None)


def check(v):
    if v > 10:
        raise ValueError('invalid')
    return v


def test11():
    p = editor.Property(5).validate(check)
    assert (p.input == p() == p.value == 5) and (p.error is None)


def test12():
    p = editor.Property(15).validate(check)
    assert (p.input == p() == p.value == 15) and (p.error is None)


def test13():
    p = editor.Property().validate(check)
    p(5)
    assert (p.input == p() == p.value == 5) and (p.error is None)


def test14():
    p = editor.Property().validate(check)
    p(15)
    assert (p.input == p() == 15) and (p.value is None) and (p.error == 'invalid')
