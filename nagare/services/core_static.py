# --
# Copyright (c) 2008-2021 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import os

from nagare.services import plugin


class CoreStaticService(plugin.Plugin):
    LOAD_PRIORITY = 120
    CONFIG_SPEC = dict(plugin.Plugin.CONFIG_SPEC, directory='string(default=None)')

    def __init__(self, name, dist, directory, statics_service):
        super(CoreStaticService, self).__init__(name, dist, directory=directory)
        self.directory = directory or os.path.join(dist.location, 'nagare', 'static')

    def handle_start(self, app, statics_service):
        statics_service.register_dir(app.static_url + '/nagare', self.directory, gzip=True)
