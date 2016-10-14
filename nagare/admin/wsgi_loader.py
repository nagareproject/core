#--
# Copyright (c) 2008-2016 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import pkg_resources
import os
import sys

from nagare import local, log
from nagare.admin import util


def error(*args, **kw):
    print args, kw


def init_local():
    local.worker = local.Thread()
    local.request = local.Thread()


def init_session_manager(conf_path, conf):
    sessions_managers = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.sessions')])
    pconf = conf['publisher'].copy()
    pconf.update(conf['sessions'])
    t = pconf.pop('type', 'standalone')
    sessions_manager = sessions_managers[t].load()()
    sessions_manager.set_config(conf_path, pconf, error)
    return sessions_manager


def init_logs(conf_path, conf):
    log.configure(conf['logging'].dict(), conf['application']['name'])
    log.activate()


def load(app):
    NAGARE_SETTINGS = os.environ.get('NAGARE_SETTINGS')
    if NAGARE_SETTINGS is None:
        print 'Missing NAGARE_SETTINGS in environment'
        sys.exit(1)

    config = util.read_application_options(NAGARE_SETTINGS, error)

    sessions_manager = init_session_manager(NAGARE_SETTINGS, config)
    init_logs(NAGARE_SETTINGS, config)

    project_name = config['application']['name']
    requirement = pkg_resources.Requirement.parse(project_name)
    data_path = pkg_resources.resource_filename(requirement, '/data')

    (app, metadatas) = util.activate_WSGIApp(app, NAGARE_SETTINGS, config, error,
                                             project_name=project_name,
                                             static_path=project_name,
                                             static_url=project_name,
                                             data_path=data_path,
                                             sessions_manager=sessions_manager,
                                             debug=config['application']['debug'])
    init_local()
    return app


