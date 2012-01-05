#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The XHTML renderer

This renderer only depends of the ``nagare.namespaces.xml`` module.
Having not dependencies to the framework make it suitable to be used in others frameworks.
"""

from __future__ import with_statement

import cStringIO, urllib

from lxml import etree as ET

from nagare.namespaces import xml
from nagare.namespaces.xml import TagProp

# ---------------------------------------------------------------------------

# Common attributes
# -----------------

componentattrs = ('id', 'class', 'style', 'title')
i18nattrs = ('lang', 'dir')
eventattrs = ('onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmousemove', 'onmouseover', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup')
allattrs = componentattrs + i18nattrs + eventattrs
focusattrs = ('accesskey', 'tabindex', 'onfocus', 'onblur')

class _HTMLTag(xml._Tag):
    """A xhtml tag
    """
    def write_htmlstring(self, encoding='utf-8', pipeline=True, **kw):
        """Serialize in XHTML the tree beginning at this tag

        In:
          - ``encoding`` -- encoding of the XML
          - ``pipeline`` -- if False, the ``meld:id`` attributes are deleted

        Return:
          - the XHTML
        """
        if not pipeline:
            for element in self.xpath('.//*[@meld:id]', namespaces={ 'meld' : xml._MELD_NS }):
                del element.attrib[xml._MELD_ID]

        return ET.tostring(self, encoding=encoding, method='html', **kw)

    def error(self, err):
        """Decorate this tag with an error message

        Forward the call to the renderer ``decorate_error()`` method

        In:
          - ``err`` -- the message

        Return:
          - a tree
        """
        return self.renderer.decorate_error(self, err)


class HeadRenderer(xml.XmlRenderer):
    """The XHTML head Renderer

    This renderer knows about the possible tags of a html ``<head>``
    """

    # Tag factories
    # -------------

    base = TagProp('base', set(('id', 'href', 'target')))
    head = TagProp('head', set(i18nattrs+('id', 'profile')))
    link = TagProp('link', set(allattrs+('charset', 'href', 'hreflang', 'type', 'rel', 'rev', 'media', 'target')))
    meta = TagProp('meta', set(i18nattrs+('id', 'http_equiv', 'name', 'content', 'scheme')))
    title = TagProp('title', set(i18nattrs+('id',)))
    style = TagProp('style', set(i18nattrs+('id',)))
    script = TagProp('script', set(i18nattrs+('id',)))

    @classmethod
    def class_init(cls, specialTags):
        """Class initialisation

        In:
          -- ``special_tags`` -- tags that have a special factory
        """
        # Create a XML parser that generate ``_HTMLTag`` nodes
        cls._xml_parser = ET.XMLParser()
        cls._xml_parser.setElementClassLookup(ET.ElementDefaultClassLookup(element=_HTMLTag))


class Renderer(xml.XmlRenderer):
    head_renderer_factory = HeadRenderer

    componentattrs = ('id', 'class', 'style', 'title')
    i18nattrs = ('lang', 'dir')
    eventattrs = ('onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmousemove', 'onmouseover', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup')
    focusattrs = ('accesskey', 'tabindex', 'onfocus', 'onblur')
    cellhalignattrs = ('align', 'char', 'charoff')
    cellvalignattrs = ('valign',)
    allattrs = componentattrs + i18nattrs + eventattrs

    # The HTML tags
    # -------------

    a = TagProp('a', set(allattrs+focusattrs+('charset', 'type', 'name', 'href', 'hreflang', 'rel', 'rev', 'shape', 'coords', 'target', 'oncontextmenu')))
    abbr = TagProp('abbr', set(allattrs))
    acronym = TagProp('acronym', set(allattrs))
    address = TagProp('address', set(allattrs))
    applet = TagProp('applet', set(componentattrs+('codebase', 'archive', 'code', 'object', 'alt', 'name', 'width'
                                                                  'height', 'align', 'hspace', 'vspace')))
    area = TagProp('area', set(allattrs + focusattrs + ('shape', 'coords', 'href', 'nohref', 'alt', 'target')))
    b = TagProp('b', set(allattrs))
    basefont = TagProp('basefont', set(componentattrs + i18nattrs + ('id', 'size', 'color', 'face')))
    bdo = TagProp('bdo', set(componentattrs+eventattrs+('lang', 'dir')))
    big = TagProp('big', set(allattrs))
    blockquote = TagProp('blockquote', set(allattrs+('cite',)))
    body = TagProp('body', set(allattrs+('onload', 'onunload', 'onfocus', 'background', 'bgcolor', 'text'
                                                               'link', 'vlink', 'alink', 'leftmargin', 'topmargin', 'marginwidth', 'marginheight')))
    br = TagProp('br', set(componentattrs+('clear',)))
    button = TagProp('button', set(allattrs + focusattrs + ('name', 'value', 'type', 'disabled')))
    caption = TagProp('caption', set(allattrs + ('align',)))
    center = TagProp('center', set(allattrs))
    cite = TagProp('cite', set(allattrs))
    code = TagProp('code', set(allattrs))
    col = TagProp('col', set(allattrs + cellhalignattrs + cellvalignattrs + ('span', 'width')))
    colgroup = TagProp('colgroup', set(allattrs + cellhalignattrs + cellvalignattrs + ('span', 'width')))
    dd = TagProp('dd', set(allattrs))
    del_ = TagProp('del', set(allattrs+('cite', 'datetime')))
    dfn = TagProp('dfn', set(allattrs))
    dir = TagProp('dir', set(allattrs+('compact',)))
    div = TagProp('div', set(allattrs+('align',)))
    dl = TagProp('dl', set(allattrs+('compact',)))
    dt = TagProp('dt', set(allattrs))
    em = TagProp('em', set(allattrs))
    embed = TagProp('embed', set(('width', 'height', 'src', 'controller', 'href', 'target', 'border', 'pluginspage',
                                                      'quality', 'type', 'bgcolor', 'menu')))
    fieldset = TagProp('fieldset', set(allattrs))
    font = TagProp('font', set(componentattrs + i18nattrs + ('face', 'size', 'color')))
    form = TagProp('form', set(allattrs + ('action', 'method', 'name', 'enctype', 'onsubmit', 'onreset', 'accept_charset', 'target')))
    frame = TagProp('frame', set())
    frameset = TagProp('frameset', set(componentattrs + ('rows', 'cols', 'onload', 'onunload', 'framespacing', 'border', 'marginwidth'
                                                                      'marginheight', 'frameborder', 'noresize', 'scrolling')))
    h1 = TagProp('h1', set(allattrs+('align',)))
    h2 = TagProp('h2', set(allattrs+('align',)))
    h3 = TagProp('h3', set(allattrs+('align',)))
    h4 = TagProp('h4', set(allattrs+('align',)))
    h5 = TagProp('h5', set(allattrs+('align',)))
    h6 = TagProp('h6', set(allattrs+('align',)))
    hr = TagProp('hr', set(allattrs+('align', 'noshade', 'size', 'width', 'color')))
    html = TagProp('html', set(i18nattrs+('id',)))
    i = TagProp('i', set(allattrs))
    iframe = TagProp('iframe', set(componentattrs+('longdesc', 'name', 'src', 'frameborder', 'marginwidth', 'marginheight'
                                                                 'noresize', 'scrolling', 'align', 'height', 'width', 'hspace', 'vspace', 'bordercolor')))
    img = TagProp('img', set(allattrs+('src', 'alt', 'name', 'longdesc', 'width', 'height', 'usemap', 'ismap'
                                                              'align', 'border', 'hspace', 'vspace', 'lowsrc')))
    input = TagProp('input', set(allattrs + focusattrs + ('type', 'name', 'value', 'checked', 'disabled', 'readonly', 'size', 'maxlength', 'src'
                                                     'alt', 'usemap', 'onselect', 'onchange', 'accept', 'align', 'border')))
    ins = TagProp('ins', set(allattrs+('cite', 'datetime')))
    isindex = TagProp('isindex', set(componentattrs + i18nattrs + ('prompt',)))
    kbd = TagProp('kbd', set(allattrs))
    label = TagProp('label', set(allattrs + ('for', 'accesskey', 'onfocus', 'onblur')))
    legend = TagProp('legend', set(allattrs + ('accesskey', 'align')))
    li = TagProp('li', set(allattrs+('type', 'value')))
    map = TagProp('map', set(i18nattrs + eventattrs + ('id', 'class', 'style', 'title', 'name')))
    menu = TagProp('menu', set(allattrs+('compact',)))
    noframes = TagProp('noframes', set(allattrs))
    noscript = TagProp('noscript', set(allattrs))
    object = TagProp('object', set(allattrs + ('declare', 'classid', 'codebase', 'data', 'type', 'codetype'
                                                                   'archive', 'standby', 'height', 'width', 'usemap', 'name'
                                                                   'tabindex', 'align', 'border', 'hspace', 'vspace')))
    ol = TagProp('ol', set(allattrs+('type', 'compact', 'start')))
    optgroup = TagProp('optgroup', set(allattrs + ('disabled', 'label')))
    option = TagProp('option', set(allattrs + ('selected', 'disabled', 'label', 'value')))
    p = TagProp('p', set(allattrs+('align',)))
    param = TagProp('param', set(('id', 'name', 'value', 'valuetype', 'type')))
    pre = TagProp('pre', set(allattrs+('width',)))
    q = TagProp('q', set(allattrs+('cite',)))
    s = TagProp('s', set(allattrs))
    samp = TagProp('samp', set(allattrs))
    script = TagProp('script', set(('id', 'charset', 'type', 'language', 'src', 'defer')))
    select = TagProp('select', set(allattrs + ('name', 'size', 'multiple', 'disabled', 'tabindex', 'onfocus', 'onblur', 'onchange', 'rows')))
    small = TagProp('small', set(allattrs))
    span = TagProp('span', set(allattrs))
    strike = TagProp('strike', set(allattrs))
    strong = TagProp('strong', set(allattrs))
    style = TagProp('style', set(i18nattrs+('id', 'type', 'media', 'title')))
    sub = TagProp('sub', set(allattrs))
    sup = TagProp('sup', set(allattrs))
    table = TagProp('table', set(componentattrs + i18nattrs + ('prompt',)))
    tbody = TagProp('tbody', set(allattrs + cellhalignattrs + cellvalignattrs))
    td = TagProp('td', set(allattrs + cellhalignattrs + cellvalignattrs + ('abbr', 'axis', 'headers', 'scope', 'rowspan'
                                                                                                   'colspan', 'nowrap', 'bgcolor', 'width', 'height'
                                                                                                   'background', 'bordercolor')))
    textarea = TagProp('textarea', set(allattrs + focusattrs + ('name', 'rows', 'cols', 'disabled', 'readonly', 'onselect', 'onchange', 'wrap')))
    tfoot = TagProp('tfoot', set(allattrs + cellhalignattrs + cellvalignattrs))
    th = TagProp('th', set(allattrs + cellhalignattrs + cellvalignattrs + ('abbr', 'axis', 'headers', 'scope', 'rowspan'
                                                                                                   'colspan', 'nowrap', 'bgcolor', 'width', 'height'
                                                                                                   'background', 'bordercolor')))
    thead = TagProp('thead', set(allattrs + cellhalignattrs + cellvalignattrs))
    tr = TagProp('tr', set(allattrs + cellhalignattrs + cellvalignattrs + ('bgcolor', 'nowrap', 'width', 'background')))
    tt = TagProp('tt', set(allattrs))
    u = TagProp('u', set(allattrs))
    ul = TagProp('ul', set(allattrs+('type', 'compact')))
    var = TagProp('var', set(allattrs))

#    frame = TagProp('frame', set(componentattrs + ('longdesc', 'name', 'src', 'frameborder', 'marginwidht', 'marginheight',
#                                                                  'noresize', 'scrolling', 'framespacing', 'border', 'marginwidth', 'marginheight',
#                                                                  'frameborder', 'noresize', 'scrolling')))
    @classmethod
    def class_init(cls, specialTags):
        """Class initialisation

        In:
          -- ``special_tags`` -- tags that have a special factory
        """
        # Create a HTML parser that generate ``_HTMLTag`` nodes
        cls._html_parser = ET.HTMLParser()
        cls._html_parser.setElementClassLookup(ET.ElementDefaultClassLookup(element=_HTMLTag))

    def __init__(self, parent=None, **kw):
        """Renderer initialisation

        In:
          - ``parent`` -- parent renderer
        """
        super(Renderer, self).__init__(parent)

        if parent is None:
            self.head = self.head_renderer_factory(**kw)
        else:
            self.head = parent.head

    def makeelement(self, tag):
        """Make a tag

        In:
          - ``tag`` -- name of the tag to create

        Return:
          - the new tag
        """
        return self._makeelement(tag, self._html_parser)

    def _parse_html(self, parser, source, fragment, no_leading_text, **kw):
        """Parse a HTML file

        In:
          - ``parser`` -- XML or HTML parser to use
          - ``source`` -- can be a filename or a file object
          - ``fragment`` -- if ``True``, can parse a HTML fragment i.e a HTML without
            a unique root
          - ``no_leading_text`` -- if ``fragment`` is ``True``, ``no_leading_text``
            is ``False`` and the HTML to parsed begins by a text, this text is keeped
          - ``kw`` -- keywords parameters are passed to the HTML parser

        Return:
          - the root element of the parsed HTML, if ``fragment`` is ``False``
          - a list of HTML elements, if ``fragment`` is ``True``
        """
        if isinstance(source, basestring):
            if source.startswith(('http://', 'https://', 'ftp://')):
                source = urllib.urlopen(source)
            else:
                source = open(source)

        if not fragment:
            # Parse a HTML file
            # ----------------

            root = ET.parse(source, parser).getroot()
            source.close()

            # Attach the renderer to the root
            root._renderer = self
            return root

        # Parse a HTML fragment
        # ---------------------

        # Create a dummy ``<body>``
        html = cStringIO.StringIO('<html><body>%s</body></html>' % source.read())
        source.close()

        body = ET.parse(html, parser).getroot()[0]
        for e in body:
            if isinstance(e, _HTMLTag):
                # Attach the renderer to each roots
                e._renderer = self

        # Return the children of the dummy ``<body>``
        return ([body.text] if body.text and not no_leading_text else []) + body[:]

    def parse_html(self, source, fragment=False, no_leading_text=False, xhtml=False, **kw):
        """Parse a (X)HTML file

        In:
          - ``source`` -- can be a filename or a file object
          - ``fragment`` -- if ``True``, can parse a HTML fragment i.e a HTML without
            a unique root
          - ``no_leading_text`` -- if ``fragment`` is ``True``, ``no_leading_text``
            is ``False`` and the HTML to parsed begins by a text, this text is keeped
          - ``xhtml`` -- is the HTML to parse a valid XHTML ?
          - ``kw`` -- keywords parameters are passed to the HTML parser

        Return:
          - the root element of the parsed HTML, if ``fragment`` is ``False``
          - a list of HTML elements, if ``fragment`` is ``True``
        """
        parser = ET.XMLParser(**kw) if xhtml else ET.HTMLParser(**kw)
        parser.setElementClassLookup(ET.ElementDefaultClassLookup(element=_HTMLTag))

        return self._parse_html(parser, source, fragment, no_leading_text, **kw)

    def parse_htmlstring(self, text, fragment=False, no_leading_text=False, xhtml=False, **kw):
        """Parse a (X)HTML string

        In:
          - ``text`` -- can be a ``str`` or ``unicode`` strings
          - ``source`` -- can be a filename or a file object
          - ``fragment`` -- if ``True``, can parse a HTML fragment i.e a HTML without
            a unique root
          - ``no_leading_text`` -- if ``fragment`` is ``True``, ``no_leading_text``
            is ``False`` and the HTML to parsed begins by a text, this text is keeped
          - ``xhtml`` -- is the HTML to parse a valid XHTML ?
          - ``kw`` -- keywords parameters are passed to the HTML parser

        Return:
          - the root element of the parsed HTML, if ``fragment`` is ``False``
          - a list of HTML elements, if ``fragment`` is ``True``
        """
        if isinstance(text, unicode):
            text = text.encode(kw.setdefault('encoding', 'utf-8'))

        return self.parse_html(cStringIO.StringIO(text), fragment, no_leading_text, xhtml, **kw)

# ---------------------------------------------------------------------------

if __name__ == '__main__':
    t = ((1, 'a'), (2, 'b'), (3, 'c'))

    h = Renderer()

    h.head << h.head.title('A test')
    h.head << h.head.script('function() {}')
    h.head << h.head.meta(name='meta1', content='content1')

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

    print h.html(h.head.head(h.head.root), h.root).write_htmlstring(pretty_print=True)
