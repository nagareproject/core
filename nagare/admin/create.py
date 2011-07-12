#--
# Copyright (c) 2008-2011 Net-ng.
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
    open(os.path.join(path, name), 'w').close()


def run(parser, options, args):
    if len(args) == 0:
        parser.error('an application name must be provided')

    if len(args) > 1:
        parser.error('only one application name must be provided')

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
                  message_extractors = { '%(id)s' : [('**.py', 'python', None)] },
                  entry_points = """
                  [nagare.applications]
                  %(id)s = %(id)s.app:app
                  """
                 )
        ''' % params))

    with open(os.path.join(root, 'setup.cfg'), 'w') as f:
        f.write(textwrap.dedent('''\
            [extract_messages]
            keywords = _ , _N:1,2 , _L , _LN:1,2 , gettext , ugettext , ngettext:1,2 , ungettext:1,2 , lazy_gettext , lazy_ugettext , lazy_ngettext:1,2 , lazy_ungettext:1,2
            output_file = data/locale/messages.pot

            [init_catalog]
            input_file = data/locale/messages.pot
            output_dir = data/locale
            domain = messages

            [update_catalog]
            input_file = data/locale/messages.pot
            output_dir = data/locale
            domain = messages

            [compile_catalog]
            directory = data/locale
            domain = messages
        '''))

    with open(os.path.join(root, 'MANIFEST.in'), 'w') as f:
        f.write(textwrap.dedent('''\
            graft conf
            graft static
            graft data/locale
        '''))

    os.mkdir(os.path.join(root, app_id))

    create_empty_file(os.path.join(root, app_id), '__init__.py')

    with open(os.path.join(root, app_id, 'app.py'), 'w') as f:
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

                h.head << h.head.title('Up and Running !')

                h.head.css_url('/static/nagare/application.css')
                h.head.css('defaultapp', '#main { margin-left: 20px; padding-bottom: 100px; background: url(/static/nagare/img/sakura.jpg) no-repeat 123px 100%% }')

                with h.div(id='body'):
                    h << h.a(h.img(src='/static/nagare/img/logo.png'), id='logo', href='http://www.nagare.org/', title='Nagare home')

                    with h.div(id='content'):
                        h << h.div('Congratulations!', id='title')

                        with h.div(id='main'):
                            h << h.h1('Your application is running')

                            h << 'You can now:'
                            with h.ul:
                                h << h.li('If your application uses a database, add your database entities into ', h.em(models_file))
                                h << h.li('Add your application components into ', h.em(this_file), ' or create new files')

                            h << h.em("Have fun!")

                with h.div(id='footer'):
                    with h.table:
                        with h.tr:
                            h << h.th('About Nagare')
                            h << h.th('Community')
                            h << h.th('Learn', class_='last')

                        with h.tr:
                            with h.td:
                                with h.ul:
                                    h << h.li(h.a('Description', href='http://www.nagare.org/trac/wiki/NagareDescription'))
                                    h << h.li(h.a('Features', href='http://www.nagare.org/trac/wiki/NagareFeatures'))
                                    h << h.li(h.a('Who uses Nagare?', href='http://www.nagare.org/trac/wiki/WhoUsesNagare'))
                                    h << h.li(h.a('Licence', href='http://www.nagare.org/trac/wiki/NagareLicence'))

                            with h.td:
                                with h.ul:
                                    h << h.li(h.a('Blogs', href='http://www.nagare.org/trac/blog'))
                                    h << h.li(h.a('Mailing list', href='http://www.nagare.org/trac/wiki/MailingLists'))
                                    h << h.li(h.a('IRC', href='http://www.nagare.org/trac/wiki/IrcChannel'))
                                    h << h.li(h.a('Bug report', href='http://www.nagare.org/trac/wiki/BugReport'))

                            with h.td(class_='last'):
                                with h.ul:
                                    h << h.li(h.a('Documentation', href='http://www.nagare.org/trac/wiki'))
                                    h << h.li(h.a('Demonstrations portal', href='http://www.nagare.org/portal'))
                                    h << h.li(h.a('Demonstrations', href='http://www.nagare.org/demo'))
                                    h << h.li(h.a('Wiki Tutorial', href='http://www.nagare.org/wiki'))

                return h.root

            # ---------------------------------------------------------------

            app = %(Id)s
        ''' % params))

    with open(os.path.join(root, app_id, 'models.py'), 'w') as f:
        f.write(textwrap.dedent('''\
            from elixir import *
            from sqlalchemy import MetaData

            __metadata__ = MetaData()

            # Here, put the definition of your Elixir or SQLAlchemy models
        '''))

    os.mkdir(os.path.join(root, 'static'))
    create_empty_file(os.path.join(root, 'static'), '__init__.py')

    os.mkdir(os.path.join(root, 'data'))
    create_empty_file(os.path.join(root, 'data'), '__init__.py')

    os.mkdir(os.path.join(root, 'data', 'locale'))

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
