#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import stackless

Tasklet = stackless.tasklet


def getcurrent():
    return Channel()


def Continuation(f, *args, **kw):
    stackless.tasklet(f)(*args, **kw).run()


class Channel(stackless.channel):
    def switch(self, value=None):
        if self.balance:
            self.send(value)
        else:
            return self.receive()
