# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import unittest

from lxml import etree as ET
from webob import Request, Response

from nagare.namespaces import xhtml
from nagare import top


class TestTop(unittest.TestCase):
    def setUp(self):
        response = Response()
        response.xml_output = False
        self.h = xhtml.Renderer(request=Request({'PATH_INFO': ''}), response=response)

    def check_html(self, html):
        html2 = top.wrap('text/html', self.h, self.h.root)
        if not isinstance(html2, list):
            html2 = [html2]
        html2 = ''.join(map(ET.tostring, html2))

        self.assertEqual(html2, html)

    # Without <html>. Without <head>. Without <body>

    def test_1(self):
        self.h << 'hello'
        self.check_html('<html><head/><body>hello</body></html>')

    def test_2(self):
        h = self.h

        h << h.comment('c1') << 'hello' << h.comment('c2')
        self.check_html('<html><head/><body><!--c1-->hello<!--c2--></body></html>')

    def test_3(self):
        h = self.h

        h << h.p('hello')
        self.check_html('<html><head/><body><p>hello</p></body></html>')

    def test_4(self):
        h = self.h

        h << h.comment('c1') << h.p('hello') << h.comment('c2') << h.p('world') << h.comment('c3')
        self.check_html('<html><head/><body><!--c1--><p>hello</p><!--c2--><p>world</p><!--c3--></body></html>')

    # Without <html>. Without <head>. With <body>

    def test_5(self):
        h = self.h

        h << h.body('hello')
        self.check_html('<html><head/><body>hello</body></html>')

    def test_6(self):
        h = self.h

        h << h.comment('c1') << h.body('hello') << h.comment('c2')
        self.check_html('<html><head/><!--c1--><body>hello</body><!--c2--></html>')

    def test_7(self):
        h = self.h

        h << h.body(h.p('hello'))
        self.check_html('<html><head/><body><p>hello</p></body></html>')

    def test_8(self):
        h = self.h

        h << h.comment('c1') << h.body(h.p('hello')) << h.comment('c2')
        self.check_html('<html><head/><!--c1--><body><p>hello</p></body><!--c2--></html>')

    # Without <html>. With <head>. Without <body>

    def test_9(self):
        h = self.h

        h << h.head.head
        self.check_html('<html><head/><body/></html>')

    def test_10(self):
        h = self.h

        h << h.comment('c1') << h.head.head << h.comment('c2')
        self.check_html('<html><!--c1--><head/><body><!--c2--></body></html>')

    def test_11(self):
        h = self.h

        h << h.head.head << 'hello'
        self.check_html('<html><head/>hello<body/></html>')

    def test_12(self):
        h = self.h

        h << h.comment('c1') << h.head.head << h.p('hello') << h.comment('c2')
        self.check_html('<html><!--c1--><head/><body><p>hello</p><!--c2--></body></html>')

    def test_13(self):
        h = self.h

        h << h.comment('c1') << h.head.head << h.comment('c2') << h.p('hello') << h.comment('c3')
        self.check_html('<html><!--c1--><head/><body><!--c2--><p>hello</p><!--c3--></body></html>')

    # Without <html>. With <head>. With <body>

    def test_14(self):

        h = self.h

        h << h.head.head << h.body
        self.check_html('<html><head/><body/></html>')

    def test_15(self):
        h = self.h

        h << h.comment('c1') << h.head.head << h.comment('c2') << h.body << h.comment('c3')
        self.check_html('<html><!--c1--><head/><!--c2--><body/><!--c3--></html>')

    def test_16(self):
        h = self.h

        h << h.head.head << 'hello' << h.body << 'world'
        self.check_html('<html><head/>hello<body/>world</html>')

    def test_17(self):
        h = self.h

        h << h.comment('c1') << h.head.head << h.p('hello') << h.comment('c2') << h.body('world') << h.comment('c3')
        self.check_html('<html><!--c1--><head/><p>hello</p><!--c2--><body>world</body><!--c3--></html>')

    # With <html>. Without <head>. Without <body>

    def test_18(self):
        h = self.h
        h << h.html << 'hello'
        self.check_html('<html><head/><body/></html>hello')

    def test_19(self):
        h = self.h

        h << h.comment('c1') << h.html << 'hello' << h.comment('c2')
        self.check_html('<!--c1--><html><head/><body/></html>hello<!--c2-->')

    def test_20(self):
        h = self.h

        with h.html:
            h << h.p('hello')

        self.check_html('<html><head/><body><p>hello</p></body></html>')

    def test_21(self):
        h = self.h

        with h.html:
            h << h.comment('c1') << h.p('hello') << h.comment('c2') << h.p('world') << h.comment('c3')

        self.check_html('<html><head/><body><!--c1--><p>hello</p><!--c2--><p>world</p><!--c3--></body></html>')

    # With <html>. Without <head>. With <body>

    def test_22(self):
        h = self.h

        with h.html:
            h << h.body('hello')
        self.check_html('<html><head/><body>hello</body></html>')

    def test_23(self):
        h = self.h

        with h.html:
            h << h.comment('c1') << h.body('hello') << h.comment('c2')
        self.check_html('<html><head/><!--c1--><body>hello</body><!--c2--></html>')

    def test_24(self):
        h = self.h

        with h.html:
            h << h.body(h.p('hello'))
        self.check_html('<html><head/><body><p>hello</p></body></html>')

    def test_25(self):
        h = self.h

        with h.html:
            h << h.comment('c1') << h.body(h.p('hello')) << h.comment('c2')
        self.check_html('<html><head/><!--c1--><body><p>hello</p></body><!--c2--></html>')

    # With <html>. With <head>. Without <body>

    def test_26(self):
        h = self.h

        with h.html:
            h << h.head.head
        self.check_html('<html><head/><body/></html>')

    def test_27(self):
        h = self.h

        with h.html:
            h << h.comment('c1') << h.head.head << h.comment('c2')
        self.check_html('<html><!--c1--><head/><body><!--c2--></body></html>')

    def test_28(self):
        h = self.h

        with h.html:
            h << h.head.head << 'hello'
        self.check_html('<html><head/>hello<body/></html>')

    def test_29(self):
        h = self.h

        with h.html:
            h << h.comment('c1') << h.head.head << h.p('hello') << h.comment('c2')
        self.check_html('<html><!--c1--><head/><body><p>hello</p><!--c2--></body></html>')

    def test_30(self):
        h = self.h

        with h.html:
            h << h.comment('c1') << h.head.head << h.comment('c2') << h.p('hello') << h.comment('c3')
        self.check_html('<html><!--c1--><head/><body><!--c2--><p>hello</p><!--c3--></body></html>')

    # With <html>. With <head>. With <body>

    def test_31(self):
        h = self.h

        with h.html:
            h << h.head.head << h.body
        self.check_html('<html><head/><body/></html>')

    def test_32(self):
        h = self.h

        with h.html:
            h << h.comment('c1') << h.head.head << h.comment('c2') << h.body << h.comment('c3')
        self.check_html('<html><!--c1--><head/><!--c2--><body/><!--c3--></html>')

    def test_33(self):
        h = self.h

        with h.html:
            h << h.head.head << 'hello' << h.body << 'world'
        self.check_html('<html><head/>hello<body/>world</html>')

    def test_34(self):
        h = self.h

        with h.html:
            h << h.comment('c1') << h.head.head << h.p('hello') << h.comment('c2') << h.body('world') << h.comment('c3')
        self.check_html('<html><!--c1--><head/><p>hello</p><!--c2--><body>world</body><!--c3--></html>')

    # ---

    def test_35(self):
        h = self.h

        h.head << h.head.title('hello')
        h << h.p('world')
        self.check_html('<html><head><title>hello</title></head><body><p>world</p></body></html>')

    def test_36(self):
        h = self.h

        h.head << h.head.title('hello')
        h << h.head.head(h.head.title('world')) << h.p('foo')
        self.check_html('<html><head><title>world</title><title>hello</title></head><body><p>foo</p></body></html>')

    def test_37(self):
        h = self.h

        h.head << h.head.head(id='header_id')
        h << h.head.head(class_='header_class') << h.p('foo')
        self.check_html('<html><head class="header_class" id="header_id"/><body><p>foo</p></body></html>')

    # ---

    def test_38(self):
        h = self.h

        h << h.processing_instruction('hello') << h.p('foo') << h.processing_instruction('world')
        self.check_html('<html><head/><body><?hello ?><p>foo</p><?world ?></body></html>')

    def test_39(self):
        h = self.h

        h << h.processing_instruction('hello') << h.html(h.p('foo'))
        self.check_html('<?hello ?><html><head/><body><p>foo</p></body></html>')

    def test_canonical(self):
        h = xhtml.Renderer(request=Request({'PATH_INFO': ''}), response=self.h.response)
        self.assertEqual(top.wrap('text/html', h, h.root).write_xmlstring(), '<html><head/><body></body></html>')

        h = xhtml.Renderer(request=Request({'PATH_INFO': ''}), response=self.h.response)
        h.head << h.head.link(rel='canonical', href='/bar')
        self.assertEqual(top.wrap('text/html', h, h.root).write_xmlstring(), '<html><head><link href="/bar" rel="canonical"/></head><body></body></html>')

        h = xhtml.Renderer(request=Request({'PATH_INFO': '/foo'}), response=self.h.response)
        self.assertEqual(top.wrap('text/html', h, h.root).write_xmlstring(), '<html><head><link href="/foo" rel="canonical"/></head><body></body></html>')

        h = xhtml.Renderer(request=Request({'PATH_INFO': '/foo'}), response=self.h.response)
        h.head << h.head.link(rel='canonical', href='/bar')
        self.assertEqual(top.wrap('text/html', h, h.root).write_xmlstring(), '<html><head><link href="/bar" rel="canonical"/></head><body></body></html>')
