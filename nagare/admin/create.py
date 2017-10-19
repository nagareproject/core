# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""The ``create`` administrative command

Generate the directory structure and the skeleton of an application.
"""

from __future__ import with_statement

import sys
import os
import textwrap
import re
from StringIO import StringIO

from configobj import ConfigObj
from nagare.admin import command


def set_options(optparser):
    optparser.usage += ' <application>'


def create_empty_file(filename):
    open(filename, 'w').close()


def create_or_update(path, create=None, update=None, *args, **kw):
    if not create:
        def create(*args, **kw):
            pass

    if not update:
        def update(*args, **kw):
            pass

    return (update if os.path.exists(path) else create)(path, *args, **kw)


def create_setup_py(filename, params):
    upgrade_setup_py(
        filename,
        params,
        textwrap.dedent('''\
        from setuptools import setup, find_packages

        VERSION = '0.0.1'


        setup(
            name='%(name)s',
            version=VERSION,
            author='',
            author_email='',
            description='',
            license='',
            keywords='',
            url='',
            packages=find_packages(),
            include_package_data=True,
            package_data={'': ['*.cfg']},
            zip_safe=False,
            install_requires=('nagare',),
            entry_points="""
            [nagare.applications]
            %(id)s = %(id)s.app:app
            """
        )''' % params)
    )


def upgrade_setup_py(filename, params, setup_py=None):
    if not setup_py:
        with open(filename, 'r') as f:
            setup_py = f.read()
            if 'message_extractors' in setup_py:
                return

    if os.path.exists(filename):
        os.rename(filename, filename + '.old')

    with open(filename, 'w') as f:
        print >>f, re.sub(r'\n(\s*)(entry_points)', r"\n\1message_extractors={'%(id)s': [('**.py', 'python', None)]},\n\1\2" % params, setup_py)


def upgrade_setup_cfg(filename):
    old_conf = ConfigObj(filename)

    new_conf = ConfigObj(StringIO(textwrap.dedent('''\
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
            ''')), list_values=False)
    new_conf.merge(old_conf)

    if new_conf != old_conf:
        if os.path.exists(filename):
            os.rename(filename, filename + '.old')

        new_conf.filename = filename
        new_conf.write()


def create_manifest_in(filename):
    with open(filename, 'w') as f:
        print >>f, textwrap.dedent('''\
            graft conf
            graft static
            graft data/locale
        ''')


def create_app_py(filename, params):
    with open(filename, 'w') as f:
        f.write(textwrap.dedent("""\
            from __future__ import with_statement

            import os
            from nagare import presentation


            class %(Id)s(object):
                pass


            @presentation.render_for(%(Id)s)
            def render(self, h, *args):
                NAGARE = 'http://www.nagare.org/'
                NAGARE_DOC = NAGARE + 'doc/'

                this_file = __file__
                if this_file.endswith('.pyc'):
                    this_file = __file__[:-1]

                models_file = os.path.join(os.path.dirname(__file__), 'models.py')

                h.head << h.head.title('Up and Running !')

                h.head.css_url('/static/nagare/application.css')
                h.head.css(
                    'defaultapp',
                    '''#main {
                           margin-left: 20px;
                           padding-bottom: 100px;
                           background: url(/static/nagare/img/sakura.jpg) no-repeat 123px 100%%;
                    }'''  # noqa: E501
                )

                with h.div(id='body'):
                    h << h.a(
                        h.img(src='/static/nagare/img/logo.png'),
                        id='logo',
                        href=NAGARE, title='Nagare home'
                    )

                    with h.div(id='content'):
                        h << h.div('Congratulations!', id='title')

                        with h.div(id='main'):
                            h << h.h1('Your application is running')

                            h << 'You can now:'
                            with h.ul:
                                with h.li:
                                    h << 'If your application uses a database, '
                                    h << 'add your database entities into '
                                    h << h.em(models_file)
                                with h.li:
                                    h << 'Add your application components into ',
                                    h << h.em(this_file)
                                    h << ' or create new files'

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
                                    h << h.li(h.a('Description', href=NAGARE_DOC+'description'))  # noqa: E501
                                    h << h.li(h.a('Features', href=NAGARE_DOC+'features'))  # noqa: E501
                                    h << h.li(h.a('License', href=NAGARE_DOC+'license'))  # noqa: E501

                            with h.td:
                                with h.ul:
                                    h << h.li(h.a('Github repositories', href='http://github.com/nagareproject'))  # noqa: E501
                                    h << h.li(h.a('Mailing list', href='http://groups.google.com/group/nagare-users'))  # noqa: E501
                                    h << h.li(h.a('Bugs report', href='https://github.com/nagareproject/core/issues'))  # noqa: E501

                            with h.td(class_='last'):
                                with h.ul:
                                    h << h.li(h.a('Documentation', href=NAGARE_DOC))  # noqa: E501
                                    h << h.li(h.a('Demonstrations portal', href=NAGARE+'portal'))  # noqa: E501
                                    h << h.li(h.a('Demonstrations', href=NAGARE+'demo'))  # noqa: E501
                                    h << h.li(h.a('Wiki Tutorial', href=NAGARE+'wiki'))  # noqa: E501

                return h.root


            # ---------------------------------------------------------------

            app = %(Id)s
        """ % params))


def create_models_py(filename):
    with open(filename, 'w') as f:
        f.write(textwrap.dedent('''\
            from elixir import *  # noqa: F403, F401
            from sqlalchemy import MetaData

            __metadata__ = MetaData()

            # Here, put the definition of your Elixir or SQLAlchemy models
        '''))


def create_conf(filename, params):
    with open(filename, 'w') as f:
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


def run(parser, options, args):
    if len(args) == 0:
        parser.error('an application name must be provided')

    if len(args) > 1:
        parser.error('only one application name must be provided')

    root = args[0]
    app_name = os.path.basename(root)
    app_id = app_name.replace('-', '_')

    create_or_update(root, os.mkdir)

    params = {
        'exe': sys.executable,
        'root': root,
        'setup': os.path.join(root, 'setup.py'),
        'name': app_name,
        'id': app_id,
        'Id': app_id.capitalize()
    }

    create_or_update(os.path.join(root, 'setup.py'), create_setup_py, upgrade_setup_py, params)
    create_or_update(os.path.join(root, 'setup.cfg'), upgrade_setup_cfg, upgrade_setup_cfg)
    create_or_update(os.path.join(root, 'MANIFEST.in'), create_manifest_in)

    create_or_update(os.path.join(root, app_id), os.mkdir)
    create_or_update(os.path.join(root, app_id, '__init__.py'), create_empty_file)
    create_or_update(os.path.join(root, app_id, 'app.py'), create_app_py, None, params)
    create_or_update(os.path.join(root, app_id, 'models.py'), create_models_py)

    create_or_update(os.path.join(root, 'static'), os.mkdir)
    create_or_update(os.path.join(root, 'static', '__init__.py'), create_empty_file)

    create_or_update(os.path.join(root, 'data'), os.mkdir)
    create_or_update(os.path.join(root, 'data', '__init__.py'), create_empty_file)
    create_or_update(os.path.join(root, 'data', 'locale'), os.mkdir)

    create_or_update(os.path.join(root, 'conf'), os.mkdir)
    create_or_update(os.path.join(root, 'conf', '__init__.py'), create_empty_file)
    create_or_update(os.path.join(root, 'conf', app_id + '.cfg'), create_conf, None, params)

    print "Application '%s' created." % app_name
    print
    print textwrap.dedent("""\
        Note:
          1. Edit the file '%(setup)s' to set the informations about your new application.
          2. Register your application with:
               - cd "%(root)s"
               - "%(exe)s" setup.py develop
        """ % params)


class Create(command.Command):
    desc = 'Create an application skeleton'

    set_options = staticmethod(set_options)
    run = staticmethod(run)
