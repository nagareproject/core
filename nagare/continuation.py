# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""A ``Continuation()`` object captures an execution context

Calling ``switch()`` on a continuation permutes the current execution context
and the captured one, thus resuming where the context was captured.
"""

Tasklet = None

try:
    from _continuation import continulet
except ImportError:
    try:
        import stackless
    except ImportError:
        # CPython
        # -------

        has_continuation = False

        def get_current():
            """Return the current execution context
            """
            return Continuation(lambda: None)

        class Continuation(object):
            """A ``Continuation()`` object launches a function in a new execution context"""

            def __init__(self, f, *args, **kw):
                """Create a new execution context where ``f`` is launched.

                This new execution context became the current one.

                In:
                  - ``f`` -- function to call
                  - ``args``, ``kw`` -- ``f`` arguments
                """
                # CPython: don't create an execution context. Only call the function
                f(*args, **kw)

            def switch(self, value=None):
                """Permute this execution context with the current one

                In:
                  - ``value`` - value returned to the captured execution context
                """
                # No continuation objects in CPython :(
                raise NotImplementedError('Stackless Python or PyPy is needed to create continuations')
    else:
        # Stackless Python
        # ----------------

        has_continuation = True
        Tasklet = stackless.tasklet

        def get_current():
            """Return the current execution context
            """
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
                """Permute this execution context with the current one

                In:
                  - ``value`` - value returned to the captured execution context
                """
                if self.balance:
                    self.send(value)
                else:
                    return self.receive()
else:
    # PyPy
    # ----

    import threading

    has_continuation = True
    _tls = threading.local()

    def get_current():
        """Return the current execution context
        """
        return getattr(_tls, 'current', None)

    def set_current(cont):
        """Set the current execution context
        """
        _tls.current = cont

    class Continuation(continulet):
        """A ``Continuation()`` object launches a function in a new execution context"""

        def __init__(self, f, *args, **kw):
            """Create a new execution context where ``f`` is launched.

            This new execution context became the current one.

            In:
              - ``f`` -- function to call
              - ``args``, ``kw`` -- ``f`` arguments
            """
            super(Continuation, self).__init__(lambda cont: f(*args, **kw))
            self.switch()

        def switch(self, value=None):
            """Permute this execution context with the current one

            In:
              - ``value`` - value returned to the captured execution context
            """
            previous = get_current()
            set_current(self)
            r = super(Continuation, self).switch(value)
            set_current(previous)
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
