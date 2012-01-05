#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import os, StringIO

import logging
import logging.config

import configobj

from nagare import local

# -----------------------------------------------------------------------------

logging._srcfile = __file__[:-1] if __file__.endswith(('.pyc', '.pyo')) else __file__

# -----------------------------------------------------------------------------

def get_logger(name='.'):
    if name is None:
        name = '.'

    if name.startswith('.'):
        try:
            name = (local.request.logger_name + name).rstrip('.')
        except AttributeError:
            name = 'nagare.application'

    return logging.getLogger(name)

def set_logger(name):
    local.request.logger_name = name

def debug(msg, *args, **kw):
    get_logger().debug(msg, *args, **kw)

def info(msg, *args, **kw):
    get_logger().info(msg, *args, **kw)

def warning(msg, *args, **kw):
    get_logger().warning(msg, *args, **kw)

def error(msg, *args, **kw):
    get_logger().error(msg, *args, **kw)

def critical(msg, *args, **kw):
    get_logger().critical(msg, *args, **kw)

def exception(msg, *args):
    get_logger().exception(msg, *args)

def log(level, msg, *args, **kw):
    get_logger().exception(level, msg, *args, **kw)

# -----------------------------------------------------------------------------

loggers = ['root']
handlers = []
formatters = []

apps_log_conf = configobj.ConfigObj({
                                            'loggers' : { 'keys' : '' },
                                            'handlers' : { 'keys' : '' },
                                            'formatters' : { 'keys' : '' },
                                            'logger_root' : { 'handlers' : '' }
                                        }, list_values=False, indent_type='')

def configure(log_conf, app_name=None):
    """Merge all the applications logging configurations

    In:
      - ``log_conf`` -- an application logging configuration
      - ``app_name`` -- the name of the application
    """
    app_default_conf = configobj.ConfigObj(indent_type='', interpolation=False)

    if app_name:
        # The default application configuration
        app_default = {
            'logger_app_'+app_name : {
                'qualname' : 'nagare.application.'+app_name,
                'level' : 'INFO',
                'handlers' : 'app_'+app_name,
                'propagate' : '1'
            },

            'handler_app_'+app_name : {
                'class' : 'StreamHandler',
                'formatter' : 'app_'+app_name,
                'args' : '(sys.stderr,)'
            },

            'formatter_app_'+app_name : {
                'format' : '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }

        # Start with the default configuration
        app_default_conf.merge(configobj.ConfigObj(app_default, indent_type='', interpolation=False))

        # Create a dedicated logger, handler and formatter for the application
        loggers.append('app_'+app_name)
        handlers.append('app_'+app_name)
        formatters.append('app_'+app_name)

        # Create the list of all the handlers of the dedicated logger
        handler = log_conf.get('logger', {}).pop('handlers', None)
        if handler:
            app_default_conf['logger_app_'+app_name]['handlers'] += (', ' + handler)

        logger_sections = [values for (section, values) in log_conf.items() if section.startswith('logger_')]

        for logger_section in logger_sections:
            if ('qualname' in logger_section) and logger_section['qualname'].startswith('.'):
                logger_section['qualname'] = ('nagare.application.' + app_name + logger_section['qualname']).rstrip('.')

        # Use the generic 'logger', 'handler' and 'formatter' sections to
        # configure the dedicated logger, handler and formatter
        for section in ('logger', 'handler', 'formatter'):
            log_conf[section+'_app_'+app_name] = log_conf.pop(section, {})

    # Merge the loggers list
    keys = log_conf.get('loggers', {}).get('keys')
    if keys:
        if isinstance(keys, basestring):
            keys = [keys]
        loggers.extend(keys)

    # Merge the handlers list
    keys = log_conf.get('handlers', {}).get('keys')
    if keys:
        if isinstance(keys, basestring):
            keys = [keys]
        handlers.extend(keys)

    # Merge the formatters list
    keys = log_conf.get('formatters', {}).get('keys')
    if keys:
        if isinstance(keys, basestring):
            keys = [keys]
        formatters.extend(keys)

    # Merge the application configuration to the default configuration
    log_conf = configobj.ConfigObj(log_conf, interpolation=False)
    app_default_conf.merge(log_conf)

    # Merge the resulting configuration to the global configuration
    apps_log_conf.merge(app_default_conf)


def activate():
    """Use the merging of all the logging configurations to configure the Python logging system
    """
    logging.addLevelName(10000, 'NONE')

    apps_log_conf['loggers']['keys'] = ','.join(set(loggers))
    apps_log_conf['handlers']['keys'] = ','.join(set(handlers))
    apps_log_conf['formatters']['keys'] = ','.join(set(formatters))

    log_conf = StringIO.StringIO('\n'.join(apps_log_conf.write()))
    logging.config.fileConfig(log_conf)
