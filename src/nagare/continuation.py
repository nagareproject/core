# --
# Copyright (c) 2014-2026 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""A ``Continuation()`` object captures a delimited execution context.

See: https://en.wikipedia.org/wiki/Delimited_continuation
"""

import sys
import warnings
from hashlib import sha256
from functools import partial
from traceback import walk_tb

warnings.filterwarnings('ignore', 'assigning None to ([0-9]+ )?unbound local', RuntimeWarning)


class ContinuationException(Exception):
    pass


class ContinuationSuspended(ContinuationException):
    pass


class ContinuationUnreacheableLine(ContinuationException):
    pass


class ContinuationCodeBlockNotFound(ContinuationException):
    pass


class Continuation:
    def __init__(self):
        self.populate(None, None, None, [])

    def populate(self, f, args, kw, frames):
        self.f = f
        self.args = args
        self.kw = kw
        self.frames = [(self.frame_hash(frame), lineno, dict(frame.f_locals)) for frame, lineno in frames]

    @staticmethod
    def frame_hash(frame):
        code = frame.f_code
        return sha256(code.co_filename.encode('utf-8') + str(code.co_firstlineno).encode('utf-8')).digest()[:8]

    @staticmethod
    def _stop(frame, event, arg):
        return None

    @classmethod
    def _jump(cls, lineno, frame, event, arg):
        try:
            frame.f_lineno = lineno
        except ValueError:
            raise ContinuationUnreacheableLine(
                f"Unreachable line {lineno} in function '{frame.f_code.co_name}' of '{frame.f_code.co_filename}'"
            )

        return cls._stop

    def _enter_function(self, frame, event, arg):
        f_hash, lineno, locals_ = self.frames[self.current_frame]
        if self.frame_hash(frame) != f_hash:
            return None

        self.current_frame += 1
        if self.current_frame == len(self.frames):
            lineno += 1

        frame.f_locals.update(locals_)

        return partial(self._jump, lineno)

    def resume(self, return_value=None):
        self.current_frame = 0
        self.return_value = return_value

        sys.settrace(self._enter_function)

        try:
            r = delimit(self.f, *self.args, **self.kw)
            if not self.current_frame == len(self.frames):
                raise ContinuationCodeBlockNotFound()
            return r
        finally:
            sys.settrace(None)

    __call__ = resume

    def _suspend(self):
        raise ContinuationSuspended(self)

    def suspend(self):
        self._suspend()
        sys.settrace(None)

        return self.return_value

    shift = suspend


def delimit(f, *args, **kw):
    try:
        return f(*args, **kw)
    except ContinuationSuspended as e:
        continuation = e.args[0]
        continuation.populate(f, args, kw, list(walk_tb(e.__traceback__))[1:-1])

        return continuation


reset = delimit
