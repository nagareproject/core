#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``create-rules`` administrative command

Generate the rewrite rules for the `apache <http://httpd.apache.org/>`_,
`lighttpd <http://www.lighttpd.net/>`_ or `nginx <http://nginx.net/>`_ http
servers, to let them serve the static contents of the launched applications,
instead of the applications themselves.
"""

import os, pkg_resources
from nagare.admin import util

def set_options(optparser):
    """Register the possible options

    They are:

      - ``-a`` or ``--apache`` to generate the apache rules (default)
      - ``-l`` or ``--lighttpd`` to generate the lighttpd rules
      - ``-n`` or ``--nginx`` to generate the nginx rules

    In:
      - ``optparser`` -- the options parser
    """
    optparser.usage += ' [applications ...]'

    optparser.add_option('-a', '--apache', action='store_const', const=generate_apache_rules, dest='generate', help='generate apache rules', default=generate_apache_rules)
    optparser.add_option('-l', '--lighttpd', action='store_const', const=generate_lighttpd_rules, dest='generate', help='generate lighttpd rules')
    optparser.add_option('-n', '--nginx', action='store_const', const=generate_nginx_rules, dest='generate', help='generate nginx rules')

def create_rules(app_names, error):
    """Generate the rewrite rules for the given registered applications

    In:
      - ``app_names`` -- list of the applications, read from the command line
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - list of tuples (application, directory of its static contents)
    """
    # If no applications is given on the command line, generate the rules
    # for all the registered applications
    if not app_names:
        app_names = [entry.name for entry in pkg_resources.iter_entry_points('nagare.applications')]

    package = pkg_resources.Requirement.parse('nagare')
    static = pkg_resources.resource_filename(package, 'static')

    apps = [('nagare', static)]   # Initialize the result tuple with the static contents of the framework

    for app_name in app_names:
        (cfgfile, app, dist, aconf) = util.read_application(app_name, error)

        static = aconf['application'].get('static', os.path.join(dist.location, 'static') if dist else None)

        if static and os.path.isdir(static):
            apps.append((aconf['application']['name'], static))

    return sorted(apps, key=lambda x: len(x[0]))

def commonprefix(filenames):
    """Return the common prefix of a list of filenames

    In:
      - ``filenames`` -- the list of filenames

    Return:
      - the common prefix
    """
    filenames = [filename.split(os.sep) for filename in filenames]
    return os.sep.join(os.path.commonprefix(filenames)) or '/'

def generate_lighttpd_rules(app_names, error):
    """Generate the lighttpd rewrite rules for the given registered applications

    In:
      - ``app_names`` -- list of the applications, read from the command line
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - yield the lighttpd configuration file fragment
    """
    apps = create_rules(app_names, error)
    document_root = commonprefix([static for (name, static) in apps])

    yield 'server.document-root = "%s"' % document_root
    yield ''

    yield 'url.rewrite = ('
    for (app_name, static) in apps:
        yield '  "^/static/%s/(.*)" => "%s/$1",' % (app_name, static[len(document_root):])
    yield ')'

def generate_nginx_rules(app_names, error):
    """Generate the nginx rewrite rules for the given registered applications

    In:
      - ``app_names`` -- list of the applications, read from the command line
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - yield the nginx configuration file fragment
    """
    for (app_name, static) in create_rules(app_names, error):
        yield 'location /static/%s/ {' % app_name
        yield '  alias %s/;' % static
        yield '}'
        yield ''

def generate_apache_rules(app_names, error):
    """Generate the apache rewrite rules for the given registered applications

    In:
      - ``app_names`` -- list of the applications, read from the command line
      - ``error`` -- the function to call in case of configuration errors

    Return:
      - yield the apache configuration file fragment
    """
    apps = create_rules(app_names, error)
    document_root = commonprefix([static for (name, static) in apps])

    yield 'DocumentRoot %s' % document_root
    yield ''

    yield 'RewriteEngine On'
    for (app_name, static) in apps:
        yield 'RewriteRule ^/static/%s/(.*)$ %s/$1 [L,PT]' % (app_name, static[len(document_root):])

def run(parser, options, args):
    print '\n'.join(options.generate(args, parser.error))

# ---------------------------------------------------------------------------

class CreateRules(util.Command):
    desc = 'Create the rewrite rules'

    set_options = staticmethod(set_options)
    run = staticmethod(run)
