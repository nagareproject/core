#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from __future__ import with_statement

from nagare.namespaces import xhtml
from nagare.namespaces import xhtml_base
from nagare.namespaces import xml
from nagare import callbacks
from nagare import wsgi
from nagare import local
from nagare.sessions.memory_sessions import SessionsWithPickledStates
from nagare import presentation

from types import ListType

from paste.fixture import TestApp

import os

def create_FixtureApp(app):
    local.worker = local.Process()
    local.request = local.Process()

    app = wsgi.create_WSGIApp(app)
    app.set_sessions_manager(SessionsWithPickledStates())
    app.start()

    return TestApp(app)

# Test for XHTML namespace

def head_render_init_test1():
    """ XHTML namespace unit test - HeadRender - Allowed tags """
    try:
        h = xhtml.HeadRenderer('/tmp/static_directory/')
        with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
            h << h.base({'id':'id', 'href':'href', 'target':'target'})
            h << h.link({'charset':'charset', 'href':'href', 'hreflang':'hreflang', 'type':'type', 'rel':'rel', 'rev':'rev', 'media':'media', 'target':'target'})
            h << h.meta({'id':'id', 'http_equiv':'http_equiv', 'name':'name', 'content':'content', 'scheme':'scheme'})
            h << h.title({'title':'title'})
            h << h.style({'id':'id'})
            h << h.script({'id':'id'})
    except AttributeError:
        assert False
    else:
        assert True


def head_render_init_test2():
    """ XHTML namespace unit test - HeadRender - Forbiden tag """
    try:
        h = xhtml.HeadRenderer('/tmp/static_directory/')
        h << h.test({'id':'id', 'href':'href', 'target':'target'})
    except AttributeError:
        assert True
    else:
        assert False


def head_render_css_url_test1():
    """ XHTML namespace unit test - HeadRender - css_url - relative url """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
        h << h.css_url('css')

    assert h._css_url == {'/tmp/static_directory/css' : (0, {})}


def head_render_javascript_css_test2():
    """ XHTML namespace unit test - HeadRender - css_url - absolute url """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
        h << h.css_url('/css')

    assert h._css_url == {'/css' : (0, {})}


def head_render_css_url_test3():
    """ XHTML namespace unit test - HeadRender - css_url - absolute url + relative url """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
        h << h.css_url('/css')
        h << h.css_url('css')

    assert h._css_url['/css'] == (0, {})
    assert h._css_url['/tmp/static_directory/css'] == (1, {})


def head_render_javascript_url_test1():
    """ XHTML namespace unit test - HeadRender - javascript_url - relative url """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
        h << h.javascript_url('test.js')

    assert h._javascript_url == {'/tmp/static_directory/test.js' : (0, {})}


def head_render_javascript_url_test2():
    """ XHTML namespace unit test - HeadRender - javascript_url - absolute url """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
        h << h.javascript_url('/test.js')
    assert h._javascript_url == {'/test.js' : (0, {})}


def head_render_javascript_url_test3():
    """ XHTML namespace unit test - HeadRender - javascript_url - absolute url + relative url """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
        h << h.javascript_url('/test.js')
        h << h.javascript_url('test.js')

    assert h._javascript_url['/test.js'] == (0, {})
    assert h._javascript_url['/tmp/static_directory/test.js'] == (1, {})


def head_render_javascript_url_test4():
    """ XHTML namespace unit test - HeadRender - javascript_url - Add twice the same js_url"""
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
        h << h.javascript_url('test.js')
        h << h.javascript_url('test.js')

    assert h._javascript_url == {'/tmp/static_directory/test.js' : (0, {})}


def head_render_javascript_test1():
    """ XHTML namespace unit test - HeadRender - javascript - use string """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
        h << h.javascript('test', 'function test(arg1) { return true }')

    assert h._named_javascript == {'test': (0, 'function test(arg1) { return true }', {})}


def head_render_javascript_test2():
    """ XHTML namespace unit test - HeadRender - javascript - use python method """

    def js_method(arg1):
        return True

    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
        h << h.javascript('test', js_method)

    assert h._javascript_url == {'/static/nagare/pyjslib.js' : (0, {})}
    assert h._named_javascript.has_key('test')


