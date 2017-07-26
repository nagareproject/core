# Encoding: utf-8

# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import unittest

from lxml import etree

from nagare.namespaces import xml, xhtml
from nagare.serializer import serialize


class TestSerializer(unittest.TestCase):
    def test_html(self):
        h = xhtml.Renderer()

        r = serialize(h.p('hello'), 'text/html', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/html', '<p>hello</p>\n'))
        r = serialize(h.p(u'été'), 'text/html', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/html', '<p>\xc3\xa9t\xc3\xa9</p>\n'))
        r = serialize(h.p('hello'), 'text/html', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/html', '<!DOCTYPE html>\n<p>hello</p>\n'))

    def test_xhtml(self):
        h = xhtml.Renderer()

        r = serialize(h.p('hello'), 'application/xhtml+xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('application/xhtml+xml', '<p>hello</p>'))
        r = serialize(h.p(u'été'), 'application/xhtml+xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('application/xhtml+xml', '<p>\xc3\xa9t\xc3\xa9</p>'))
        r = serialize(h.p('hello'), 'application/xhtml+xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('application/xhtml+xml', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<p>hello</p>"))

    def test_xml(self):
        x = xml.Renderer()

        r = serialize(x.person('hello'), 'text/xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/xml', '<person>hello</person>'))
        r = serialize(x.person(u'été'), 'text/xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/xml', '<person>\xc3\xa9t\xc3\xa9</person>'))
        r = serialize(x.person('hello'), 'text/xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/xml', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<person>hello</person>"))

    def test_comment(self):
        x = xml.Renderer()

        r = serialize(x.comment('hello'), 'text/xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/xml', '<!--hello-->'))
        r = serialize(x.comment(u'été'), 'text/xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/xml', '<!--\xc3\xa9t\xc3\xa9-->'))
        r = serialize(x.comment('hello'), 'text/xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/xml', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<!--hello-->"))

    def test_pi(self):
        x = xml.Renderer()

        r = serialize(x.processing_instruction('hello'), 'text/xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/xml', '<?hello ?>'))
        r = serialize(x.processing_instruction(u'été'), 'text/xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/xml', '<?\xc3\xa9t\xc3\xa9 ?>'))
        r = serialize(x.processing_instruction('hello'), 'text/xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/xml', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<?hello ?>"))

    def test_etree(self):
        e = etree.Element('person')
        e.text = 'hello'
        r = serialize(e, 'text/xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/xml', '<person>hello</person>'))
        e = etree.Element('person')
        e.text = u'été'
        r = serialize(e, 'text/xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/xml', '<person>\xc3\xa9t\xc3\xa9</person>'))
        e = etree.Element('person')
        e.text = 'hello'
        r = serialize(e, 'text/xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/xml', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<person>hello</person>"))

    def test_str(self):
        r = serialize('hello world', 'text/msg', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/msg', 'hello world'))
        r = serialize(u'été'.encode('utf-8'), 'text/msg', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/msg', '\xc3\xa9t\xc3\xa9'))
        r = serialize('hello world', 'text/msg', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/msg', 'hello world'))
        r = serialize('hello world', '', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/plain', 'hello world'))
        r = serialize(u'été'.encode('utf-8'), '', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/plain', '\xc3\xa9t\xc3\xa9'))
        r = serialize('hello world', '', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/plain', 'hello world'))

    def test_unicode(self):
        r = serialize(u'hello world', 'text/msg', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/msg', 'hello world'))
        r = serialize(u'été', 'text/msg', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/msg', '\xc3\xa9t\xc3\xa9'))
        r = serialize(u'hello world', 'text/msg', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/msg', 'hello world'))
        r = serialize(u'hello world', '', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/plain', 'hello world'))
        r = serialize(u'été', '', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/plain', '\xc3\xa9t\xc3\xa9'))
        r = serialize(u'hello world', '', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/plain', 'hello world'))

    def test_list(self):
        h = xhtml.Renderer()
        x = xml.Renderer()

        e = etree.Element('person')
        e.text = 'hello'

        l = [h.p('hello'), x.person('hello'), x.comment('hello'), x.processing_instruction('hello'), e, 'hello', u'hello']

        r = serialize(l, 'text/html', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/html', '<p>hello</p>\n<person>hello</person>\n<!--hello-->\n<?hello >\n<person>hello</person>\nhellohello'))
        r = serialize(l, 'text/html', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/html', '<!DOCTYPE html>\n<p>hello</p>\n<person>hello</person>\n<!--hello-->\n<?hello >\n<person>hello</person>\nhellohello'))

        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('application/xhtml+xml', '<p>hello</p><person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello'))
        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('application/xhtml+xml', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<p>hello</p><person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello"))

        r = serialize(l, 'text/msg', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/msg', '<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello'))
        r = serialize(l, 'text/msg', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/msg', '<!DOCTYPE html>\n<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello'))

        r = serialize(l, '', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('', '<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello'))
        r = serialize(l, '', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('', '<!DOCTYPE html>\n<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello'))

        l = l[1:] + [l[0]]
        r = serialize(l, 'text/html', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/html', '<person>hello</person>\n<!--hello-->\n<?hello >\n<person>hello</person>\nhellohello<p>hello</p>\n'))
        r = serialize(l, 'text/html', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/html', '<!DOCTYPE html>\n<person>hello</person>\n<!--hello-->\n<?hello >\n<person>hello</person>\nhellohello<p>hello</p>\n'))

        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('application/xhtml+xml', '<person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p>'))
        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('application/xhtml+xml', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p>"))

        r = serialize(l, 'text/msg', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/msg', "<person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p>\n"))
        r = serialize(l, 'text/msg', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/msg', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p>\n"))

        r = serialize(l, '', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('', '<person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p>\n'))
        r = serialize(l, '', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p>\n"))

        l = l[1:] + [l[0]]
        r = serialize(l, 'text/html', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/html', '<!--hello-->\n<?hello >\n<person>hello</person>\nhellohello<p>hello</p>\n<person>hello</person>\n'))
        r = serialize(l, 'text/html', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/html', '<!DOCTYPE html>\n<!--hello-->\n<?hello >\n<person>hello</person>\nhellohello<p>hello</p>\n<person>hello</person>\n'))

        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('application/xhtml+xml', '<!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p><person>hello</person>'))
        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('application/xhtml+xml', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p><person>hello</person>"))

        r = serialize(l, 'text/msg', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/msg', '<!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p>\n<person>hello</person>'))
        r = serialize(l, 'text/msg', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/msg', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p>\n<person>hello</person>"))

        r = serialize(l, '', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('', '<!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p>\n<person>hello</person>'))
        r = serialize(l, '', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<!--hello--><?hello ?><person>hello</person>hellohello<p>hello</p>\n<person>hello</person>"))

        l = l[1:] + [l[0]]
        r = serialize(l, 'text/html', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/html', '<?hello >\n<person>hello</person>\nhellohello<p>hello</p>\n<person>hello</person>\n<!--hello-->\n'))
        r = serialize(l, 'text/html', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/html', '<!DOCTYPE html>\n<?hello >\n<person>hello</person>\nhellohello<p>hello</p>\n<person>hello</person>\n<!--hello-->\n'))

        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('application/xhtml+xml', '<?hello ?><person>hello</person>hellohello<p>hello</p><person>hello</person><!--hello-->'))
        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('application/xhtml+xml', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<?hello ?><person>hello</person>hellohello<p>hello</p><person>hello</person><!--hello-->"))

        r = serialize(l, 'text/msg', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/msg', '<?hello ?><person>hello</person>hellohello<p>hello</p>\n<person>hello</person><!--hello-->'))
        r = serialize(l, 'text/msg', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/msg', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<?hello ?><person>hello</person>hellohello<p>hello</p>\n<person>hello</person><!--hello-->"))

        r = serialize(l, '', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('', '<?hello ?><person>hello</person>hellohello<p>hello</p>\n<person>hello</person><!--hello-->'))
        r = serialize(l, '', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<?hello ?><person>hello</person>hellohello<p>hello</p>\n<person>hello</person><!--hello-->"))

        l = l[1:] + [l[0]]
        r = serialize(l, 'text/html', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/html', '<person>hello</person>\nhellohello<p>hello</p>\n<person>hello</person>\n<!--hello-->\n<?hello >\n'))
        r = serialize(l, 'text/html', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/html', '<!DOCTYPE html>\n<person>hello</person>\nhellohello<p>hello</p>\n<person>hello</person>\n<!--hello-->\n<?hello >\n'))

        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('application/xhtml+xml', '<person>hello</person>hellohello<p>hello</p><person>hello</person><!--hello--><?hello ?>'))
        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('application/xhtml+xml', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<person>hello</person>hellohello<p>hello</p><person>hello</person><!--hello--><?hello ?>"))

        r = serialize(l, 'text/msg', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/msg', '<person>hello</person>hellohello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?>'))
        r = serialize(l, 'text/msg', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/msg', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<person>hello</person>hellohello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?>"))

        r = serialize(l, '', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('', '<person>hello</person>hellohello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?>'))
        r = serialize(l, '', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('', "<?xml version='1.0' encoding='utf-8'?>\n<!DOCTYPE html>\n<person>hello</person>hellohello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?>"))

        l = l[1:] + [l[0]]
        r = serialize(l, 'text/html', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/html', 'hellohello<p>hello</p>\n<person>hello</person>\n<!--hello-->\n<?hello >\n<person>hello</person>\n'))
        r = serialize(l, 'text/html', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/html', 'hellohello<p>hello</p>\n<person>hello</person>\n<!--hello-->\n<?hello >\n<person>hello</person>\n'))

        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('application/xhtml+xml', 'hellohello<p>hello</p><person>hello</person><!--hello--><?hello ?><person>hello</person>'))
        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('application/xhtml+xml', 'hellohello<p>hello</p><person>hello</person><!--hello--><?hello ?><person>hello</person>'))

        r = serialize(l, 'text/msg', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/msg', 'hellohello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>'))
        r = serialize(l, 'text/msg', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/msg', 'hellohello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>'))

        r = serialize(l, '', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('', 'hellohello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>'))
        r = serialize(l, '', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('', 'hellohello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>'))

        l = l[1:] + [l[0]]
        r = serialize(l, 'text/html', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/html', 'hello<p>hello</p>\n<person>hello</person>\n<!--hello-->\n<?hello >\n<person>hello</person>\nhello'))
        r = serialize(l, 'text/html', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/html', 'hello<p>hello</p>\n<person>hello</person>\n<!--hello-->\n<?hello >\n<person>hello</person>\nhello'))

        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('application/xhtml+xml', 'hello<p>hello</p><person>hello</person><!--hello--><?hello ?><person>hello</person>hello'))
        r = serialize(l, 'application/xhtml+xml', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('application/xhtml+xml', 'hello<p>hello</p><person>hello</person><!--hello--><?hello ?><person>hello</person>hello'))

        r = serialize(l, 'text/msg', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('text/msg', 'hello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>hello'))
        r = serialize(l, 'text/msg', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('text/msg', 'hello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>hello'))

        r = serialize(l, '', '<!DOCTYPE html>', False)
        self.assertEqual(r, ('', 'hello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>hello'))
        r = serialize(l, '', '<!DOCTYPE html>', True)
        self.assertEqual(r, ('', 'hello<p>hello</p>\n<person>hello</person><!--hello--><?hello ?><person>hello</person>hello'))
