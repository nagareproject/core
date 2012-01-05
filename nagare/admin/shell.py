#--
# Copyright (c) 2008-2012 Net-ng.
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

import sys, os, code, __builtin__
import pkg_resources

from nagare import database, log, local
from nagare.admin import util

def create_globals(cfgfiles, debug, error):
    """
    In:
      - ``cfgfile`` -- paths to application configuration files or names of
        registered applications
      - ``debug`` -- enable the display of the generated SQL statements
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - the namespace with the ``apps`` and ``session`` variables defined
    """
    # Configure the local service
    local.worker = local.Process()
    local.request = local.Process()

    configs = []

    # Merge all the ``[logging]]`` section of all the applications
    for cfgfile in cfgfiles:
        # Read the configuration file of the application
        (cfgfile, app, dist, aconf) = util.read_application(cfgfile, error)
        configs.append((cfgfile, app, dist, aconf))

        log.configure(aconf['logging'].dict(), aconf['application']['name'])

    # Configure the logging service
    log.activate()

    apps = {}

    # For each application given, activate its metadata and its logger
    for (cfgfile, app, dist, aconf) in configs:
        name = aconf['application']['name']

        log.set_logger('nagare.application.'+name)

        requirement = None if not dist else pkg_resources.Requirement.parse(dist.project_name)
        data_path = None if not requirement else pkg_resources.resource_filename(requirement, '/data')

        (apps[name], databases) = util.activate_WSGIApp(app, cfgfile, aconf, error, data_path=data_path, debug=debug)

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


class IPythonShellV1(object):
    """A IPython < 0.11 interpreter
    """
    def __init__(self, ipython, banner, app_names, ns):
        """Initialisation

        In:
          - ``ipython`` -- the ``IPython`` module
          - ``banner`` -- banner to display
          - ``app_names`` -- names of the activated applications
          - ``ns`` -- the namespace with the ``apps`` and ``session`` variables defined
        """
        prompt = '[%s]' % app_names[0] if len(app_names) == 1 else ''
        self.shell = ipython.Shell.IPShell(argv=['--prompt_in1=Nagare%s [\\#]: ' % prompt], user_ns=ns)
        self.banner = banner

    def __call__(self):
        """Launch the interpreter
        """
        self.shell.mainloop(1, self.banner)


class IPythonShellV2(object):
    """A IPython >= 0.11 interpreter
    """
    def __init__(self, ipython, banner, app_names, ns):
        """Initialisation

        In:
          - ``ipython`` -- the ``IPython`` module
          - ``banner`` -- banner to display
          - ``app_names`` -- names of the activated applications
          - ``ns`` -- the namespace with the ``apps`` and ``session`` variables defined
        """
        config = ipython.config.loader.Config()
        prompt = '[%s]' % app_names[0] if len(app_names) == 1 else ''
        config.InteractiveShellEmbed.prompt_in1 = 'Nagare%s [\\#]: ' % prompt

        self.shell = ipython.frontend.terminal.embed.InteractiveShellEmbed(config=config, user_ns=ns, banner1=banner)
        self.shell.confirm_exit = False

    def __call__(self):
        """Launch the interpreter
        """
        self.shell()


class PythonShell(code.InteractiveConsole):
    """A plain Python interpreter
    """
    def __init__(self, banner, app_names, ns):
        """Initialisation

        In:
          - ``banner`` -- banner to display
          - ``app_names`` -- names of the activated applications
          - ``ns`` -- the namespace with the ``apps`` and ``session`` variables defined
        """
        code.InteractiveConsole.__init__(self, ns)
        self.banner = banner
        self.prompt = '[%s]' % app_names[0] if len(app_names) == 1 else ''

    def raw_input(self, prompt):
        return code.InteractiveConsole.raw_input(self, 'nagare'+self.prompt+prompt)

    def __call__(self):
        self.interact(self.banner)


class PythonShellWithHistory(PythonShell):
    """A plain Python interpreter with a readline history
    """
    def __call__(self, readline):
        """Launch the interpreter

        In:
          - ``readline`` -- the ``readline`` module
          - ``banner`` -- banner to display
        """
        # Set completion on TAB and a dedicated commands history file
        import rlcompleter

        readline.parse_and_bind('tab: complete')

        history_path = os.path.expanduser('~/.nagarehistory')

        if os.path.exists(history_path):
            readline.read_history_file(history_path)

        readline.set_history_length(200)

        PythonShell.__call__(self)

        readline.write_history_file(history_path)


def create_python_shell(ipython, banner, app_names, ns):
    """Shell factory

    Create a shell according to the installed modules (``readline`` and ``ipython``)

    In:
      - ``ipython`` -- does the user want a IPython shell?
      - ``banner`` -- banner to display
      - ``app_names`` -- names of the activated applications
      - ``ns`` -- the namespace with the ``apps`` and ``session`` variables defined
    """
    if ipython:
        try:
            import IPython
        except ImportError:
            pass
        else:
            shell_factory = IPythonShellV1 if map(int, IPython.__version__.split('.')) < [0, 11] else IPythonShellV2
            shell_factory(IPython, banner, app_names, ns)()
            return

    try:
        import readline

        PythonShellWithHistory(banner, app_names, ns)(readline)
    except ImportError:
        PythonShell(banner, app_names, ns)()


def shell(parser, options, args):
    """Launch an interactive shell

    In:
      - ``parser`` -- the ``optparse.OptParser`` object used to parse the configuration file
      - ``options`` -- options in the command line
      - ``args`` -- arguments in the command line

    The arguments are a list of names of registered applications
    or paths to applications configuration files.
    """
    ns = create_globals(args, options.debug, parser.error)
    ns['__name__'] = '__console__'

    banner = "Python %s on %s\nNagare %s\n\nVariables 'apps' and 'session' are available" % (sys.version,
                sys.platform,
                pkg_resources.get_distribution('nagare').version)

    create_python_shell(options.ipython, banner, [app.name for app in ns['apps'].values()], ns)

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
    """Execute Python statements a file

    In:
      - ``parser`` -- the ``optparse.OptParser`` object used to parse the configuration file
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
