#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Helpers to validate form datum"""

from nagare import var

class Property(var.Var):
    """An editor property

    An editor property has:

      - a current value: this value is always set
      - a valid value: this value is only set if the validating function has validated it
      - a validating function: a function that raise an exception if the value
        is invalid else, return the value to set
      - the message of the last validation error or ``None`` if the current value
        is valid
    """
    def __init__(self, v=None):
        """Initialisation

        Members are:

          - ``self.input`` -- the current value
          - ``self.value`` -- the last valid value
          - ``self.error`` -- the last error message
        """
        super(Property, self).__init__(v)

        self.value = v
        self.error = None

    def _validate(self, input):
        """Default validation function

        In:
          - ``input`` -- value to validate

        Return
          - ``input``
        """
        return input

    def validate(self, f):
        """Set the validating function

        In:
          - ``f`` -- the validating function. Called with the value to
            validate. Raise the exception ``ValueError`` is the value is
            invalid. Return the value to be set (i.e a validation function
            can do conversions too)

        Return:
          - ``self``
        """
        self._validate = f
        return self

    def set(self, input):
        """Set the values

        Always set the current value but only the valid value if the validating
        function return OK

        In:
          - ``input`` -- the input string or ``cgi.FieldStorage`` object
        """

        if not hasattr(input, 'file'):
            super(Property, self).set(input)

        try:
            self.value = self._validate(input) # Call the validating function
            if callable(self.value):
                self.value = self.value()
            self.error = None
        except ValueError, data:
            self.error = data[0]

    def commit(self, o, name):
        """Set the attribute ``name`` of the object ``o`` with the valid value

        In:
          - ``o`` -- target object
          - ``name`` -- name of the attribute to set in the target object
        """
        setattr(o, name, self.value)


class Editor(object):
    """An editor object act as a buffer between the datum received from a
    form an the target object.

    An editor object has a set of editor properties, each with a possible
    validating function, and will modified the target object only if all
    the validating functions are passed ok.
    """
    def __init__(self, target, properties_to_create=()):
        """Initialisation

        Create the set of properties from some attributes of the target object

        In:
          - ``target`` - the target object
          - ``properties_to_create`` -- name of the attritbutes to read from the
            target object, then to write into
        """
        self.target = target

        for name in properties_to_create:
            # Create a property with the same name and value than the attribute
            # of the target object
            setattr(self, name, Property(getattr(target, name)))

    def is_validated(self, properties_to_validate):
        """Check the validity of a set of properties

        In:
          - ``properties_to_validate`` -- name of the properties to validate

        Return
          - a boolean
        """
        return all([getattr(self, name).error is None for name in properties_to_validate])

    def commit(self, properties_to_commit=(), properties_to_validate=()):
        """Write back the value of the property to the target object, only if
        they are all valid

        In:
          - ``properties_to_commit`` -- names of properties to check then to
            write to the target object
          - ``properties_to_validate`` -- additional names of properties to check

        Return:
          - are all the properties valid ?
        """
        validated = self.is_validated(set(properties_to_commit) | set(properties_to_validate))

        if validated:
            for name in properties_to_commit:
                getattr(self, name).commit(self.target, name)

        return validated
