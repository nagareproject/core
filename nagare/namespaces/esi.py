#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Edge Server-side Include renderer"""

from lxml import etree as ET

from nagare.namespaces import xml
from nagare.namespaces.xml import TagProp

# Official ESI namespace
NS = 'http://www.edge-delivery.org/esi/1.0'

class Renderer(xml.XmlRenderer):
    """ The ESI renderer
    """

    # The ESI tags
    # ------------

    include = TagProp('include', set(('src', 'alt', 'onerror')))
    inline = TagProp('inline', set(('name', 'fetchable')))
    choose = TagProp('choose', set())
    when = TagProp('when', set(('test',)))
    otherwise = TagProp('otherwise', set())
    try_ = TagProp('try', set())
    attempt = TagProp('attempt', set())
    except_ = TagProp('except', set())
    comment = TagProp('comment', set(('text',)))
    remove = TagProp('remove', set())
    vars = TagProp('vars', set())

    def esi(self, text):
        """Generate a ``esi`` comment element

        In:
          - ``text`` -- comment text

        Return:
          - the comment element
        """
        return ET.Comment('esi ' + text)

if __name__ == '__main__':
    from nagare.namespaces import xhtml

    h = xhtml.Renderer()
    s = Renderer()
    s.namespaces= { 'esi' : NS }
    s.default_namespace = 'esi'

    html = h.html(h.body(h.h1('hello'), s.include(dict(src='http://www.net-ng.com'), s.include(src='http://www.net-ng.com')), h.p('world')))

    print html.write_xmlstring(pretty_print=True)

