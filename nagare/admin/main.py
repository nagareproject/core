#--
# Copyright (c) 2008, 2009, 2010 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``nagare-admin`` executable

The ``main()`` function is called by the ``nagare-admin`` console script, created
by  ``setuptools``
"""

import sys, os
import optparse

import configobj
import pkg_resources

from nagare.admin import util

def usage(commands):
    """
    Display the usage of ``nagare-admin``

    In:
      - ``commands`` -- list of the classes implementing the commands
    """
    yield '%prog <command>'
    yield ''
    yield 'with <command> :'

    # Display the description of each command
    l = max(map(len, commands))
    for name in sorted(commands):
        yield ' - %s: %s' % (name.ljust(l), commands[name].desc)

# ---------------------------------------------------------------------------

def main():
    """Dispatcher for the ``nagare-admin`` commands

    The commands are classed, registered under the ``nagare.commands`` entry point
    """

    # Load all the commands
    commands = {}
    for entry_point in pkg_resources.iter_entry_points('nagare.commands'):
        try:
            commands[entry_point.name] = entry_point.load()
        except ImportError:
            print "Warning: the command '%s' can't be imported" % entry_point.name
            raise

    parser = optparse.OptionParser(usage='\n'.join(usage(commands)))

    if (len(sys.argv) == 1) or (sys.argv[1] == '-h') or (sys.argv[1] == '--help'):
        parser.print_usage(sys.stderr)
        parser.exit()

    command_name = sys.argv[1]
    command = commands.get(command_name)
    if command is None:
        parser.error("command '%s' not found" % command_name)

    parser.usage = '%%prog %s [options]' % command_name

    argv = command.set_options(parser) # Let the command register its command line options
    (options, args) = parser.parse_args((argv if argv is not None else sys.argv)[2:])   # Parse the command line

    command.run(parser, options, args)  # Run the command
