# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""The ``shell`` and ``batch`` administrative commands

The ``shell`` command launches an interactive Python shell.
The ``batch`` command execute Python statements from a file.

In both cases:

  - the global variable ``apps`` is a dictionary of application name -> application object
  - the global variable ``session`` is the database session
  - the metadata of the applications are activated
"""

import __builtin__
import sys
import os
import code
import pkg_resources

from nagare import database, log, local
from nagare.admin import util, reference, command


def activate_applications(cfgfiles, debug, error):
    """Initialize applications

    In:
      - ``cfgfile`` -- paths to application configuration files or names of
        registered applications
      - ``debug`` -- enable the display of the generated SQL statements
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - database session
      - {application name -> application object}
    """
    # Configure the local service
    local.worker = local.Process()
    local.request = local.Process()

    configs = []

    # Merge all the ``[logging]]`` section of all the applications
    for cfgfile in cfgfiles:
        # Read the configuration file of the application
        conffile, app, project_name, aconf = util.read_application(cfgfile, error)
        if conffile is None:
            error('Configuration file "%s" not found' % cfgfile)
        configs.append((conffile, app, project_name, aconf))

        log.configure(aconf['logging'].dict(), aconf['application']['app'])

    # Configure the logging service
    log.activate()

    apps = {}

    # For each application given, activate its metadata and its logger
    for cfgfile, app, project_name, aconf in configs:
        name = aconf['application']['app']

        log.set_logger('nagare.application.' + name)

        data_path = aconf['application']['data']

        apps[name], databases = util.activate_WSGIApp(app, cfgfile, aconf, error, data_path=data_path, debug=debug)

        for database_settings, populate in databases:
            database.set_metadata(*database_settings)

    session = database.session
    session.begin()
    return session, apps


def activate_application(cfgfile, debug, error):
    """Initialize one application

    In:
      - ``cfgfile`` -- path to an application configuration file or name of
        a registered application
      - ``debug`` -- enable the display of the generated SQL statements
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - database session
      - application name
      - application object
    """
    session, apps = activate_applications([cfgfile], debug, error)
    return (session,) + apps.items()[0]


def create_globals(cfgfiles, debug, error):
    """Return a namespace with the initialized applications

    In:
      - ``cfgfile`` -- paths to application configuration files or names of
        registered applications
      - ``debug`` -- enable the display of the generated SQL statements
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - the namespace with the ``apps`` and ``session`` variables defined
    """
    session, apps = activate_applications(cfgfiles, debug, error)
    return {'session': session, 'apps': apps}


# -----------------------------------------------------------------------------

def set_shell_options(optparser):
    optparser.usage += ' [application ...]'

    optparser.add_option('-d', '--debug', action='store_const', const=True, default=False, dest='debug', help='debug mode for the database engine')
    optparser.add_option('--plain', action='store_const', const=False, default=True, dest='ipython', help='launch a plain Python interpreter instead of PtPython/BPython/IPython')


class IPythonShellV1(object):
    """A IPython < 0.11 interpreter
    """
    def __init__(self, ipython, banner, prompt, ns):
        """Initialisation

        In:
          - ``ipython`` -- the ``IPython`` module
          - ``banner`` -- banner to display
          - ``prompt`` -- name of the activated application
          - ``ns`` -- the namespace with the ``apps`` and ``session`` variables defined
        """
        self.shell = ipython.Shell.IPShell(argv=['--prompt_in1=Nagare%s [\\#]: ' % prompt], user_ns=ns)
        self.banner = banner

    def __call__(self):
        """Launch the interpreter
        """
        self.shell.mainloop(1, self.banner)


class IPythonShellV2(object):
    """A IPython >= 0.11 interpreter
    """
    def __init__(self, ipython, banner, prompt, ns):
        """Initialisation

        In:
          - ``ipython`` -- the ``IPython`` module
          - ``banner`` -- banner to display
          - ``prompt`` -- name of the activated application
          - ``ns`` -- the namespace with the ``apps`` and ``session`` variables defined
        """
        config = ipython.config.loader.Config()
        config.PromptManager.in_template = 'Nagare%s [\\#]: ' % prompt

        self.shell = getattr(ipython, 'frontend', ipython).terminal.embed.InteractiveShellEmbed(config=config, user_ns=ns, banner1=banner)
        self.shell.confirm_exit = False

    def __call__(self):
        """Launch the interpreter
        """
        self.shell()


class IPythonShellV3(object):
    """A IPython >= 5.0 interpreter
    """
    def __init__(self, ipython, banner, prompt, ns):

        class NagarePrompts(ipython.terminal.prompts.Prompts):
            def in_prompt_tokens(self, cli=None):
                return [
                    (ipython.terminal.prompts.Token.Prompt, 'Nagare%s [' % prompt),
                    (ipython.terminal.prompts.Token.PromptNum, str(self.shell.execution_count)),
                    (ipython.terminal.prompts.Token.Prompt, ']: '),
                ]

        self.shell = ipython.terminal.embed.InteractiveShellEmbed(banner1=banner, user_ns=ns, confirm_exit=False)
        self.shell.prompts = NagarePrompts(self.shell)

    def __call__(self):
        self.shell()


class PythonShell(code.InteractiveConsole):
    """A plain Python interpreter
    """
    def __init__(self, banner, prompt, ns):
        """Initialisation

        In:
          - ``banner`` -- banner to display
          - ``prompt`` -- name of the activated application
          - ``ns`` -- the namespace with the ``apps`` and ``session`` variables defined
        """
        code.InteractiveConsole.__init__(self, ns)
        self.banner = banner
        self.prompt = prompt

    def raw_input(self, prompt):
        return code.InteractiveConsole.raw_input(self, 'Nagare' + self.prompt + prompt)

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
        readline.parse_and_bind('tab: complete')

        history_path = os.path.expanduser('~/.nagarehistory')

        if os.path.exists(history_path):
            readline.read_history_file(history_path)

        readline.set_history_length(200)

        PythonShell.__call__(self)

        readline.write_history_file(history_path)


def create_python_shell(ipython, banner, prompt, ns):
    """Shell factory

    Create a shell according to the installed modules (``readline`` and ``ipython``)

    In:
      - ``ipython`` -- does the user want a IPython shell?
      - ``banner`` -- banner to display
      - ``prompt`` -- name of the activated application
      - ``ns`` -- the namespace with the ``apps`` and ``session`` variables defined
    """
    if ipython:
        try:
            from ptpython import repl, prompt_style
        except ImportError:
            pass
        else:
            def configure(repl):
                class NagarePrompt(prompt_style.ClassicPrompt):
                    def in_tokens(self, cli):
                        return [(prompt_style.Token.Prompt, 'Nagare%s>>> ' % prompt)]

                repl.all_prompt_styles['nagare'] = NagarePrompt()
                repl.prompt_style = 'nagare'

            print banner

            repl.embed(
                globals(), ns,
                history_filename=os.path.expanduser('~/.nagarehistory'),
                configure=configure
            )
            return

        try:
            from bpython import curtsies, embed
        except ImportError:
            pass
        else:
            class FullCurtsiesRepl(curtsies.FullCurtsiesRepl):
                def __init__(self, config, *args, **kw):
                    config.hist_file = os.path.expanduser('~/.nagarehistory')
                    super(FullCurtsiesRepl, self).__init__(config, *args, **kw)

                @property
                def ps1(self):
                    return 'Nagare' + prompt + super(FullCurtsiesRepl, self).ps1

            curtsies.FullCurtsiesRepl = FullCurtsiesRepl

            embed(ns, banner=banner)
            return

        try:
            import IPython
        except ImportError:
            pass
        else:
            ipython_version = pkg_resources.parse_version(IPython.__version__)
            if ipython_version < pkg_resources.parse_version('0.11'):
                shell_factory = IPythonShellV1
            elif ipython_version < pkg_resources.parse_version('5.0'):
                import IPython.config
                shell_factory = IPythonShellV2
            else:
                shell_factory = IPythonShellV3

            shell_factory(IPython, banner, prompt, ns)()
            return

    try:
        import readline

        PythonShellWithHistory(banner, prompt, ns)(readline)
    except ImportError:
        PythonShell(banner, prompt, ns)()


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

    banner = "Python %s on %s\nNagare %s\n\nVariables 'apps' and 'session' are available" % (
        sys.version,
        sys.platform,
        pkg_resources.get_distribution('nagare').version
    )

    apps = ns['apps'].values()

    create_python_shell(
        options.ipython,
        banner,
        '[%s]' % apps[0].name if len(apps) == 1 else '',
        ns
    )


class Shell(command.Command):
    desc = 'Launch a shell'

    set_options = staticmethod(set_shell_options)
    run = staticmethod(shell)


# -----------------------------------------------------------------------------

def set_batch_options(optparser):
    optparser.usage += ' <application> <file.py>'

    optparser.add_option('-d', '--debug', action='store_const', const=True, default=False, dest='debug', help='debug mode for the database engine')

    if not sys.argv[3:]:
        return None

    for i, option in enumerate(sys.argv[3:]):
        if not option.startswith('-'):
            break

    return sys.argv[:i + 4]


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
    if not args:
        parser.error('No application given')

    if len(args) == 1:
        parser.error('No file given')

    for i, option in enumerate(sys.argv[3:]):
        if not option.startswith('-'):
            break

    del sys.argv[:i + 3]

    ns = create_globals(args[:1], options.debug, parser.error)
    __builtin__.__dict__.update(ns)

    reference.load_file(args[1], None)


class Batch(command.Command):
    desc = 'Execute Python statements from a file'

    set_options = staticmethod(set_batch_options)
    run = staticmethod(batch)
