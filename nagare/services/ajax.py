# --
# Copyright (c) 2008-2020 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import os

from nagare.services import plugin

AJAX_PREFIX = '/static/nagare'


class AjaxService(plugin.Plugin):
    LOAD_PRIORITY = 120
    CONFIG_SPEC = {'directory': 'string(default=None)'}

    def __init__(self, name, dist, directory, statics_service):
        super(AjaxService, self).__init__(name, dist)

        location = directory or os.path.join(dist.location, 'nagare', 'static')
        statics_service.register_dir(AJAX_PREFIX, location)