def head_render_javascript_test3():
    """ XHTML namespace unit test - HeadRender - javascript - add 2 js with same name """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
        h << h.javascript('test', 'function test(arg1) { return true }')
        h << h.javascript('test', 'function test(arg1) { return true }')

    assert h._named_javascript == {'test' : (0, 'function test(arg1) { return true }', {})}


def head_render_render_test1():
    """ XHTML namespace unit test - HeadRender - Render - render only style tag """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    h << h.style()
    assert presentation.render(h, None, None, None).write_htmlstring().replace('\n', '') == '<head><style></style></head>'


def head_render_render_test2():
    """ XHTML namespace unit test - HeadRender - Render - render only css_url method """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    h << h.css_url('css')
    assert presentation.render(h, None, None, None).write_htmlstring().replace('\n', '') == '<head><link href="/tmp/static_directory/css" type="text/css" rel="stylesheet"></head>'


def head_render_render_test3():
    """ XHTML namespace unit test - HeadRender - Render - render only css method """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    h << h.css('css_test', 'test')
    assert presentation.render(h, None, None, None).write_htmlstring().replace('\n', '') == '<head><style type="text/css">test</style></head>'


def head_render_render_test4():
    """ XHTML namespace unit test - HeadRender - Render - call render two times with css_url method"""
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    h << h.css_url('css')
    presentation.render(h, None, None, None)
    renderResult = presentation.render(h, None, None, None)
    assert not isinstance(renderResult, ListType)
    assert presentation.render(h, None, None, None).write_htmlstring().replace('\n', '') == '<head><link href="/tmp/static_directory/css" type="text/css" rel="stylesheet"></head>'


def head_render_render_test5():
    """ XHTML namespace unit test - HeadRender - Render - render only css method """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    h << h.css('css_test', 'test')
    assert presentation.render(h, None, None, None).write_htmlstring().replace('\n', '') == '<head><style type="text/css">test</style></head>'


def head_render_render_test6():
    """ XHTML namespace unit test - HeadRender - Render - render only javascript_url method """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    h << h.javascript_url('test.js')
    assert presentation.render(h, None, None, None).write_htmlstring().replace('\n', '') == '<head><script src="/tmp/static_directory/test.js" type="text/javascript"></script></head>'


def head_render_render_test7():
    """ XHTML namespace unit test - HeadRender - Render - render only string js method """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    h << h.javascript('test.js', 'function test() { return True }')
    assert presentation.render(h, None, None, None).write_htmlstring().replace('\n', '') == '<head><script type="text/javascript">function test() { return True }</script></head>'


def head_render_render_test8():
    """ XHTML namespace unit test - HeadRender - Render - render only python2js method """

    def js_method(arg1):
        return True

    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'lang':'lang', 'dir':'dir', 'id':'id', 'profile':'profile'}):
        h << h.javascript('test', js_method)
    assert presentation.render(h, None, None, None).write_htmlstring().replace('\n', '') == '<head lang="lang" profile="profile" id="id" dir="dir"><script src="/static/nagare/pyjslib.js" type="text/javascript"></script><script type="text/javascript">function nagare_namespaces_test_test_xhtmlns_js_method(arg1) {    return true;}</script></head>'


def head_render_render_test9():
    """ XHTML namespace unit test - HeadRender - Render - render with head """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    h << h.head({'id':'id'})
    assert presentation.render(h, None, None, None).write_htmlstring().replace('\n', '') == '<head id="id"></head>'


def head_render_render_test10():
    """ XHTML namespace unit test - HeadRender - Render - render with head & style """
    h = xhtml.HeadRenderer('/tmp/static_directory/')
    with h.head({'id':'id'}):
        h << h.style('test', {'id':'id'})
    assert presentation.render(h, None, None, None).write_htmlstring().replace('\n', '') == '<head id="id"><style id="id">test</style></head>'


def html_render_init_test1():
    """ XHTML namespace unit test - HTMLRender - init - test if head exists """
    h = xhtml.Renderer()
    assert hasattr(h, 'head')
    assert isinstance(h.head, xhtml.HeadRenderer)


def html_render_init_test2():
    """ XHTML namespace unit test - HTMLRender - init - add bad element """
    h = xhtml.Renderer()
    try:
        h << h.bad_element
    except AttributeError:
        assert True
    else:
        assert False


def html_render_parse_html_test1():
    """ XHTML namespace unit test - HTMLRender - parse_html - good encoding """
    try:
        h = xhtml.Renderer()
        root = h.parse_html(os.path.join(os.path.dirname(__file__), 'helloworld.html'))
    except UnicodeDecodeError:
        assert False
    else:
        assert True


