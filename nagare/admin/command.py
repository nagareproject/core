# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""The ``nagare-admin`` executable

The ``run()`` function is called by the ``nagare-admin`` console script, created
by  ``setuptools``
"""

import os
import sys
import optparse

import pkg_resources


# ---------------------------------------------------------------------------

class Command(object):
    """The base class of all the commands"""
    desc = ''

    @classmethod
    def set_options(cls, parser):
        """Define the available options for this command

        Out:
          - ``parser`` -- this ``optparse.OptionParser`` will parse the command line
        """
        pass

    @classmethod
    def run(cls, parser, options, args):
        """Command code

        In:
          - ``parser`` -- this ``optparse.OptionParser`` has parsed the command line
          - ``options`` -- the options read on the command line
          - ``args`` -- arguments left on the command line

        Return:
          - the Unix command status
        """
        return 2

    def parse(self, argv, commands):
        """Parse the command line

        In:
          - ``argv`` -- list of the arguments on the command line
          - ``commands`` -- parent commands of this command

        Return:
          - the Unix command status
        """
        parser = optparse.OptionParser(usage=' '.join(commands))
        self.set_options(parser)

        return self.run(parser, *parser.parse_args(argv))

    def get_description(self, commands):
        """Return the description of the command

        In:
          - ``commands`` -- parent commands of this command

        Return:
          - A list with a single tuple (full name of the command, description of the command)
        """
        return [(' '.join(commands), self.desc)]


class Commands(dict):
    """Command with sub-commands"""

    def add_command(self, names, command):
        """Define a sub-commands

        In:
          - ``names`` -- list of names of the sub-command
          - ``command`` -- the sub-command object
        """
        name = names.pop(0)
        if names:
            # The sub-commands has sub-commands itself.
            # Add a new 'Commands()' node if not already registered
            self.setdefault(name, Commands()).add_command(names, command)
        else:
            self[name] = command

    def _usage(self, commands, error):
        """Usage of this command

        In:
          - ``commands`` -- parent commands of this command
          - ``error`` - optional error message

        Return:
          - yield the usage line per line
        """
        yield 'Usage: ' + ' '.join(commands + ('<command>',))
        yield ''
        yield 'with <command>:'

        # Return the description of each sub-commands
        commands = list(self.get_description(()))

        l = max(len(name) for name, _ in commands)
        for name, desc in sorted(commands):
            yield ' - %s: %s' % (name.ljust(l), desc)

        if error:
            yield ''
            yield error

    def usage(self, commands, error=None):
        """Print the usage of this command on ``stderr``

        In:
          - ``commands`` -- parent commands of this command
          - ``error`` - optional error message

        Return:
          - **no return**, interpreter exit
        """
        print >>sys.stderr, '\n'.join(self._usage(commands, error))
        sys.exit(2)

    def parse(self, argv, commands):
        """Parse the command line

        In:
          - ``argv`` -- list of the arguments on the command line
          - ``commands`` -- parent commands of this command

        Return:
          - the Unix command status
        """
        if not argv:
            # No sub-command given on the command line
            self.usage(commands)

        name = argv.pop(0)
        if name not in self:
            # The sub-command given on the command line doesn't exist
            self.usage(commands, "error: command '%s' not found" % name)

        # Parse the command line for the sub-command given
        return self[name].parse(argv, commands + (name,))

    def get_description(self, commands):
        """Return the description of the command

        In:
          - ``commands`` -- parent commands of this command

        Return:
          - A list of tuples (full name of the sub-command, description of the sub-command)
        """
        for name, command in self.items():
            for r in command.get_description(commands + (name,)):
                yield r


# ---------------------------------------------------------------------------

def run(entry_point_section='nagare.commands'):
    """Dispatcher for the ``nagare-admin`` commands

    The commands are classes, registered under the ``entry_point_section`` entry point
    """

    # Load all the commands
    commands = Commands()
    for entry_point in pkg_resources.iter_entry_points(entry_point_section):
        try:
            commands.add_command(entry_point.name.split('.'), entry_point.load()())
        except ImportError:
            print "Warning: the command '%s' can't be imported" % entry_point.name
            raise

    return commands.parse(sys.argv[1:], (os.path.basename(sys.argv[0]),))
