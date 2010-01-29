# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

"""Utiliy module that watches for files modification and exits the current
process when this event happens.

This module is derivated from Ian Bicking's one to only exit if there is no
importation errors into the modified file.
"""

import os, sys, time, threading, traceback
import subprocess

def _turn_sigterm_into_systemexit():
    """
    Attempts to turn a SIGTERM exception into a SystemExit exception.
    """
    try:
        import signal
    except ImportError:
        return

    def handle_term(signo, frame):
        raise SystemExit

    signal.signal(signal.SIGTERM, handle_term)


def _quote_first_command_arg(arg):
    """
    There's a bug in Windows when running an executable that's
    located inside a path with a space in it.  This method handles
    that case, or on non-Windows systems or an executable with no
    spaces, it just leaves well enough alone.
    """
    if (sys.platform != 'win32') or (' ' not in arg):
        # Problem does not apply:
        return arg

    try:
        import win32api
    except ImportError:
        raise ValueError(
            "The executable %r contains a space, and in order to "
            "handle this issue you must have the win32api module "
            "installed" % arg)

    return win32api.GetShortPathName(arg)


def restart_with_monitor():
    while True:
        args = [_quote_first_command_arg(sys.executable)] + sys.argv
        new_environ = os.environ.copy()
        new_environ['nagare_reloaded'] = 'True'

        proc = None
        try:
            try:
                _turn_sigterm_into_systemexit()
                proc = subprocess.Popen(args, env=new_environ)
                exit_code = proc.wait()
                proc = None
            except KeyboardInterrupt:
                print '^C caught in monitor process'
                #if self.verbose > 1:
                #    raise
                return 1
        finally:
            if (proc is not None) and hasattr(os, 'kill'):
                import signal
                try:
                    os.kill(proc.pid, signal.SIGTERM)
                except (OSError, IOError):
                    raise

        if exit_code != 3:
            return exit_code

        print '-'*20, 'Restarting', '-'*20

class Monitor(object):
    def __init__(self, poll_interval, included_files, excluded_directories):
        self.poll_interval = poll_interval
        self.included_files = list(included_files)
        self.excluded_directories = [d + ('' if d.endswith(os.sep) else os.sep) for d in excluded_directories]

        self.mtimes = {}

    def watch_file(self, filename):
        self.included_files.append(filename)

    def periodic_reload(self):
        while not self.check_modifications():
            time.sleep(self.poll_interval)
        os._exit(3)

    def check_modification(self, filename):
        try:
            mtime = os.stat(filename).st_mtime
        except (OSError, IOError):
            return False

        r = (self.mtimes.setdefault(filename, mtime) < mtime)
        self.mtimes[filename] = mtime

        return r

    def check_modifications(self):
        for filename in self.included_files:
            if self.check_modification(filename):
                print >> sys.stderr, 'File %s changed; reloading...' % filename
                return True

        for m in sys.modules.values():
            if not hasattr(m, '__file__'):
                continue

            filename = m.__file__

            for directory in self.excluded_directories:
                if filename.startswith(directory):
                    continue

            if filename.endswith(('.pyc', '.pyo')) and os.path.exists(filename[:-1]):
                filename = filename[:-1]

            if self.check_modification(filename):
                try:
                    reload(m)
                    print >> sys.stderr, 'Module %s changed; reloading...' % filename
                    return True
                except Exception, e:
                    print >> sys.stderr, 'WARNING, module %s NOT reloaded' % filename
                    print >> sys.stderr, traceback.format_exc()

        return False


def install(poll_interval=1, included_files=(), excluded_directories=()):
    mon = Monitor(poll_interval, included_files, excluded_directories)
    t = threading.Thread(target=mon.periodic_reload)
    t.setDaemon(True)
    t.start()
    return mon