if 0:
    def html_render_parse_html_test2():
        """ XHTML namespace unit test - HTMLRender - parse_html - bad encoding """
        try:
            h = xhtml.Renderer()
            root = h.parse_html(os.path.join(os.path.dirname(__file__), 'iso-8859.html'), encoding='utf-8')
        except UnicodeDecodeError:
            assert True
        else:
            assert False


def html_render_parse_html_test3():
    """ XHTML namespace unit test - HTMLRender - parse_htmlstring - bad html (auto correct)"""
    h = xhtml.Renderer()
    root = h.parse_htmlstring('<html><head><body></body></head><html>')
    assert root.write_htmlstring() == '<html><head></head><body></body></html>'


def html_render_parse_html_test4():
    """ XHTML namespace unit test - HTMLRender - parse_htmlstring - bad html"""
    h = xhtml.Renderer()
    root = h.parse_htmlstring('test')
    assert root.write_htmlstring() == '<html><body><p>test</p></body></html>'


def html_render_parse_html_test5():
    """ XHTML namespace unit test - HTMLRender - parse_html - get html from an URL """
    try:
        h = xhtml.Renderer()
        root = h.parse_html('http://www.google.fr/')
    except:
        assert False
    else:
        assert True


xml_tree_1 = "<a>text</a>"
def html_render_parse_html_test6():
    """ XHTML namespace unit test - HTMLRender - parse_html - option xhtml=False - xmlstring - Test child type """
    x = xhtml.Renderer()
    root = x.parse_htmlstring(xml_tree_1, xhtml=False)
    assert type(root) == xhtml_base._HTMLTag


def html_render_parse_html_test7():
    """ XHTML namespace unit test - HTMLRender - parse_html - option xhtml=True  - xmlstring - Test child type """
    x = xhtml.Renderer()
    root = x.parse_htmlstring(xml_tree_1, xhtml=True)
    assert type(root) == xhtml.A


def html_render_parse_html_test8():
    """ XHTML namespace unit test - HTMLRender - parse_xml - xmlstring - Test child type """
    x = xhtml.Renderer()
    root = x.parse_xmlstring(xml_tree_1)
    assert type(root) == xml._Tag


html_tree_1 = "<html><body></html>"
def html_render_parse_html_test9():
    """ XHTML namespace unit test - HTMLRender - parse_html - option xhtml=False - htmlstring - Test child type """
    x = xhtml.Renderer()
    root = x.parse_htmlstring(html_tree_1, xhtml=False)
    assert type(root) == xhtml_base._HTMLTag


def html_render_parse_html_test10():
    """ XHTML namespace unit test - HTMLRender - parse_html - option xhtml=True  - htmlstring - Test child type """
    try:
        x = xhtml.Renderer()
        root = x.parse_htmlstring(html_tree_1, xhtml=True)
    except:
        assert True
    else:
        assert False


def html_render_parse_html_test11():
    """ XHTML namespace unit test - HTMLRender - parse_xml - htmlstring - Test child type """
    try:
        x = xhtml.Renderer()
        root = x.parse_xmlstring(html_tree_1)
    except:
        assert True
    else:
        assert False


xhtml_tree_1 = "<xhtml><a/></xhtml>"
def html_render_parse_html_test12():
    """ XHTML namespace unit test - HTMLRender - parse_html - option xhtml=False - xhtmlstring - Test child type """
    x = xhtml.Renderer()
    root = x.parse_htmlstring(xhtml_tree_1, xhtml=False)
    assert type(root.getchildren()[0]) == xhtml_base._HTMLTag


def html_render_parse_html_test13():
    """ XHTML namespace unit test - HTMLRender - parse_html - option xhtml=True - xhtmlstring - Test child type """
    x = xhtml.Renderer()
    root = x.parse_htmlstring(xhtml_tree_1, xhtml=True)
    assert type(root.getchildren()[0]) == xhtml.A


def html_render_parse_html_test14():
    """ XHTML namespace unit test - HTMLRender - parse_xml - xhtmlstring - Test child type """
    x = xhtml.Renderer()
    root = x.parse_xmlstring(xhtml_tree_1)
    assert type(root.getchildren()[0]) == xml._Tag


