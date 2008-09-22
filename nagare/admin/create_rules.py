#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``create-rules`` administrative command

Generate the rewrite rules for the `lighttpd <http://www.lighttpd.net/>`_ and
`nginx <http://nginx.net/>`_ http server, to let them serve the static contents
of the launched applications instead of the applications themself.
"""

import os, pkg_resources
from nagare.admin import util

def set_options(optparser):
    """Register the possible options
    
    They are:
    
      - ``-l`` or ``--lighttpd`` to generate the lighttpd rules (default)
      - ``-n`` or ``--nginx`` to generate the nginx rules
      
    In:
      - ``optparser`` -- the options parser
    """
    optparser.usage += ' [applications ...]'

    optparser.add_option('-l', '--lighttpd', action='store_const', const='l', dest='server', help='generate lighttpd rules', default='l')
    optparser.add_option('-n', '--nginx', action='store_const', const='n', dest='server', help='generate nginx rules')

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
    
    apps = [('nagare', static)]   # Initialise the result tuple with the static contents of the framework
    
    for app_name in app_names:
        (cfgfile, app, dist, aconf) = util.read_application(app_name, error)
    
        static = aconf['application'].get('static', os.path.join(dist.location, 'static'))
    
        if static and not os.path.isdir(static):
            static = None
    
        apps.append((app_name, static))
    
    return sorted(apps, key=lambda x: len(x[0]))

def generate_lighttpd_rules(app_names, error):
    """Generate the lighttpd rewrite rules for the given registered applications
    
    In:
      - ``app_names`` -- list of the applications, read from the command line
      - ``error`` -- the function to call in case of configuration errors
      
    Return:
      - yield the lighttpd configuration file fragment
    """    
    apps = create_rules(app_names, error)
    document_root = os.path.commonprefix([static for (name, static) in apps])
    
    yield 'server.document-root = "%s"' % document_root
    yield ''
    
    yield 'url.rewrite = ('
    for (app_name, static) in apps:
        yield '  "^/static/%s/(.*)" => "%s/$1",' % (app_name, static[len(document_root):])
    
    yield '  "^(.*)" => "/fcgi/$1"'
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

def run(parser, options, args):
    if options.server == 'l':
        print '\n'.join(generate_lighttpd_rules(args, parser.error))
    
    if options.server == 'n':
        print '\n'.join(generate_nginx_rules(args, parser.error))

# ---------------------------------------------------------------------------

class CreateRules(util.Command):
    desc = 'Create the rewrite rules'

    set_options = staticmethod(set_options)
    run = staticmethod(run)
