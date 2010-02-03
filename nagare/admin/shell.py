#--
# Copyright (c) 2008, 2009, 2010 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``shell`` and ``batch`` administrative commands

The ``shell`` command launches an interactive Python shell.
The ``batch`` command execute Python statements from a file.

In both cases:

  - the global variable ``apps`` is a dictionary of application name -> application object
  - the global variable ``session`` is the database session
  - the metadata of the applications are activated
"""

import sys, os, code, atexit, __builtin__

from nagare import database, log
from nagare.admin import util

def create_globals(cfgfiles, debug, error):
    """
    In:
      - ``cfgfile`` -- paths to application configuration files or names of
        registered applications
      - ``debug`` -- enable the display of the generated SQL statements
      - ``error`` -- the function to call in case of configuration errors
    """

    configs = []

    # Merge all the ``[logging]]`` section of all the applications
    for cfgfile in cfgfiles:
        # Read the configuration file of the application
        (cfgfile, app, dist, aconf) = util.read_application(cfgfile, error)
        configs.append((cfgfile, app, dist, aconf))

        log.configure(aconf['logging'].dict(), aconf['application']['name'])

    # Configure the logging system
    log.activate()

    apps = {}

    # For each application given, activate its metadata and its logger
    for (cfgfile, app, dist, aconf) in configs:
        name = aconf['application']['name']

        log.set_logger('nagare.application.'+name)

        (apps[name], databases) = util.activate_WSGIApp(app, cfgfile, aconf, error, debug=debug)

        for (database_settings, populate) in databases:
            database.set_metadata(*database_settings)

    session = database.session
    session.begin()
    return dict(session=session, apps=apps)

# -----------------------------------------------------------------------------

def set_shell_options(optparser):
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


def shell(parser, options, args):
    """Launch an interactive shell

    In:
      - ``parser`` -- the optparse.OptParser object used to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines

    The arguments are a list of names of registered applications
    or paths to applications configuration files.
    """
    ns = create_globals(args, options.debug, parser.error)
    ns['__name__'] = '__console__'

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

    set_options = staticmethod(set_shell_options)
    run = staticmethod(shell)

# -----------------------------------------------------------------------------

def set_batch_options(optparser):
    optparser.usage += ' <application> <file.py>'

    optparser.add_option('-d', '--debug', action='store_const', const=True, default=False, dest='debug', help='debug mode for the database engine')

    if not sys.argv[3:]:
        return None

    for (i, option) in enumerate(sys.argv[3:]):
        if not option.startswith('-'):
            break

    return sys.argv[:i+4]

def batch(parser, options, args):
    """Execute Python statements from files

    In:
      - ``parser`` -- the optparse.OptParser object used to parse the configuration file
      - ``options`` -- options in the command lines
      - ``args`` -- arguments in the command lines

    The arguments are the name of a registered applications, or the path to
    an applications configuration file, followed by the paths of a file to
    execute
    """
    if len(args)==0:
        parser.error('No application given')

    if len(args)==1:
        parser.error('No file given')

    for (i, option) in enumerate(sys.argv[3:]):
        if not option.startswith('-'):
            break

    del sys.argv[:i+3]

    ns = create_globals(args[:1], options.debug, parser.error)
    __builtin__.__dict__.update(ns)

    util.load_file(args[1], None)

class Batch(util.Command):
    desc = 'Execute Python statements from a file'

    set_options = staticmethod(set_batch_options)
    run = staticmethod(batch)