def htmltag_write_xmlstring_test1():
    """ XHTML namespace unit test - HTMLRender - write_htmlstring - without argument """
    h = xhtml.Renderer()
    h << h.table(h.tr(h.td()),h.tr(h.td()))
    assert h.root.write_htmlstring() == '<table><tr><td></td></tr><tr><td></td></tr></table>'


def htmltag_write_xmlstring_test2():
    """ XHTML namespace unit test - HTMLRender - write_htmlstring - with pipeline == True"""
    h = xhtml.Renderer()
    h << h.table(h.tr(h.td().meld_id('test'),h.tr(h.td().meld_id('test'))))
    assert h.root.write_htmlstring(pipeline=True) == '<table><tr><td xmlns:ns0="http://www.plope.com/software/meld3" ns0:id="test"></td><tr><td xmlns:ns0="http://www.plope.com/software/meld3" ns0:id="test"></td></tr></tr></table>'


def htmltag_write_xmlstring_test3():
    """ XHTML namespace unit test - HTMLRender - write_htmlstring - with pipeline == False """
    h = xhtml.Renderer()
    h << h.table(h.tr(h.td().meld_id('false'),h.tr(h.td().meld_id('false'))))
    assert h.root.write_htmlstring(pipeline=False) == '<table><tr><td xmlns:ns0="http://www.plope.com/software/meld3"></td><tr><td xmlns:ns0="http://www.plope.com/software/meld3"></td></tr></tr></table>'


def html_render_add_tag_test1():
    """ XHTML namespace unit test - HTMLRender - add tag - create simple html """
    h = xhtml.Renderer()
    h << h.html(h.body(h.table(h.tr(h.td()),h.tr(h.td()))))
    assert h.root.write_htmlstring().replace('\n', '') == '<html><body><table><tr><td></td></tr><tr><td></td></tr></table></body></html>'


def html_render_form_test1():
    """ XHTML namespace unit test - Form - create simple form """
    h = xhtml.Renderer()
    h << h.html(h.body(h.form(h.input(type="string", name="input1", value="value"), h.input(type="submit", name="submit"))))
    form = h.root.xpath('.//form')
    attributes = form[0].attrib
    assert attributes['method'] == "post"
    assert attributes['accept-charset'] == "utf-8"
    assert attributes['enctype'] == "multipart/form-data"
    assert attributes['action'] == "?"

    assert h.root.write_htmlstring().replace('\n', '') == '<html><body><form enctype="multipart/form-data" method="post" accept-charset="utf-8" action="?"><input type="string" name="input1" value="value"><input type="submit" name="submit"></form></body></html>'


def html_render_form_test2():
    """ XHTML namespace unit test - Form - create 2 imbrecated forms """
    h = xhtml.Renderer()
    h << h.html(h.body(h.form(h.input(type="string", name="input1", value="value"), h.form(h.input(type="submit", name="submit")))))
    assert len(h.root.xpath('.//form')) == 1


def html_render_form_test3():
    """ XHTML namespace unit test - Form - create 2 forms not imbrecated"""
    h = xhtml.Renderer()
    h << h.html(h.body(h.form(h.input(type="string", name="input1", value="value")), h.form(h.input(type="string", name="input2", value="value"))))
    assert len(h.root.xpath('.//form')) == 2


def html_render_form_test4():
    """ XHTML namespace unit test - Form - create simple form with iso-8859-15 enconding"""
    h = xhtml.Renderer()
    h << h.html(h.body(h.form(h.input(type="string", name="input1", value="value"), h.input(type="submit", name="submit"), {"accept-charset":"iso-8859-15"})))
    form = h.root.xpath('.//form')
    attributes = form[0].attrib
    assert attributes['method'] == "post"
    assert attributes['accept-charset'] == "iso-8859-15"
    assert attributes['enctype'] == "multipart/form-data"
    assert attributes['action'] == "?"


class My_app_test_form():

    def __init__(self):
        self.actions_done = []

    def my_pre_action(self):
        self.actions_done.append('my_pre_action')
        assert self.actions_done == ['my_pre_action']


    def my_post_action(self):
        self.actions_done.append('my_post_action')
        assert self.actions_done == ['my_pre_action', 'my_input_action', 'my_post_action',]


    def my_input_action(self):
        self.actions_done.append('my_input_action')
        assert self.actions_done == ['my_pre_action', 'my_input_action']


    def my_submit_action(self):
        self.actions_done.append('my_submit_action')
        assert self.actions_done == ['my_pre_action', 'my_input_action', 'my_post_action', 'my_submit_action']


