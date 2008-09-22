#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The ``create`` administrative command

Generate the directory structure and the skeleton of an application.
"""

from __future__ import with_statement

import sys, os
import textwrap

from nagare.admin import util

def set_options(optparser):
    optparser.usage += ' application'


def create_empty_file(path, name):
    f = open(os.path.join(path, name), 'w')
    f.close()


def run(parser, options, args):
    if len(args) == 0:
        parser.error('an application name must be provide')

    if len(args) > 1:
        parser.error('only one application name must be provide')

    root = args[0]
    app_name = os.path.basename(root)
    app_id = app_name.replace('-', '_')

    if os.path.exists(root):
        parser.error("the directory '%s' already exists" % root)
    os.mkdir(root)

    params = {
        'exe' : sys.executable,
        'root' : root,
        'setup' : os.path.join(root, 'setup.py'),
        'name' : app_name,
        'id' : app_id,
        'Id' : app_id.capitalize()
    }

    with open(os.path.join(root, 'setup.py'), 'w') as f:
        f.write(textwrap.dedent('''\
            VERSION = '0.0.1'

            from setuptools import setup, find_packages

            setup(
                  name = '%(name)s',
                  version = VERSION,
                  author = '',
                  author_email = '',
                  description = '',
                  license = '',
                  keywords = '',
                  url = '',
                  packages = find_packages(),
                  include_package_data = True,
                  package_data = {'' : ['*.cfg']},
                  zip_safe = False,
                  install_requires = ('nagare',),
                  entry_points = """
                  [nagare.applications]
                  %(id)s = %(id)s.%(id)s:app
                  """
                 )
        ''' % params))

    os.mkdir(os.path.join(root, app_id))

    create_empty_file(os.path.join(root, app_id), '__init__.py')

    with open(os.path.join(root, app_id, app_id+'.py'), 'w') as f:
        f.write(textwrap.dedent('''\
            from __future__ import with_statement

            import os
            from nagare import presentation

            class %(Id)s(object):
                pass

            @presentation.render_for(%(Id)s)
            def render(self, h, *args):
                this_file = __file__
                if this_file.endswith('.pyc'):
                    this_file = __file__[:-1]

                models_file = os.path.join(os.path.dirname(__file__), 'models.py')

                h.head.css_url('/static/nagare/application.css')
                h.head << h.head.title('Up and Running !')

                with h.div(class_='mybody'):
                    with h.div(id='myheader'):
                        h << h.a(h.img(src='/static/nagare/img/logo.gif'), id='logo', href='http://www.nagare.org/', title='Nagare home')
                        h << h.span('Congratulations !', id='title')

                    with h.div(id='main'):
                        h << h.h1('Your application is running')

                        with h.p:
                            h << 'You can now:'
                            with h.ul:
                                h << h.li('If your application uses a database, add your database entities into ', h.i(models_file))
                                h << h.li('Add your application components into ', h.i(this_file), ' or create new files')

                        h << h.p('To lean more, go to the ', h.a('official website', href='http://www.nagare.org/'))

                        h << "Have fun !"

                h << h.div(class_='footer')

                return h.root

            # ---------------------------------------------------------------

            app = %(Id)s
        ''' % params))

    with open(os.path.join(root, app_id, 'models.py'), 'w') as f:
        f.write(textwrap.dedent('''\
            from elixir import *
            from sqlalchemy import MetaData

            __metadata__ = MetaData()
        '''))

    os.mkdir(os.path.join(root, 'static'))
    create_empty_file(os.path.join(root, 'static'), '__init__.py')

    os.mkdir(os.path.join(root, 'data'))
    create_empty_file(os.path.join(root, 'data'), '__init__.py')

    os.mkdir(os.path.join(root, 'conf'))
    create_empty_file(os.path.join(root, 'conf'), '__init__.py')

    with open(os.path.join(root, 'conf', app_id+'.cfg'), 'w') as f:
        f.write(textwrap.dedent('''\
            [application]
            path = app %(id)s
            name = %(id)s
            debug = off

            [database]
            activated = off
            uri = sqlite:///$here/../data/%(id)s.db
            metadata = %(id)s.models:__metadata__
            debug = off
        ''' % params))

    print "Application '%s' created." % app_name
    print
    print textwrap.dedent("""\
        Note:
          1. Edit the file '%(setup)s' to set the informations about your new application.
          2. Register your application with:
               - cd "%(root)s"
               - "%(exe)s" setup.py develop
        """ % params)


class Create(util.Command):
    desc = 'Create an application skeleton'

    set_options = staticmethod(set_options)
    run = staticmethod(run)
