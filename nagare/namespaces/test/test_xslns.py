#--
# Copyright (c) 2008-2013 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from __future__ import with_statement

from nagare.namespaces import xsl
from nagare.namespaces import xhtml


def test2():
    """ XSL namespace unit test - simple xsl transformation 2 """
    x = xsl.Renderer()
    x.namespaces = {'xsl': 'http://www.w3.org/1999/XSL/Transform'}
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
