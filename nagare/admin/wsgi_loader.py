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
from nagare.admin import util, serve


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


def init_publisher(conf_path, conf):
    # Create the function to get the static contents of the application
    nagare_req = pkg_resources.Requirement.parse('nagare')

    publishers = dict([(entry.name, entry) for entry in pkg_resources.iter_entry_points('nagare.publishers')])
    t = conf['publisher'].get('type', 'standalone')
    publisher = publishers[t].load()()

    get_file = None
    static_path = conf['application']['static']
    if static_path is not None and os.path.isdir(static_path):
        get_file = lambda path, static_path=static_path: serve.get_file_from_root(static_path, path)

    # Register the function to serve the static contents of the application
    static_url = publisher.register_static(conf['application']['name'], get_file)
    publisher.register_static('nagare', lambda path, r=nagare_req: serve.get_file_from_package(r, path))
    return publisher, static_url


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
    publisher, static_url = init_publisher(NAGARE_SETTINGS, config)
    init_logs(NAGARE_SETTINGS, config)

    project_name = config['application']['name']
    requirement = pkg_resources.Requirement.parse(project_name)
    data_path = pkg_resources.resource_filename(requirement, '/data')

    (app, metadatas) = util.activate_WSGIApp(app, NAGARE_SETTINGS, config, error,
                                             project_name=project_name,
                                             static_path=project_name,
                                             static_url=static_url,
                                             data_path=data_path,
                                             publisher=publisher,
                                             sessions_manager=sessions_manager,
                                             debug=config['application']['debug'])
    init_local()
    return app


