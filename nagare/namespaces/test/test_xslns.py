#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from __future__ import with_statement

import os

from nagare.namespaces import xsl
from nagare.namespaces import xml
from nagare.namespaces import xhtml


def test1():
    """ XSL namespace unit test - simple xsl transformation 1 """
    x = xsl.Renderer()
    x.namespaces = { 'xsl' : 'http://www.w3.org/1999/XSL/Transform' }
    x.default_namespace = 'xsl'

    styleSheet = x.stylesheet(
        x.output(encoding="utf-8", method="html"),
        x.template(x.copy(x.apply_templates(select="@*|node()")), match="@*|node()"),
        x.template(x.element(name="head"),
                   x.element(x.element(x.apply_templates(select="@*|node()"), name="body"), name="html"),
                   match="helloWorlds"),
        x.template(x.element(x.value_of(select="@language"), ' : ', x.value_of(select="."), name="h1"), match="helloWorld")
    )

    x = xml.Renderer()

    f = open(os.path.join(os.path.dirname(__file__), 'test_xmlns_1.xml'))
    root = x.parse_xmlstring(f.read())
    f.close()

    r = root.getroottree().xslt(styleSheet)

    f = open(os.path.join(os.path.dirname(__file__), 'helloworld.html'))
    xmlToCompare = f.read()
    f.close()

    assert r.__str__().strip() == xmlToCompare


def test2():
    """ XSL namespace unit test - simple xsl transformation 2 """
    x = xsl.Renderer()
    x.namespaces = { 'xsl' : 'http://www.w3.org/1999/XSL/Transform' }
    x.default_namespace = 'xsl'

    styleSheet = x.stylesheet(
        x.output(encoding="utf-8"),
        x.template(
            x.copy_of(select="."), match="/"
        )
    )

    h = xhtml.Renderer()

    page = h.html(h.h1('Hello'), h.h2('World'))

    r = page.getroottree().xslt(styleSheet)

    assert r.xpath('//html/h1')[0].text == 'Hello'
    assert r.xpath('//html/h2')[0].text == 'World'
