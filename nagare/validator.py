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
        if strip:
            v = v.strip(chars)

        if rstrip:
            v = v.rstrip(chars)

        if lstrip:
            v = v.lstrip(chars)

        self.value = v


class IntValidator(Validator):
    """Conversion and validation of integers
    """
    def __init__(self, v, *args, **kw):
        """Initialisation

        Check that the value is an integer

        In:
          - ``v`` -- value to validate
        """
        super(IntValidator, self).__init__(v, *args, **kw)

        try:
            self.value = int(self.value)
        except (ValueError, TypeError):
            raise ValueError('Must be an integer')

    def to_int(self):
        """Return the value, converted to an integer

        Return:
          - the integer value
        """
        return self.value
    __call__ = to_int

    def lesser_than(self, max, msg='Must be lesser than %(max)d'):
        """Check that the value is lesser than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if self.value < max:
            return self

        raise ValueError(msg % { 'value' : self.value, 'max' : max })

    def lesser_or_equal_than(self, max, msg='Must be lesser or equal than %(max)d'):
        """Check that the value is lesser or equal than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if self.value <= max:
            return self

        raise ValueError(msg % { 'value' : self.value, 'max' : max })

    def greater_than(self, min, msg='Must be greater than %(min)d'):
        """Check that the value is greater than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if self.value > min:
            return self

        raise ValueError(msg % { 'value' : self.value, 'min' : min })

    def greater_or_equal_than(self, min, msg='Must be greater or equal than %(min)d'):
        """Check that the value is greater or equal than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if self.value >= min:
            return self

        raise ValueError(msg % { 'value' : self.value, 'min' : min })


class StringValidator(Validator):
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

    def not_empty(self, msg="Can't be empty"):
        """Check that the value is not empty

        In:
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) != 0:
            return self

        raise ValueError(msg)

    def match(self, r, msg='Incorrect format'):
        """Check that the value respects a format given as a regexp

        In:
          - ``r`` -- the regexp
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if re.match(r, self.value):
            return self

        raise ValueError(msg % { 'value' : self.value })

    def shorter_than(self, max, msg='Length must be shorter than %(max)d characters'):
        """Check that the value is shorter than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) < max:
            return self

        raise ValueError(msg % { 'value' : self.value, 'max' : max })

    def shorter_or_equal_than(self, max, msg='Length must be shorter or equal than %(max)d characters'):
        """Check that the value is shorter or equal than a limit

        In:
          - ``max`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) <= max:
            return self

        raise ValueError(msg % { 'value' : self.value, 'max' : max })

    def length_equal(self, v, msg='Length must be %(len)d characters'):
        """Check that the value has an exact length

        In:
          - ``v`` -- the length
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) == v:
            return self

        raise ValueError(msg % { 'value' : self.value, 'len' : v })

    def longer_than(self, min, msg='Length must be longer than %(min)d characters'):
        """Check that the value is longer than a limit

        In:
          - ``min`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) > min:
            return self

        raise ValueError(msg % { 'value' : self.value, 'min' : min })

    def longer_or_equal_than(self, min, msg='Length must be longer or equal than %(min)d characters'):
        """Check that the value is longer or equal than a limit

        In:
          - ``min`` -- the limit
          - ``msg`` -- message to raise

        Return:
          - ``self``
        """
        if len(self.value) >= min:
            return self

        raise ValueError(msg % { 'value' : self.value, 'min' : min })

    def isalnum(self, msg='some characters are not alphanumeric'):
        if self.value.isalnum():
            return self

        raise ValueError(msg % { 'value' : self.value })

    def isalpha(self, msg='some characters are not alphabetic'):
        if self.value.isalpha():
            return self

        raise ValueError(msg % { 'value' : self.value })

    def isdigit(self, msg='some characters are not digits'):
        if self.value.isdigit():
            return self

        raise ValueError(msg % { 'value' : self.value })

    def islower(self, msg='some characters are not lowercase'):
        if self.value.islower():
            return self

        raise ValueError(msg % { 'value' : self.value })


    def isupper(self, msg='some characters are not uppercase'):
        if self.value.isupper():
            return self

        raise ValueError(msg % { 'value' : self.value })

    def isspace(self, msg='some characters are not whitespace'):
        if self.value.isspace():
            return self

        raise ValueError(msg % { 'value' : self.value })

# Aliases
to_int = IntValidator
to_string = StringValidator