@presentation.render_for(My_app_test_form)
def render(self, h, *args):
    h << h.html(h.body(h.div('My_app_test_form'),
                       h.form(
                              h.input(type="text", name="input1", value="value").action(lambda x: self.my_input_action()),
                              h.input(type="submit", name="submit").action(lambda: self.my_submit_action())
                             ).pre_action(lambda: self.my_pre_action()).post_action(lambda: self.my_post_action())
         ))
    return h.root


def html_render_form_test5():
    """ XHTML namespace unit test - Form - create test methods call order """
    myApp = My_app_test_form
    app = create_FixtureApp(myApp)
    res = app.get('/')
    form = res.forms[0]
    res = form.submit()


def html_render_select_test1():
    """ XHTML namespace unit test - Select - form with simple select input """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                with h.select:
                    h << h.option(value="option1")
                    h << h.option(value="option2", selected='selected')
    options = h.root.xpath('.//option')
    assert options[1].attrib['selected'] == 'selected'


def html_render_select_test2():
    """ XHTML namespace unit test - Select - test selected method """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                with h.select:
                    h << h.option(value="option1")
                    h << h.option(value="option2")

    options = h.root.xpath('.//option')
    for option in options:
        option.selected('option2')

    assert options[1].attrib['selected'] == 'selected'


def html_render_select_test3():
    """ XHTML namespace unit test - Select - test selected method with multiple select """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                with h.select(multiple=True):
                    h << h.option(value="option1")
                    h << h.option(value="option2")
                    h << h.option(value="option3")

    options = h.root.xpath('.//option')
    for option in options:
        option.selected(['option1', 'option3'])

    assert options[0].attrib['selected'] == 'selected'
    assert options[2].attrib['selected'] == 'selected'


def html_render_select_test4():
    """ XHTML namespace unit test - Select - test selected method with multiple select and prefixed select """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                with h.select(multiple=True):
                    h << h.option(value="option1")
                    h << h.option(value="option2", selected="selected")
                    h << h.option(value="option3")

    options = h.root.xpath('.//option')
    for option in options:
        option.selected(['option1', 'option3'])

    assert options[0].attrib['selected'] == 'selected'
    assert options[2].attrib['selected'] == 'selected'


def html_render_select_test5():
    """ XHTML namespace unit test - Select - test selected method with multiple select and option group """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                with h.select(multiple=True):
                    h << h.option(value="option1")
                    with h.optgroup:
                        h << h.option(value="option2")
                        h << h.option(value="option3")

    options = h.root.xpath('.//option')
    for option in options:
        option.selected(['option1', 'option3'])

    assert options[0].attrib['selected'] == 'selected'
    assert options[2].attrib['selected'] == 'selected'


def html_render_select_test6():
    """ XHTML namespace unit test - Select - test selected method with multiple select """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                h << h.select([h.option(value='option1').selected(['option1', 'option3']),
                               h.option(value='option2').selected(['option1', 'option3']),
                               h.option(value='option3').selected(['option1', 'option3'])], multiple=True)

    options = h.root.xpath('.//option')
    assert options[0].attrib['selected'] == 'selected'
    assert options[2].attrib['selected'] == 'selected'



class My_app_test_select_multiple():

    def __init__(self):
        self.choices = "default"

    def set_choices(self, choices):
        assert isinstance(choices, (list, tuple))
        self.choices = choices


@presentation.render_for(My_app_test_select_multiple)
def render(self, h, *args):
    with h.html:
        with h.body:
            h << h.div("choice:", self.choices)
            with h.form:
                h << h.select([h.option(value='option1').selected(['option2']),
                               h.option(value='option2').selected(['option2']),
                               h.option(value='option3').selected(['option2'])], multiple=True).action(lambda opt: self.set_choices(opt))
    return h.root


def html_render_select_test7():
    """ XHTML namespace unit test - Select - test selected method with multiple attribute but one choice """
    myApp = My_app_test_select_multiple
    app = create_FixtureApp(myApp)
    res = app.get('/')
    assert 'choice:default' in res
    form = res.forms[0]
    res = form.submit()
    assert 'choice:option2' in res


class My_app_test_select_single():

    def __init__(self):
        self.choices = "default"

    def set_choice(self, choices):
        assert choices == 'option1'
        self.choices = choices


