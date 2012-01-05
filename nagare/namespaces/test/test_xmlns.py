#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from __future__ import with_statement

import csv
import os
from StringIO import StringIO
from types import ListType

from lxml import etree as ET

from nagare.namespaces import xml

def append_text_test1():
    """ XML namespace unit test - append_text Append text to an empty node

    In:
      - <node/>

    Out:
      - <node>test</node>
    """
    x = xml.Renderer()

    node = x.node()
    node.append_text('test')
    assert node.text == 'test'
    assert node.write_xmlstring() == '<node>test</node>'


def append_text_test2():
    """ XML namespace unit test - append_text - Append text to node with text child

    In:
      - <node>test1</node>

    Out:
      - <node>test1test2</node>
    """
    x = xml.Renderer()

    node = x.node('test1')
    node.append_text('test2')
    assert node.text == 'test1test2'
    assert node.write_xmlstring() == '<node>test1test2</node>'


def append_text_test3():
    """ XML namespace unit test - append_text - Append text to node with node child

    In:
      - <node><child/></node>

    Out:
      - <node><child/>test</node>
    """
    x = xml.Renderer()

    node = x.node(x.child())
    node.append_text('test')
    assert node.getchildren()[0].tail == 'test'
    assert node.write_xmlstring() == '<node><child/>test</node>'


def append_text_test4():
    """ XML namespace unit test - append_text - Append text to node with text & node children

    In:
      - <node>test1<child/></node>

    Out:
      - <node>test1<child/>test2</node>
    """
    x = xml.Renderer()

    node = x.node(['test1', x.child()])
    node.append_text('test2')
    assert node.text == 'test1'
    assert node.getchildren()[0].tail == 'test2'
    assert node.write_xmlstring() == '<node>test1<child/>test2</node>'


def add_child_test1():
    """ XML namespace unit test - add_child - add text

    In:
      - <node/>

    Out:
      - <node>test</node>
    """
    x = xml.Renderer()

    node = x.node('test')
    assert node.text == 'test'
    assert node.write_xmlstring() == '<node>test</node>'


def add_child_test2():
    """ XML namespace unit test - add_child - add node

    In:
      - <node/>

    Out:
      - <node><child/></node>
    """
    x = xml.Renderer()

    child = x.child()
    node = x.node(child)
    assert node.getchildren()[0] == child
    assert node.write_xmlstring() == '<node><child/></node>'


def add_child_test3():
    """ XML namespace unit test - add_child - add dictionnary

    In:
      - <node/>

    Out:
      - <node test="test"/>
    """
    x = xml.Renderer()

    node = x.node({'test':'test'})
    assert node.attrib == {'test':'test'}
    assert node.write_xmlstring() == '<node test="test"/>'


def add_child_test4():
    """ XML namespace unit test - add_child - add attribute with keyword

    In:
      - <node/>

    Out:
      - <node test="test"/>
    """
    x = xml.Renderer()

    node = x.node(test='test')
    assert node.attrib == {'test':'test'}
    assert node.write_xmlstring() == '<node test="test"/>'


def add_child_test5():
    """ XML namespace unit test - add_child - add tuple (text, node, text, dict)

    In:
      - <node/>

    Out:
      - <node test="test">test<child/>test</node>
    """
    x = xml.Renderer()

    child = x.child()
    node = x.node(('test', child, 'test', {'test':'test'}))

    assert node.attrib == {'test':'test'}
    assert node.text == 'test'
    assert node.getchildren()[0] == child
    assert node.getchildren()[0].tail == 'test'
    assert node.write_xmlstring() == '<node test="test">test<child/>test</node>'


def add_child_test6():
    """ XML namespace unit test - add_child - add list [text, node, text, dict]

    In:
      - <node/>

    Out:
      - <node test="test">test<child/>test</node>
    """
    x = xml.Renderer()

    child = x.child()
    node = x.node(['test', child, 'test', {'test':'test'}])

    assert node.attrib == {'test':'test'}
    assert node.text == 'test'
    assert node.getchildren()[0] == child
    assert node.getchildren()[0].tail == 'test'
    assert node.write_xmlstring() == '<node test="test">test<child/>test</node>'


