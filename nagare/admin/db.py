#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``create-db`` and ``drop-db`` administrative commands

Create or delete the database tables of an application
"""

from __future__ import with_statement

import pkg_resources

from nagare import local, log, database
from nagare.admin import util

def read_options(debug, args, error):
    """Activate all the database metadata objects of an application

    Several metadata objects can be activated if there are sub-sections into
    the [database] section.

    In:
      - ``debug`` -- flag to display the generated SQL statements
      - ``args`` -- arguments in the command lines: application to activate
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - tuples (metadata object, populate function)
   """
    # If no application name is given, display the list of the registered applications
    if len(args) == 0:
        print 'Available applications:'
        app_names = [entry.name for entry in pkg_resources.iter_entry_points('nagare.applications')]
        for app_name in sorted(app_names):
            print ' -', app_name
        return ()

    if len(args) != 1:
        error('Bad number of parameters')

    # Read the configuration of the application
    (cfgfile, app, dist, aconf) = util.read_application(args[0], error)

    # Configure the local service
    local.worker = local.Process()
    local.request = local.Process()

    # Configure the logging service
    log.configure(aconf['logging'].dict(), aconf['application']['name'])
    log.activate()
    log.set_logger('nagare.application.'+ aconf['application']['name'])
    
    return util.activate_WSGIApp(app, cfgfile, aconf, error, debug=debug)[1]


def create(parser, options, args):
    """Create the database tables of the application

    If the ``--drop`` option is on, delete the existing tables before to re-create them

    If the ``--no-populate`` option is off, call the populate function (if it exists)
    after the creation of the tables

    In:
      - ``parser`` -- the optparse.OptParser object used to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines : application name
    """
    for (database_settings, populate) in read_options(options.debug, args, parser.error):
        database.set_metadata(*database_settings)

        with database.session.begin():
            if options.drop:
                database_settings[0].drop_all()

            database_settings[0].create_all()

            if options.populate and populate:
                util.load_object(populate)[0]()


def drop(parser, options, args):
    """Delete the database tables of the application

    In:
      - ``parser`` -- the optparse.OptParser object used to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines : application name
    """
    for (database_settings, populate) in read_options(options.debug, args, parser.error):
        database.set_metadata(*database_settings)

        with database.session.begin():
            database_settings[0].drop_all()

# ---------------------------------------------------------------------------

class DBCreate(util.Command):
    desc = 'Create the database of an application'

    @staticmethod
    def set_options(optparser):
        optparser.usage += ' <application>'

        optparser.add_option('-d', '--debug', action='store_const', const=True, default=False, dest='debug', help='debug mode for the database engine')
        optparser.add_option('--drop', action='store_const', const=True, default=False, dest='drop', help='drop the database tables before to re-create them')
        optparser.add_option('--no-populate', action='store_const', const=False, default=True, dest='populate', help='populate the database tables')

    run = staticmethod(create)


class DBDrop(util.Command):
    desc = 'Drop the database of an application'

    @staticmethod
    def set_options(optparser):
        optparser.usage += ' <application>'

        optparser.add_option('-d', '--debug', action='store_const', const=True, default=False, dest='debug', help='debug mode for the database engine')

    run = staticmethod(drop)
