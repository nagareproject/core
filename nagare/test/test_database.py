#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import os
import csv
import operator

from elixir import *
from sqlalchemy import MetaData

from nose import with_setup
from paste.fixture import TestApp

from nagare.namespaces import xml
from nagare import presentation
from nagare import component
from nagare import wsgi
from nagare import local
from nagare.sessions.memory_sessions import SessionsWithPickledStates

from exceptions import Exception

def create_FixtureApp(app):
    local.worker = local.Process()
    local.request = local.Process()

    app = wsgi.create_WSGIApp(app)
    app.set_sessions_manager(SessionsWithPickledStates())
    app.start()

    return TestApp(app)

__metadata__ = MetaData()
__metadata__.bind = "sqlite:///:memory:"
__metadata__.bind.echo = False

# Setup / Teardown functions
def setup():
    setup_all()


def setup_func():
    create_all()


def teardown_func():
    drop_all()


class Language(Entity):
    id = Field(Unicode(50), primary_key=True)
    label = Field(Unicode(50))


class App1:

    def __init__(self):
        self.languages = []


    def add_language(self, language):
        self.languages.append(language)


@presentation.render_for(App1)
def render(self, h, *args):
    return h.helloWorlds([h.helloWorld(language.label, {'language':language.id}) for language in self.languages])


@with_setup(setup_func, teardown_func)
def test_1():
    """ database - simple test with sqlalchemy/elixir """
    Language(id=u"english", label=u"hello world")
    session.flush()

    language = Language.query.all()[0]
    assert language.id    == u"english"
    assert language.label == u"hello world"

    Language(id=u"french", label=u"bonjour monde")
    session.flush()

    language = Language.query.all()[1]
    assert language.id    == u"french"
    assert language.label == u"bonjour monde"


@with_setup(setup_func, teardown_func)
def test_2():
    """ database - simple test with sqlalchemy/elixir unicode test """
    filePath = os.path.join(os.path.dirname(__file__), 'helloworld.csv')
    reader = csv.reader(open(filePath, 'r'))

    res = {}
    for row in reader:
        res[row[0].decode('utf-8')] = row[1].decode('utf-8')
        Language(id=row[0].decode('utf-8'), label=row[1].decode('utf-8'))
    session.flush()

    for language in Language.query.all():
        assert language.label == res[language.id]



@with_setup(setup_func, teardown_func)
def test_3():
    """ database - test with elixir & framework render method """
    app = App1()

    filePath = os.path.join(os.path.dirname(__file__), 'helloworld.csv')
    reader = csv.reader(open(filePath, 'r'))

    res = {}
    for row in reader:
        res[row[0].decode('utf-8')] = row[1].decode('utf-8')
        Language(id=row[0].decode('utf-8'), label=row[1].decode('utf-8'))
    session.flush()

    for language in Language.query.all():
        app.add_language(language)

    h = xml.Renderer()
    xmlToTest = component.Component(app).render(h).write_xmlstring(xml_declaration=True, pretty_print=True).strip()

    f = open(os.path.join(os.path.dirname(__file__), 'test_xmlns_1.xml'))
    xmlToCompare = f.read()
    f.close()

    assert xmlToTest == xmlToCompare


class Father(Entity):
    name = Field(Unicode(100))
    has_many('children', of_kind='Child')


class Child(Entity):
    name = Field(Unicode(100))
    belongs_to('father', of_kind='Father')


@with_setup(setup_func, teardown_func)
def test4():
    """ database - test children relation with sqlalchemy/elixir """

    f = Father(name=u"Father")

    c1 = Child(name=u"Child1")
    c2 = Child(name=u"Child2")

    f.children.append(c1)
    f.children.append(c2)
    assert f is c1.father
    assert f is c2.father
    session.flush()

    assert reduce(operator.__and__, [(elt.father.id == f.id) for elt in Child.query.all()])


def setup_func_2():
    create_all()
    Father(name=u"Charles Ingalls")
    session.flush()

class My_database_app():

    def __init__(self):
        self.father = Father.get_by(name=u'Charles Ingalls')

    def add_child(self, name):
        child = Child(name=name)
        self.father.children.append(child)
        if "Ingalls" not in name:
            raise Exception


@presentation.render_for(My_database_app, model='name')
def render(self, h, *args):
    h << h.div(self.father.name)
    return h.root

@presentation.render_for(My_database_app)
def render(self, h, comp, *args):
    h << h.div(self.father.name, id="father")
    h << [h.div(child.name, id="child") for child in self.father.children]

    h << h.a('Add Mary', id='add_mary').action(lambda: self.add_child(u'Mary Ingalls'))
    h << h.a('Add Nancy', id='add_nancy').action(lambda: self.add_child(u'Nancy Oleson'))
    h << h.a('Add Carrie', id='add_carrie').action(lambda: self.add_child(u'Carrie Ingalls'))
    h << h.a('changes name', id='get_name').action(lambda: comp.becomes(self, model='name'))

    return h.root


@with_setup(setup_func_2, teardown_func)
def test5():
    """ database - Get element in database """
    myApp = My_database_app
    app = create_FixtureApp(myApp)
    res = app.get('/')
    assert u"Charles Ingalls" in res


@with_setup(setup_func_2, teardown_func)
def test6():
    """ database - Add element in database """
    myApp = My_database_app
    app = create_FixtureApp(myApp)
    res = app.get('/')
    res = res.click(linkid="add_mary")
    assert Child.get_by(name=u"Mary Ingalls") is not None
    assert u"Charles Ingalls" in res
    assert u"Mary Ingalls" in res
    res = res.click(linkid="get_name")
    assert u"Charles Ingalls" in res


@with_setup(setup_func_2, teardown_func)
def test7():
    """ database - Add 2 elements in database """
    myApp = My_database_app
    app = create_FixtureApp(myApp)
    res = app.get('/')
    res = res.click(linkid="add_mary")
    assert Child.get_by(name=u"Mary Ingalls") is not None
    assert u"Charles Ingalls" in res
    assert u"Mary Ingalls" in res
    res = res.click(linkid="add_carrie")
    assert Child.get_by(name=u"Carrie Ingalls") is not None
    assert u"Charles Ingalls" in res
    assert u"Carrie Ingalls" in res
    assert u"Mary Ingalls" in res
    res = res.click(linkid="get_name")
    assert u"Charles Ingalls" in res


@with_setup(setup_func_2, teardown_func)
def test8():
    """ database - Add 2 elements in database and test rollback on Exception """
    myApp = My_database_app
    app = create_FixtureApp(myApp)
    res = app.get('/')
    res = res.click(linkid="add_mary")
    assert Child.get_by(name=u"Mary Ingalls") is not None
    assert u"Charles Ingalls" in res
    assert u"Mary Ingalls" in res

    try:
        res = res.click(linkid="add_nancy")
    except:
        res = app.get('/')
    assert Child.get_by(name=u"Nancy Oleson") is None
    assert u"Charles Ingalls" in res
    assert u"Nancy Oleson" not in res

    res = res.click(linkid="add_carrie")
    assert Child.get_by(name=u"Carrie Ingalls") is not None
    assert u"Charles Ingalls" in res
    assert u"Carrie Ingalls" in res
    assert u"Mary Ingalls" in res
    res = res.click(linkid="get_name")
    assert u"Charles Ingalls" in res