@presentation.render_for(My_app_test_select_single)
def render(self, h, *args):
    with h.html:
        with h.body:
            h << h.div("choice:", self.choices)
            with h.form:
                h << h.select([h.option(value="option1").selected(['option1']),
                               h.option(value="option2").selected(['option1']),
                               h.option(value="option3").selected(['option1'])]).action(lambda opt: self.set_choice(opt))
    return h.root


def html_render_select_test8():
    """ XHTML namespace unit test - Select - test selected method with single attribute """
    myApp = My_app_test_select_single
    app = create_FixtureApp(myApp)
    res = app.get('/')
    assert 'choice:default' in res
    form = res.forms[0]
    res = form.submit()
    assert 'choice:option1' in res


def html_render_checkbox_test1():
    """ XHTML namespace unit test - Checkboxes - init """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                h << h.input(type="checkbox", value="option1")
                h << h.input(type="checkbox", value="option2", checked='checked')
    checkboxes = h.root.xpath('.//input[@type="checkbox"]')
    assert 'checked' not in checkboxes[0].attrib.keys()
    assert 'checked' in checkboxes[1].attrib.keys()


def html_render_checkbox_test2():
    """ XHTML namespace unit test - Checkboxes - test selected method """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                checkbox = h.input(type="checkbox", value="option1")
                h << checkbox
                h << h.input(type="checkbox", value="option2", checked='checked')
    checkboxes = h.root.xpath('.//input[@type="checkbox"]')
    checkbox.selected(True)

    assert 'checked' in checkboxes[0].attrib.keys()
    assert 'checked' in checkboxes[1].attrib.keys()


def html_render_checkbox_test3():
    """ XHTML namespace unit test - Checkboxes - test selected method to unselected checkbox """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                checkbox = h.input(type="checkbox", value="option1", checked='checked')
                h << checkbox
                h << h.input(type="checkbox", value="option2")
    checkboxes = h.root.xpath('.//input[@type="checkbox"]')
    checkbox.selected(False)

    assert 'checked' not in checkboxes[0].attrib.keys()


def html_render_radiobutton_test1():
    """ XHTML namespace unit test - Radio - init """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                h << h.input(name="radio", type="radio", value="option1")
                h << h.input(name="radio", type="radio", value="option2", checked='checked')
                h << h.input(name="radio", type="radio", value="option3")
    radios = h.root.xpath('.//input[@type="radio"]')
    assert 'checked' not in radios[0].attrib.keys()
    assert 'checked' in radios[1].attrib.keys()
    assert 'checked' not in radios[2].attrib.keys()


def html_render_radiobutton_test2():
    """ XHTML namespace unit test - Radio - test selected method """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                radio = h.input(name="radio", type="radio", value="option1")
                h << radio
                h << h.input(name="radio", type="radio", value="option2", checked='checked')
                h << h.input(name="radio", type="radio", value="option3")
    radios = h.root.xpath('.//input[@type="radio"]')
    radio.selected(True)
    assert 'checked' in radios[0].attrib.keys()
    assert 'checked' in radios[1].attrib.keys()
    assert 'checked' not in radios[2].attrib.keys()


def html_render_radiobutton_test3():
    """ XHTML namespace unit test - Radio - test selected method to unselected checkbox """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                h << h.input(name="radio", type="radio", value="option1")
                radio = h.input(name="radio", type="radio", value="option2", checked='checked')
                h << radio
                h << h.input(name="radio", type="radio", value="option3")
    radios = h.root.xpath('.//input[@type="radio"]')
    radio.selected(False)
    assert 'checked' not in radios[0].attrib.keys()
    assert 'checked' not in radios[1].attrib.keys()
    assert 'checked' not in radios[2].attrib.keys()


def html_render_radiobutton_test4():
    """ XHTML namespace unit test - Radio - init with label """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                h << h.input(name="radio", type="radio", value="value1", id="option1") << h.label("option 1", for_="option1") << h.br
                h << h.input(name="radio", type="radio", value="value1", id="option2", checked="checked") << h.label("option 2", for_="option2") << h.br
                h << h.input(name="radio", type="radio", value="value1", id="option3") << h.label("option 3", for_="option3") << h.br
    labels = h.root.xpath('.//label')

    assert reduce(lambda x, y: x and y, [label.get('for') is not None for label in labels])



