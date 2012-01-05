#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Helper to validate a configuration"""

import configobj
from validate import Validator

def _validate(filename, config):
    """Validate a ``ConfigObj`` object

    In:
      -  ``filename`` -- the path to the configuration file
      - ``config`` -- the ``ConfigObj`` object, created from the configuration file

    Return:
      - yield the error messages
    """
    errors = configobj.flatten_errors(config, config.validate(Validator(), preserve_errors=True))

    for (sections, name, error) in errors:
        yield 'file "%s", section "[%s]", parameter "%s": %s' % (filename, ' / '.join(sections), name, error)

def validate(filename, config, error):
    """Validate a ``ConfigObj`` object

    In:
      -  ``filename`` -- the path to the configuration file
      - ``config`` -- the ``ConfigObj`` object, created from the configuration file
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - is the configuration valid ?
    """
    errors = list(_validate(filename, config))
    if errors:
        error('\n'.join(errors))
        return False

    return True
