#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""XSL renderer"""

from __future__ import with_statement

from nagare.namespaces import xml
from nagare.namespaces.xml import TagProp

# ----------------------------------------------------------------------------------

class Renderer(xml.XmlRenderer):
    """ The XSL renderer
    """

    content_type = 'text/xsl'

    # The XSL tags
    # ------------

    apply_imports = TagProp('apply-imports', set())
    apply_templates = TagProp('apply-templates', set(('select', 'mode')))
    attribute = TagProp('attribute', set(('name', 'namespace')))
    attribute_set = TagProp('attribute-set', set(('name', 'use-attribute-sets')))
    call_template = TagProp('call-template', set(('name',)))
    choose = TagProp('choose', set())
    comment = TagProp('comment', set())
    copy = TagProp('copy', set(('use-attribute-sets',)))
    copy_of = TagProp('copy-of', set(('select',)))
    decimal_format = TagProp('decimal-format', set(('name', 'decimal-separator', 'grouping-separator', 'infinity',
                                                     'minus-sign', 'NaN', 'percent', 'per-mille', 'zero-digit',
                                                     'pattern-separator')))
    element = TagProp('element', set(('name', 'namespace', 'use-attribute-sets')))
    fallback = TagProp('fallback', set(('select',)))
    if_ = TagProp('if', set(('test',)))
    import_ = TagProp('import', set(('href',)))
    include = TagProp('include', set(('href',)))
    for_each = TagProp('for-each', set(('select',)))
    key = TagProp('key', set(('name', 'match', 'use')))
    message = TagProp('message', set(('terminate',)))
    namespace_alias = TagProp('namespace-alias', set(('stylesheet-prefix',)))
    number = TagProp('number', set(('level', 'count', 'from', 'value', 'format',
                                    'lang', 'letter-value', 'grouping-separator',
                                    'grouping-size')))
    otherwise = TagProp('otherwise', set())
    output = TagProp('output', set(('method', 'version', 'encoding',
                                    'omit-xml-declaration', 'standalone',
                                    'doctype-public', 'doctype-system',
                                    'cdata-section-elements', 'indent',
                                    'media-type')))
    param = TagProp('param', set(('name', 'select')))
    preserve_space = TagProp('preserve-space', set(('elements',)))
    processing_instruction = TagProp('processing-instruction', set(('name',)))
    sort = TagProp('sort', set(('select', 'lang', 'data-type', 'order', 'case-order')))
    strip_space = TagProp('strip-space', set(('elements',)))
    stylesheet = TagProp('stylesheet', set(('version', 'id',
                                            'extension-element-prefixes',
                                            'exclude-result-prefixes')))
    template = TagProp('template', set(('match', 'name', 'priority', 'mode')))
    transform = TagProp('transform', set(('version', 'id',
                                            'extension-element-prefixes',
                                            'exclude-result-prefixes')))
    text = TagProp('text', set())
    value_of = TagProp('value-of', set(('select', 'disable-output-escaping')))
    variable = TagProp('variable', set(('name', 'select')))
    when = TagProp('when', set(('test',)))
    with_param = TagProp('with-param', set(('name', 'select')))

# ----------------------------------------------------------------------------------

"""
<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="utf-8"/>
  <xsl:template match="/">
    <xsl:copy-of select="."/>
  </xsl:template>
</xsl:transform>
"""

if __name__ == '__main__':
    from nagare.namespaces import xhtml

    x = Renderer()
    x.namespaces = { 'xsl' : 'http://www.w3.org/1999/XSL/Transform' }
    x.default_namespace = 'xsl'

    xsl = x.stylesheet(
        x.output(encoding="utf-8"),
        x.template(
            x.copy_of(select="."), match="/"
        )
    )

    print xsl.write_xmlstring(xml_declaration=True, pretty_print=True)

    h = xhtml.Renderer()

    page = h.html(h.h1('Hello'), h.h2('world'))

    print page.write_xmlstring(pretty_print=True)

    r = page.getroottree().xslt(xsl)

    print str(r)
    print
