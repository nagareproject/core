#--
# Copyright (c) 2008, Net-ng.
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

import os

import pkg_resources
import configobj

from nagare import database
from nagare.admin import util

def set_metadata(conf, debug):
    """Activate the database metadata object
    
    The location of the metadata object is read from the configuration file
    
    In:
      - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
      - ``debug`` -- debug mode for the database engine
      
    Return:
      - the metadata object
    """
    metadata = conf.get('metadata', '')

    if conf['activated'] and metadata:
        metadata = util.load_object(metadata)[0]
        
        # All the parameters, of the [database] section, with an unknown name are
        # given to the database engine
        engine_conf = dict([(k, v) for (k, v) in conf.items() if k not in ('uri', 'activated', 'metadata', 'debug', 'populate')])
        database.set_metadata(metadata, conf['uri'], debug, **engine_conf)
    
        return metadata


def read_options(parser, options, args):
    """Activate all the database metadata objects of an application
    
    Several metadata objects can be activated if there are sub-sections into
    the [database] section.
    
    In:
      - ``parser`` -- the optparse.OptParser object used to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines : application to activate
      
    Return:
      - yield tuples (metadata object, populate function)
    """
    apps = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.applications')])

    # If no application name is given, display the list of the registered applications
    if len(args) == 0:
        print 'Available applications:'
        for app_name in sorted(apps):
            print ' -', app_name
        return

    if len(args) != 1:
        parser.error('Bad number of parameters')

    # Read the configuration of the application
    (cfgfile, app, dist, aconf) = util.read_application(args[0], parser.error)
    
    for (section, content) in aconf['database'].items():
        if isinstance(content, configobj.Section):
            metadata = set_metadata(content, options.debug)
            if metadata is not None:
                yield (metadata, content['populate'])
            del aconf['database'][section]

    metadata = set_metadata(aconf['database'], options.debug)
    if metadata is not None:
        yield (metadata, aconf['database']['populate'])


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
    for (metadata, populate) in read_options(parser, options, args):
        with database.session.begin():
            if options.drop:
                metadata.drop_all()
            
            metadata.create_all()

            if options.populate and populate:
                util.load_object(populate)[0]()
            

def drop(parser, options, args):
    """Delete the database tables of the application
    
    In:
      - ``parser`` -- the optparse.OptParser object used to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines : application name
    """
    for (metadata, populate) in read_options(parser, options, args):
        with database.session.begin():
            metadata.drop_all()

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