def add_child_test7():
    """ XML namespace unit test - add_child - add int

    In:
      - <node/>

    Out:
      - <node>42</node>
    """
    x = xml.Renderer()

    node = x.node(42)
    assert node.text == '42'
    assert node.write_xmlstring() == '<node>42</node>'


def add_child_test8():
    """ XML namespace unit test - add_child - add float

    In:
      - <node/>

    Out:
      - <node>0.1</node>
    """
    x = xml.Renderer()

    node = x.node(0.1)
    assert node.text == '0.1'
    assert node.write_xmlstring() == '<node>0.1</node>'


def add_child_test9():
    """ XML namespace unit test - add_child - add dictionnary with python keyword

    In:
      - <node/>

    Out:
      - <node class="test"/>
    """
    x = xml.Renderer()

    node = x.node({'class_':'test'})
    assert node.attrib == {'class':'test'}
    assert node.write_xmlstring() == '<node class="test"/>'


def add_child_test10():
    """ XML namespace unit test - add_child - add attribute with python keyword

    In:
      - <node/>

    Out:
      - <node class="test"/>
    """
    x = xml.Renderer()

    node = x.node(class_='test')
    assert node.attrib == {'class':'test'}
    assert node.write_xmlstring() == '<node class="test"/>'


def add_child_test11():
    """ XML namespace unit test - add_child - add object instance and raise exception

    In:
      - <node/>

    Out:
      - Exception
    """
    x = xml.Renderer()

    try:
        node = x.node(object())
    except Exception:
        assert True
    else:
        assert False


def replace_test1():
    """ XML namespace unit test - replace - replace simple node by node

    In:
      - <node><child1/></node>

    Out:
      - <node><child2/></node>
    """
    x = xml.Renderer()

    child1 = x.child1()
    node = x.node(child1)
    assert node.getchildren()[0] == child1
    child2 = x.child2()
    child1.replace(child2)
    assert node.getchildren()[0] == child2
    assert node.write_xmlstring() == '<node><child2/></node>'


def replace_test2():
    """ XML namespace unit test - replace - replace simple node with text before by node

    In:
      - <node><child1/></node>

    Out:
      - <node><child2/></node>
    """
    x = xml.Renderer()

    child1 = x.child1()
    node = x.node('test', child1)
    assert node.getchildren()[0] == child1
    child2 = x.child2()
    child1.replace(child2)
    assert node.getchildren()[0] == child2
    assert node.write_xmlstring() == '<node>test<child2/></node>'


def replace_test3():
    """ XML namespace unit test - replace - replace simple node with text after by node

    In:
      - <node><child1/></node>

    Out:
      - <node><child2/></node>
    """
    x = xml.Renderer()

    child1 = x.child1()
    node = x.node(child1, 'test')
    assert node.getchildren()[0] == child1
    child2 = x.child2()
    child1.replace(child2)
    assert node.getchildren()[0] == child2
    assert node.write_xmlstring() == '<node><child2/>test</node>'


def replace_test4():
    """ XML namespace unit test - replace - replace simple node by text

    In:
      - <node><child1/></node>

    Out:
      - <node>test</node>
    """
    x = xml.Renderer()

    child1 = x.child1()
    node = x.node(child1)
    assert node.getchildren()[0] == child1
    child1.replace('test')
    assert node.text == 'test'
    assert node.write_xmlstring() == '<node>test</node>'


def replace_test5():
    """ XML namespace unit test - replace - replace simple node by node + text

    In:
      - <node><child1/></node>

    Out:
      - <node>test<child2/></node>
    """
    x = xml.Renderer()

    child1 = x.child1()
    node = x.node(child1)
    assert node.getchildren()[0] == child1
    child2 = x.child2()
    child1.replace('test', child2)
    assert node.text == 'test'
    assert node.write_xmlstring() == '<node>test<child2/></node>'


def replace_test6():
    """ XML namespace unit test - replace - replace root node

    In:
      - <node/>

    Out:
      - <node/>
    """
    x = xml.Renderer()

    node = x.node()
    node.replace('test')
    assert node.write_xmlstring() == '<node/>'

xml_test1_in = """
    <node xmlns:meld="http://www.plope.com/software/meld3">
    <child meld:id="child"/>
    </node>
"""

