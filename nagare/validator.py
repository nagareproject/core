#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Set of validating objects

Suitable to be the validating functions of ``editor.property`` objects
"""

import re

from nagare import i18n, partial


_L = partial.Partial(i18n._L, domain='nagare')


class Validator(object):
    """Base class for the validation objects
    """
    def __init__(self, v, strip=False, rstrip=False, lstrip=False, chars=None):
        """Initialization

        This object only do conversions, possibly removing characters at the
        beginning / end of the value

        In:
          - ``v`` -- value to validate
          - ``strip`` -- remove the characters at the beginning and the end
          - ``rstrip`` -- remove the characters at the end
          - ``lstrip`` -- remove the characters at the beginning
          - ``chars`` -- list of characters to removed, spaces by default
        """
        if not isinstance(v, basestring):
            raise ValueError('Input must be a string')

        if strip:
            v = v.strip(chars)

        if rstrip:
            v = v.rstrip(chars)

        if lstrip:
            v = v.lstrip(chars)

        self.value = v


class _IntValidator(Validator):
    """Conversion and validation of integers
    """
    def __init__(self, v, base=10, *args, **kw):
        """Initialisation

        Check that the value is an integer

        In:
          - ``v`` -- value to validate
        """
        super(_IntValidator, self).__init__(v, *args, **kw)

        try:
            self.value = int(self.value, base)
        except (ValueError, TypeError):
            raise ValueError('Must be an integer')

    def to_int(self):
        """Return the value, converted to an integer

        Return:
          - the integer value
        """
        return self.value
    __call__ = to_int

    def lesser_than(self, max, msg=_L('Must be lesser than %(max)d')):
        """Check that the value is lesser than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if self.value < max:
            return self

        raise ValueError(msg % {'value': self.value, 'max': max})

    def lesser_or_equal_than(self, max, msg=_L('Must be lesser or equal than %(max)d')):
        """Check that the value is lesser or equal than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if self.value <= max:
            return self

        raise ValueError(msg % {'value': self.value, 'max': max})

    def greater_than(self, min, msg=_L('Must be greater than %(min)d')):
        """Check that the value is greater than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if self.value > min:
            return self

        raise ValueError(msg % {'value': self.value, 'min': min})

    def greater_or_equal_than(self, min, msg=_L('Must be greater or equal than %(min)d')):
        """Check that the value is greater or equal than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if self.value >= min:
            return self

        raise ValueError(msg % {'value': self.value, 'min': min})


class _StringValidator(Validator):
    """Conversion and validation of string
    """
    def to_string(self):
        """Return the value, converted to a string

        Return:
          - the string value
        """
        return self.value
    __call__ = to_string

    def to_int(self, base=10):
        """Return the value, converted to an integer

        In:
          - ``base`` -- base for the conversion

        Return:
          - the integer value
        """
        return int(self.value, base=base)

    def not_empty(self, msg=_L("Can't be empty")):
        """Check that the value is not empty

        In:
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) != 0:
            return self

        raise ValueError(msg)

    def match(self, r, msg=_L('Incorrect format')):
        """Check that the value respects a format given as a regexp

        In:
          - ``r`` -- the regexp
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if re.match(r, self.value):
            return self

        raise ValueError(msg % {'value': self.value})

    def shorter_than(self, max, msg=_L('Length must be shorter than %(max)d characters')):
        """Check that the value is shorter than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) < max:
            return self

        raise ValueError(msg % {'value': self.value, 'max': max})

    def shorter_or_equal_than(self, max, msg=_L('Length must be shorter or equal than %(max)d characters')):
        """Check that the value is shorter or equal than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) <= max:
            return self

        raise ValueError(msg % {'value': self.value, 'max': max})

    def length_equal(self, v, msg=_L('Length must be %(len)d characters')):
        """Check that the value has an exact length

        In:
          - ``v`` -- the length
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) == v:
            return self

        raise ValueError(msg % {'value': self.value, 'len': v})

    def longer_than(self, min, msg=_L('Length must be longer than %(min)d characters')):
        """Check that the value is longer than a limit

        In:
          - ``min`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) > min:
            return self

        raise ValueError(msg % {'value': self.value, 'min': min})

    def longer_or_equal_than(self, min, msg=_L('Length must be longer or equal than %(min)d characters')):
        """Check that the value is longer or equal than a limit

        In:
          - ``min`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) >= min:
            return self

        raise ValueError(msg % {'value': self.value, 'min': min})

    def isalnum(self, msg=_L('Some characters are not alphanumeric')):
        if self.value.isalnum():
            return self

        raise ValueError(msg % {'value': self.value})

    def isalpha(self, msg=_L('Some characters are not alphabetic')):
        if self.value.isalpha():
            return self

        raise ValueError(msg % {'value': self.value})

    def isdigit(self, msg=_L('Some characters are not digits')):
        if self.value.isdigit():
            return self

        raise ValueError(msg % {'value': self.value})

    def islower(self, msg=_L('Some characters are not lowercase')):
        if self.value.islower():
            return self

        raise ValueError(msg % {'value': self.value})

    def isupper(self, msg=_L('Some characters are not uppercase')):
        if self.value.isupper():
            return self

        raise ValueError(msg % {'value': self.value})

    def isspace(self, msg=_L('Some characters are not whitespace')):
        if self.value.isspace():
            return self

        raise ValueError(msg % {'value': self.value})


class DualCallable(object):
    """"A hackish base class to allow both direct and lazy calls of methods

    For compatibility with the old and new way to built a validation chain.

    Examples:

      - Old validation with direct calls: valid = lambda v: IntValidator(v).greater_than(10)
      - New validation with lazy calls: valid = IntValidator().greater_than(10)
    """
    @classmethod
    def init(cls):
        """Class Initialization

        Read all the methods belonging to the ``cls`` class and extend this class
        with methods of the same names

        In:
          - ``cls`` -- class to proxy
        """
        for method in cls.get_cls().__dict__:
            if not method.startswith('_'):

                def _(m):
                    return lambda self, *args, **kw: self.add_validation(_method=m, *args, **kw)

                setattr(cls, method, _(method))

        return cls

    @classmethod
    def get_cls(cls):
        """Return the class where the methods to call are located
        """
        return cls.__bases__[1]

    def __init__(self, v=None, *args, **kw):
        """Initialization

        If a value is passed, all the methods will be directly called
        else, the method calls will be recorded and called later

        In:
          - ``v`` -- optional value
          - ``args``, ``kw`` -- parameters of ``__init__``
        """
        if v is None:
            self.args = args
            self.kw = kw

            self.methods_chain = []
        else:
            self.args = self.kw = self.methods_chain = None
            super(DualCallable, self).__init__(v, *args, **kw)

    def add_validation(self, *args, **kw):
        """Directly call or record the call to a method

        In:
          - ``_method`` -- method to call (keyword parameter)
          - ``args``, ``kw`` -- parameters of ``_method``
        """
        method = kw.pop('_method')
        if self.methods_chain is None:
            # Call the method
            r = getattr(self.get_cls(), method)(self, *args, **kw)
        else:
            # Record the call
            self.methods_chain.append((method, args, kw))
            r = self

        return r

    def __call__(self, v=None):
        """Final call. Call all the recorded methods

        In:
          - ``v`` -- value to start with

        Return:
          - the final result of all the calls
        """
        if self.methods_chain:
            super(DualCallable, self).__init__(v, *self.args, **self.kw)

            for method, args, kw in self.methods_chain:
                getattr(self.get_cls(), method)(self, *args, **kw)

        return super(DualCallable, self).__call__()


# Mixins
IntValidator = type.__new__(type, 'IntValidator', (DualCallable, _IntValidator), {}).init()
StringValidator = type.__new__(type, 'StringValidator', (DualCallable, _StringValidator), {}).init()

# Aliases
to_int = IntValidator
to_string = StringValidator
