#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``shell`` administrative command

Launch an interactive Python shell where:

  - the global variable ``apps`` is a dictionary of application name -> application object
  - the global variable ``session`` is the database session
  - the metadata of the applications are activated
"""

import sys, os, code, atexit

import configobj

from nagare.admin import util, db
from nagare import database

def set_options(optparser):
    optparser.usage += ' <application>'

    optparser.add_option('-d', '--debug', action='store_const', const=True, default=False, dest='debug', help='debug mode for the database engine')
    optparser.add_option('--plain', action='store_const', const=False, default=True, dest='ipython', help='launch a plain Python interpreter instead of IPython')


def run_ipython_shell(shell, ns):
    """Launch a IPython interpreter

    In:
      - ``shell`` -- a IPython interpreter
      - ``ns`` -- the namespace with the ``apps`` and ``session`` variables defined
    """
    print "Variables 'apps' and 'session' are available"
    shell.IPShell(argv=[], user_ns=ns).mainloop(sys_exit=1)


def run_python_shell(ns):
    """Launch a plain Python interpreter

    In:
      - ``ns`` -- the namespace with the ``apps`` and ``session`` variables defined
    """
    try:
        import readline
    except ImportError:
        pass
    else:
        # If the ``readline`` module exists, set completion on TAB and a
        # dedicated commands history
        import rlcompleter

        readline.parse_and_bind("tab: complete")

        history_path = os.path.expanduser("~/.nagarehistory")

        if os.path.exists(history_path):
            readline.read_history_file(history_path)

        readline.set_history_length(200)
        atexit.register(lambda: readline.write_history_file(history_path))

    sys.ps1 = 'nagare>>> '
    interpreter = code.InteractiveConsole(ns)
    interpreter.interact("Python %s on %s\nVariables 'apps' and 'session' are available" % (sys.version, sys.platform))


def run(parser, options, args):
    """Launch an interactive shell

    In:
      - ``parser`` -- the optparse.OptParser object used to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines

    The arguments are a list of names of registered applications
    or paths to applications configuration files.
    """
    apps = {}

    # For each application given, activate its metadata
    for cfgfile in args:
        (cfgfile, app, dist, aconf) = util.read_application(cfgfile, parser.error)

        apps[aconf['application']['name']] = app

        for (section, content) in aconf['database'].items():
            if isinstance(content, configobj.Section):
                db.set_metadata(content, options.debug)
                del aconf['database'][section]

        db.set_metadata(aconf['database'], options.debug)

    ns = dict(
              session=database.session,
              apps=apps,
              __name__='__console__'
                 )

    try:
        import IPython
        ipython_available = True
    except ImportError:
        ipython_available = False

    if ipython_available and options.ipython:
        run_ipython_shell(IPython.Shell, ns)
    else:
        run_python_shell(ns)


class Shell(util.Command):
    desc = 'Launch a shell'

    set_options = staticmethod(set_options)
    run = staticmethod(run)