def html_render_textarea_test1():
    """ XHTML namespace unit test - TextArea - init """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                h << h.textarea("test", name="textearea1", type="textarea")

    textarea = h.root.xpath('.//textarea')[0]
    assert textarea.text == 'test'


def html_render_submit_test1():
    """ XHTML namespace unit test - Input submit - init """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                input = h.input(name="submit1", type="submit")
                h << input

    assert isinstance(input, xhtml.SubmitInput)


def html_render_password_test1():
    """ XHTML namespace unit test - Input password - init """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                input = h.input(name="password1", type="password")
                h << input

    assert isinstance(input, xhtml.PasswordInput)


def html_render_hidden_test1():
    """ XHTML namespace unit test - Input hidden - init """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                input = h.input(name="hidden1", type="hidden")
                h << input

    assert isinstance(input, xhtml.HiddenInput)


def html_render_file_test1():
    """ XHTML namespace unit test - Input file - init """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                input = h.input(name="file1", type="file")
                h << input

    assert isinstance(input, xhtml.FileInput)


def html_render_text_test1():
    """ XHTML namespace unit test - Input text - init """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                input = h.input(name="text1", type="text")
                h << input

    assert isinstance(input, xhtml.TextInput)


def html_render_text_test1():
    """ XHTML namespace unit test - Input text - init """
    h = xhtml.Renderer()
    with h.html:
        with h.body:
            with h.form:
                input = h.input(name="text1", type="text")
                h << input

    assert isinstance(input, xhtml.TextInput)


def html_render_img_test1():
    """ XHTML namespace unit test - Tag img - init - external source """
    h = xhtml.Renderer()

    with h.html:
        with h.body:
            h << h.img(src="http://www.google.com/intl/en_ALL/images/logo.gif")

    assert h.root.write_htmlstring() == '<html><body><img src="http://www.google.com/intl/en_ALL/images/logo.gif"></body></html>'


def html_render_img_test2():
    """ XHTML namespace unit test - Tag img - init - relative source """
    h = xhtml.Renderer(static='/tmp/static/')

    with h.html:
        with h.body:
            h << h.img(src="logo.gif")

    assert h.root.write_htmlstring() == '<html><body><img src="/tmp/static/logo.gif"></body></html>'


def html_render_img_test3():
    """ XHTML namespace unit test - Tag img - init - absolute source """
    h = xhtml.Renderer(static_url='/tmp/static/')

    with h.html:
        with h.body:
            h << h.img(src="/logo.gif")

    assert h.root.write_htmlstring() == '<html><body><img src="/logo.gif"></body></html>'


def html_render_select_test8():
    """ XHTML namespace unit test - Select - test selected method with single attribute """
    myApp = My_app_test_select_single
    app = create_FixtureApp(myApp)
    res = app.get('/')
    assert 'choice:default' in res
    form = res.forms[0]
    res = form.submit()
    assert 'choice:option1' in res


def html_render_a_test1():
    """ XHTML namespace unit test - Tag a - init """
    h = xhtml.Renderer()

    with h.html:
        with h.body:
            h << h.a("google", href="http://www.google.com")

    a = h.root.xpath('.//a')[0]
    assert isinstance(a, xhtml.A)
    assert h.root.write_htmlstring() == '<html><body><a href="http://www.google.com">google</a></body></html>'


def html_render_img_test2():
    """ XHTML namespace unit test - Tag a - init - relative source """
    h = xhtml.Renderer(static_url='/tmp/static/')

    with h.html:
        with h.body:
            h << h.img(src="logo.gif")

    assert h.root.write_htmlstring() == '<html><body><img src="/tmp/static/logo.gif"></body></html>'


def html_render_action_test1():
    """ XHTML namespace unit test - action - put action method on tag a """
    h = xhtml.Renderer(callbacks=callbacks.Callbacks(), static_url='/tmp/static/')

    with h.html:
        with h.body:
            a = h.a().action(lambda x: None)
            h << a

    assert a.attrib['href'] is not None


def html_render_action_test2():
    """ XHTML namespace unit test - action - put action method on tag a (replace existing href) """
    h = xhtml.Renderer(callbacks=callbacks.Callbacks(), static_url='/tmp/static/')

    with h.html:
        with h.body:
            a = h.a(href='http://www.google.com').action(lambda x: None)
            h << a

    assert a.attrib['href'] == 'http://www.google.com'