def repeat_test1():
    """ XML namespace unit test - repeat - Repeat with 2 simple text, use childname argument"""
    x = xml.Renderer()
    node = x.parse_xmlstring(xml_test1_in)
    iterator = node.repeat(['test1', 'test2'], childname='child')

    for child, value in iterator:
        child.append_text(value)
    assert [child.text for child in node.getchildren()] == ['test1', 'test2']


def repeat_test2():
    """ XML namespace unit test - repeat - Repeat with 2 simple text, don't use childname argument"""
    x = xml.Renderer()
    node = x.parse_xmlstring(xml_test1_in)
    child = node.findmeld('child')
    iterator = child.repeat(['test1', 'test2'])

    for child, value in iterator:
        child.append_text(value)
    assert [child.text for child in node.getchildren()] == ['test1', 'test2']

def repeat_test3():
    """ XML namespace unit test - repeat - findmeld in repeat loop """
    h = xml.Renderer()

    xhtml_tree_2 = '<div xmlns:meld="http://www.plope.com/software/meld3"><ul><li meld:id="entry"><span meld:id="count">count</span></li></ul></div>'

    root = h.parse_xmlstring(xhtml_tree_2, fragment=True)[0]

    for (elem, count) in root.repeat(range(2), 'entry'):
        elem.findmeld('count').fill(count)

    h << root

    assert h.root.write_xmlstring() == '<div xmlns:meld="http://www.plope.com/software/meld3"><ul><li meld:id="entry"><span meld:id="count">0</span></li><li meld:id="entry"><span meld:id="count">1</span></li></ul></div>'

def root_test1():
    """ XML namespace unit test - root - one element """
    x = xml.Renderer()
    x << x.node()

    assert not isinstance(x.root, ListType)


def root_test2():
    """ XML namespace unit test - root - two elements """
    x = xml.Renderer()
    x << x.node()
    x << x.node()

    assert isinstance(x.root, ListType)


def parse_xmlstring_test1():
    """ XML namespace unit test - parse_xmlstring - good encoding """
    try:
        x = xml.Renderer()
        f = open(os.path.join(os.path.dirname(__file__), 'test_xmlns_1.xml'))
        root = x.parse_xmlstring(f.read())
        f.close()
    except UnicodeDecodeError:
        assert False
    else:
        assert True

def parse_xmlstring_test2():
    """ XML namespace unit test - parse_xmlstring - bad encoding """
    try:
        x = xml.Renderer()
        f = open(os.path.join(os.path.dirname(__file__), 'iso-8859.xml'))
        root = x.parse_xml(f, encoding='utf-8')
        f.close()
    except ET.XMLSyntaxError:
        assert True
    else:
        assert False


xml_fragments_1 = """leading_text<fragment1></fragment1>text<fragment2></fragment2>"""
def parse_xmlstring_test3():
    """ XML namespace unit test - parse_xmlstring - parse fragment xml with fragment flag """
    x = xml.Renderer()
    roots = x.parse_xmlstring(xml_fragments_1, fragment=True)
    assert roots[0] == 'leading_text'
    assert roots[1].write_xmlstring() == "<fragment1/>text"
    assert roots[1].tail == "text"
    assert roots[2].write_xmlstring() == "<fragment2/>"


def parse_xmlstring_test4():
    """ XML namespace unit test - parse_xmlstring - parse xml tree with fragment flag """
    x = xml.Renderer()
    roots = x.parse_xmlstring(xml_fragments_1, fragment=True, no_leading_text=True)
    assert roots[0].write_xmlstring() == "<fragment1/>text"
    assert roots[0].tail == "text"
    assert roots[1].write_xmlstring() == "<fragment2/>"


xml_tree_1 = "<a>text</a>"
def parse_xmlstring_test5():
    """ XML namespace unit test - parse_xmlstring - Test parse child type """
    x = xml.Renderer()
    root = x.parse_xmlstring(xml_tree_1)
    assert type(root) == xml._Tag


def parse_xml_test1():
    """ XML namespace unit test - parse_xmlstring - good encoding """
    try:
        x = xml.Renderer()
        root = x.parse_xml(os.path.join(os.path.dirname(__file__), 'test_xmlns_1.xml'))
    except UnicodeDecodeError:
        assert False
    else:
        assert True


