# --
# Copyright (c) 2008-2023 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""A ``Continuation()`` object captures an execution context.

Calling ``switch()`` on a continuation permutes the current execution context
and the captured one, thus resuming where the context was captured.
"""

import sys
import warnings
from traceback import walk_tb

Tasklet = None


class ContinuationException(Exception):
    pass


class ContinuationSuspended(ContinuationException):
    pass


class ContinuationUnreacheableLine(ContinuationException):
    pass


try:
    import stackless
except ImportError:
    # CPython
    # -------

    has_continuation = sys.version_info >= (3, 10)  # PEP626 needed
    if has_continuation:
        warnings.filterwarnings('ignore', 'assigning None to ([0-9]+ )?unbound local', RuntimeWarning)

        class _Continuation:
            def __init__(self):
                self.f = self.args = self.kw = self.frames = self.r = None
                self.i = 0

            def populate(self, f, args, kw, frames):
                self.f = f
                self.args = args
                self.kw = kw
                self.frames = frames

            def _call_tracer(self, *args):
                return self._line_tracer

            def _line_tracer(self, frame, *args):
                code_id, lineno, locals = self.frames[self.i]
                if hash(frame.f_code) != code_id:
                    return self._line_tracer

                self.i += 1
                if self.i == len(self.frames):
                    lineno += 1
                    locals['r'] = self.r
                    sys.settrace(None)

                frame.f_locals.update(locals)

                try:
                    frame.f_lineno = lineno
                except ValueError:
                    raise ContinuationUnreacheableLine(
                        "Unreachable line {} in function '{}' of '{}'".format(
                            lineno, frame.f_code.co_name, frame.f_code.co_filename
                        )
                    )

            def resume(self, continuation_return=None):
                self.i = 0
                self.r = continuation_return
                sys.settrace(self._call_tracer)

                return Continuation(self.f, *self.args, **self.kw)

            def switch(self, *args):
                r = None

                if args:
                    return self.resume(args[0])

                raise ContinuationSuspended(self)
                return r

        get_current = _Continuation

        def Continuation(f, *args, **kw):
            try:
                return f(*args, **kw)
            except ContinuationSuspended as e:
                continuation = e.args[0]
                continuation.populate(
                    f,
                    args,
                    kw,
                    [(hash(frame.f_code), lineno, frame.f_locals) for frame, lineno in walk_tb(e.__traceback__)][1:-1],
                )
                return continuation
    else:

        def Continuation(f, *args, **kw):
            return f(*args, **kw)

        def get_current(*args, **kw):
            raise NotImplementedError('CPython>=3.10 or Stackless Python needed')

else:
    # Stackless Python
    # ----------------

    has_continuation = True
    Tasklet = stackless.tasklet

    def get_current():
        """Return the current execution context."""
        return Channel()

    def Continuation(f, *args, **kw):
        """Create a new execution context where ``f`` is launched.

        This new execution context became the current one.

        In:
            - ``f`` -- function to call
            - ``args``, ``kw`` -- ``f`` arguments
        """
        stackless.tasklet(f)(*args, **kw).run()

    class Channel(stackless.channel):
        def switch(self, value=None):
            # Permute this execution context with the current one

            # In:
            #   - ``value`` - value returned to the captured execution context
            #
            # .. note:
            #   - the code of this function will be serialized.
            #     Keep it to a minimal (no docstring ...)
            if self.balance:
                self.send((stackless.getcurrent(), value))
            else:
                sender, r = self.receive()
                if not sender.is_main:
                    sender.kill()

                return r


def call_wrapper(action, *args, **kw):
    """A wrapper that creates a continuation and calls a function.

    It's necessary to wrapper a callable that do directly or indirectly a
    ``comp.call(o)`` into such a ``call_wrapper``.

    .. note::
        The actions your registered on the ``<a>`` tags or on the submit buttons
        are already wrapped for you.

    In:
      - ``action`` -- a callable. It will be called, wrapped into a new continuation,
        with the ``args`` and ``kw`` parameters.
      - ``args`` -- positional parameters of the callable
      - ``kw`` -- keywords parameters of the callable
    """
    Continuation(action, *args, **kw)