def html_render_action_test3():
    """ XHTML namespace unit test - action - put action method on tag imagge """
    h = xhtml.Renderer(callbacks=callbacks.Callbacks(), static_url='/tmp/static/')

    with h.html:
        with h.body:
            a = h.img().action(lambda x: None)
            h << a

    assert a.attrib['src'] is not None


def html_render_action_test4():
    """ XHTML namespace unit test - action - put action method on tag a (replace existing href) """
    h = xhtml.Renderer(callbacks=callbacks.Callbacks(), static_url='/tmp/static/')

    with h.html:
        with h.body:
            a = h.a(src="logo.gif").action(lambda x: None)
            h << a

    assert a.attrib['src'] != 'http://www.google.com'


def html_render_action_test5():
    """ XHTML namespace unit test - asynchronous render - action - put action method on tag a """
    h = xhtml.AsyncRenderer(callbacks=callbacks.Callbacks(), static_url='/tmp/static/')

    with h.html:
        with h.body:
            a = h.a().action(lambda x: None)
            h << a

    assert a.attrib['href'] is not None


def html_render_action_test6():
    """ XHTML namespace unit test - asynchronous render - action - put action method on tag a (replace existing href) """
    h = xhtml.AsyncRenderer(callbacks=callbacks.Callbacks(), static_url='/tmp/static/')

    with h.html:
        with h.body:
            a = h.a(href='http://www.google.com').action(lambda x: None)
            h << a

    assert a.attrib['href'] != 'http://www.google.com'


def html_render_action_test7():
    """ XHTML namespace unit test - asynchronous render - action - put action method on tag imagge """
    h = xhtml.AsyncRenderer(callbacks=callbacks.Callbacks(), static_url='/tmp/static/')

    with h.html:
        with h.body:
            a = h.img().action(lambda x: None)
            h << a

    assert a.attrib['src'] is not None


def html_render_action_test8():
    """ XHTML namespace unit test - asynchronous render - action - put action method on tag a (replace existing href) """
    h = xhtml.AsyncRenderer(callbacks=callbacks.Callbacks(), static_url='/tmp/static/')

    with h.html:
        with h.body:
            a = h.a(src="logo.gif").action(lambda x: None)
            h << a

    assert a.attrib['src'] != 'http://www.google.com'


xml_test1_out = """<html><body onload="javascript:alert()">
<ul>
<li>Hello</li>
<li>world</li>
<li>yeah</li>
</ul>
<div class="toto"><h1>moi<i>toto</i>
</h1></div>
<div>yeah012</div>
<table toto="toto">
<tr>
<td>1</td>
<td>a</td>
</tr>
<tr>
<td>2</td>
<td>b</td>
</tr>
<tr>
<td>3</td>
<td>c</td>
</tr>
</table>
</body></html>"""


def global_test1():
    """ XHTML namespace unit test - create xhtml by procedural way """
    t = ((1, 'a'), (2, 'b'), (3, 'c'))

    h = xhtml.Renderer()

    with h.html:
        with h.body(onload='javascript:alert()'):
            with h.ul:
                with h.li('Hello'): pass
                with h.li:
                    h << 'world'
                h << h.li('yeah')

            with h.div(class_='toto'):
                with h.h1('moi'):
                    h << h.i('toto')

            with h.div:
                h << 'yeah'
                for i in range(3):
                    h << i

            with h.table(toto='toto'):
                for row in t:
                    with h.tr:
                        for column in row:
                            with h.td:
                                h << column

    xmlToTest = h.root.write_htmlstring(pretty_print=True).strip()
    assert xmlToTest == xml_test1_out


def global_test2():
    """ XHTML namespace unit test - create xhtml by functionnal way """
    t = ((1, 'a'), (2, 'b'), (3, 'c'))

    h = xhtml.Renderer()

    helloWorld = h.ul([h.li('Hello'), h.li('world'), h.li('yeah')])
    totoDiv    = h.div([h.h1('moi', [h.i('toto')])], {'class':'toto'})
    yeah012    = h.div('yeah012')
    table      = h.table([h.tr([h.td(elt1), h.td(elt2)]) for elt1,elt2 in t], {'toto':'toto'})

    html = h.html([h.body([helloWorld, totoDiv, yeah012, table], {'onload':'javascript:alert()'})])

    xmlToTest = html.write_htmlstring(pretty_print=True).strip()

    assert xmlToTest == xml_test1_out