def findmeld_test1():
    """ XML namespace unit test - find_meld - one element """
    x = xml.Renderer()
    node = x.parse_xmlstring(xml_test1_in)
    child = node.findmeld('child')

    assert child is not None


def findmeld_test2():
    """ XML namespace unit test - find_meld - zero element """
    x = xml.Renderer()
    node = x.parse_xmlstring("""<node xmlns:meld="http://www.plope.com/software/meld3"></node>""")
    child = node.findmeld('child')
    assert child is None


def findmeld_test3():
    """ XML namespace unit test - find_meld - zero element and default argument """
    x = xml.Renderer()
    node = x.parse_xmlstring("""<node xmlns:meld="http://www.plope.com/software/meld3"></node>""")
    child = node.findmeld('child', 'test')
    assert child == 'test'

# Test for XML namespace

xml_test2_in = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml"
          xmlns:meld="http://www.plope.com/software/meld3"
          xmlns:bar="http://foo/bar">
      <head>
        <meta content="text/html; charset=ISO-8859-1" http-equiv="content-type" />
        <title meld:id="title">This is the title</title>
      </head>
      <body>
        <div/> <!-- empty tag -->
        <div meld:id="content_well">
          <form meld:id="form1" action="." method="POST">
          <table border="0" meld:id="table1">
            <tbody meld:id="tbody">
              <tr>
                <th>Name</th>
                <th>Description</th>
              </tr>
              <tr meld:id="tr" class="foo">
                <td meld:id="td1">Name</td>
                <td meld:id="td2">Description</td>
              </tr>
            </tbody>
          </table>
          <input type="submit" name="next" value=" Next "/>
          </form>
        </div>
      </body>
    </html>"""


def global_test1():
    """ XML namespace unit test - create xml by procedural way """
    x = xml.Renderer()

    filePath = os.path.join(os.path.dirname(__file__), 'helloworld.csv')

    reader = csv.reader(open(filePath, 'r'))

    with x.helloWorlds:
        for row in reader:
            with x.helloWorld(language=row[0].decode('utf-8')):
                x << row[1].decode('utf-8')

    xmlToTest = x.root.write_xmlstring(xml_declaration=True, pretty_print=True).strip()

    f = open(os.path.join(os.path.dirname(__file__), 'test_xmlns_1.xml'))
    xmlToCompare = f.read()
    f.close()
    assert xmlToTest == xmlToCompare


def global_test2():
    """ XML namespace unit test - create xml by functionnal way """
    x = xml.Renderer()

    filePath = os.path.join(os.path.dirname(__file__), 'helloworld.csv')

    reader = csv.reader(open(filePath, 'r'))

    root = x.helloWorlds([x.helloWorld(row[1].decode('utf-8'),
                            {'language':row[0].decode('utf-8')}) for row in reader])

    xmlToTest = root.write_xmlstring(xml_declaration=True, pretty_print=True).strip()

    f = open(os.path.join(os.path.dirname(__file__), 'test_xmlns_1.xml'))
    xmlToCompare = f.read()
    f.close()
    assert xmlToTest == xmlToCompare


def global_test3():
    """ XML namespace unit test - test parse_xmlstring method """
    x = xml.Renderer()

    f = open(os.path.join(os.path.dirname(__file__), 'test_xmlns_1.xml'))
    root = x.parse_xmlstring(f.read())
    f.close()

    xmlToTest = root.write_xmlstring(xml_declaration=True, pretty_print=True).strip()

    f = open(os.path.join(os.path.dirname(__file__), 'test_xmlns_1.xml'))
    xmlToCompare = f.read()
    f.close()
    assert xmlToTest == xmlToCompare


def global_test4():
    """ XML namespace unit test - meld3 - test findmeld with children affectation """

    x = xml.Renderer()
    root = x.parse_xmlstring(xml_test2_in)

    root.findmeld('title').text = 'My document'
    root.findmeld('form1').set('action', './handler')
    data = (
        {'name':'Girls',
         'description':'Pretty'},
        {'name':'Boys',
         'description':'Ugly'},
        )

    iterator = root.findmeld('tr').repeat(data)
    for element, item in iterator:
        td1 = element.findmeld('td1')
        td1.text = item['name']
        element.findmeld('td2').text = item['description']

    assert [elt.text for elt in root.xpath('.//x:td', namespaces={ 'x' : 'http://www.w3.org/1999/xhtml'})] == ['Girls', 'Pretty', 'Boys', 'Ugly']
    assert root[0][1].text == 'My document'
    assert root.xpath('.//x:form', namespaces={ 'x' : 'http://www.w3.org/1999/xhtml'})[0].attrib['action'] == './handler'


def global_test5():
    """ XML namespace unit test - meld3 - test findmeld & replace method """
    x = xml.Renderer()
    root = x.parse_xmlstring(xml_test2_in)

    root.findmeld('title').text = 'My document'
    root.findmeld('form1').set('action', './handler')

    data = (
        {'name':'Girls',
         'description':'Pretty'},
        {'name':'Boys',
         'description':'Ugly'},
        )

    children = []
    for elt in data:
        children.append(x.tr([x.td(elt['name']), x.td(elt['description'])], {'class':'bar'}))

    root.findmeld('tr').replace(children)

    assert root.findall('.//tr')[1].attrib['class'] == 'bar'
    assert [elt.text for elt in root.xpath('.//td')] == ['Girls', 'Pretty', 'Boys', 'Ugly']


def global_test6():
    """ XML namespace unit test - meld3 - test option write_xmlstring method with option pipeline=False """
    x = xml.Renderer()
    root = x.parse_xmlstring(xml_test2_in)

    root.findmeld('title').text = 'My document'
    root.findmeld('form1').set('action', './handler')

    data = (
        {'name':'Girls',
         'description':'Pretty'},
        {'name':'Boys',
         'description':'Ugly'},
        )

    children = []
    for elt in data:
        children.append(x.tr([x.td(elt['name']), x.td(elt['description'])], {'class':'bar'}))

    root.findmeld('tr').replace(children)

    root.write_xmlstring(xml_declaration=True, pretty_print=True, pipeline=False).strip()

    assert root.findmeld('tr') is None
    assert root.findmeld('content_well') is None


def global_test7():
    """ XML namespace unit test - meld3 - test option write_xmlstring method with option pipeline=True """
    x = xml.Renderer()
    root = x.parse_xmlstring(xml_test2_in)

    root.findmeld('title').text = 'My document'
    root.findmeld('form1').set('action', './handler')

    data = (
        {'name':'Girls',
         'description':'Pretty'},
        {'name':'Boys',
         'description':'Ugly'},
        )

    children = []
    for elt in data:
        children.append(x.tr([x.td(elt['name']), x.td(elt['description'])], {'class':'bar'}))

    root.findmeld('tr').replace(children)

    root.write_xmlstring(xml_declaration=True, pretty_print=True, pipeline=False).strip()

    assert root.findmeld('tr') is None
    assert root.findmeld('content_well') is None


def global_test8():
    """ XML namespace unit test - create xml """
    x = xml.Renderer()
    x.namespaces = {'meld':'http://www.plope.com/software/meld3'}
    data = (
        {'name':'Girls',
         'description':'Pretty'},
        {'name':'Boys',
         'description':'Ugly'},
        )

    with x.html:
        with x.head:
            with x.meta:
                x << {'content':'text/html; charset=ISO-8859-1', 'http-equiv':'content-type'}
            with x.title.meld_id('title'):
                x << 'My document'
        with x.body:
            with x.div:
                pass
            x << x.comment(' empty tag ')
            with x.div:
                with x.form.meld_id('form1'):
                    x << {'action':'./handler'}
                    with x.table:
                        with x.tbody:
                            with x.tr:
                                x << x.th('Name') << x.th('Description')
                            for elt in data:
                                with x.tr.meld_id('tr'):
                                    x << x.td(elt['name']).meld_id('td') << x.td(elt['description']).meld_id('td')
                    with x.input:
                        x << {'type':'submit', 'name':'next', 'value': ' Next '}

    assert [elt.text for elt in x.root.xpath('.//td')] == ['Girls', 'Pretty', 'Boys', 'Ugly']
    assert x.root[0][1].text == 'My document'
    assert x.root.xpath('.//form')[0].attrib['action'] == './handler'

