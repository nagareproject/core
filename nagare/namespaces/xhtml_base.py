# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""The XHTML renderer

This renderer only depends of the ``nagare.namespaces.xml`` module.
Having not dependencies to the framework make it suitable to be used in others frameworks.
"""

import cStringIO
import urllib
import peak

from lxml import etree as ET

from nagare.namespaces import xml
from nagare.namespaces.xml import TagProp

# ---------------------------------------------------------------------------

# Common attributes
# -----------------

componentattrs = {'id', 'class', 'style', 'title'}
i18nattrs = {'lang', 'dir'}
eventattrs = {
    'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmousemove',
    'onmouseover', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup'
}
allattrs = componentattrs | i18nattrs | eventattrs
focusattrs = {'accesskey', 'tabindex', 'onfocus', 'onblur'}


class _HTMLTag(xml._Tag):
    """A xhtml tag
    """
    def write_xmlstring(self, encoding='utf-8', pipeline=True, **kw):
        """Serialize in XML the tree beginning at this tag

        In:
          - ``encoding`` -- encoding of the XML
          - ``pipeline`` -- if False, the ``meld:id`` attributes are deleted

        Return:
          - the XML
        """
        return xml._Tag.write_xmlstring(self.decorate_error(), encoding, pipeline, **kw)

    def write_htmlstring(self, encoding='utf-8', pipeline=True, **kw):
        """Serialize in XHTML the tree beginning at this tag

        In:
          - ``encoding`` -- encoding of the XML
          - ``pipeline`` -- if False, the ``meld:id`` attributes are deleted

        Return:
          - the XHTML
        """
        if not pipeline:
            for element in self.xpath('.//*[@meld:id]', namespaces={'meld': xml._MELD_NS}):
                del element.attrib[xml._MELD_ID]

        return ET.tostring(self.decorate_error(), encoding=encoding, method='html', **kw)

    def error(self, err):
        """Mark this tag as erroneous

        In:
          - ``err`` -- the error message

        Return:
          - ``self``
        """
        if err is not None:
            self.has_error = err

        return self

    def decorate_error(self):
        """Decorate this tag with an error structure

        Forward the call to the renderer ``decorate_error()`` method

        Return:
          - a tree
        """
        err = getattr(self, 'has_error', None)
        return self if err is None else self.renderer.decorate_error(self, err)


@peak.rules.when(xml.add_child, (_HTMLTag, _HTMLTag))
def add_child(next_method, self, element):
    """Add a tag to a tag

    In:
      - ``self`` -- the tag
      - ``element`` -- the tag to add
    """
    return next_method(self, element.decorate_error())


@peak.rules.when(xml.add_attribute, (_HTMLTag, basestring, basestring))
def add_attribute(next_method, self, name, value):
    if name.startswith('data_'):
        name = name.replace('_', '-')

    next_method(self, name, value)


class HeadRenderer(xml.XmlRenderer):
    """The XHTML head Renderer

    This renderer knows about the possible tags of a html ``<head>``
    """

    # Tag factories
    # -------------

    base = TagProp('base', {'id', 'href', 'target'})
    head = TagProp('head', i18nattrs | {'id', 'profile'})
    link = TagProp('link', allattrs | {'charset', 'href', 'hreflang', 'type', 'rel', 'rev', 'media', 'target'})
    meta = TagProp('meta', i18nattrs | {'id', 'http_equiv', 'name', 'content', 'scheme'})
    title = TagProp('title', i18nattrs | {'id'})
    style = TagProp('style', i18nattrs | {'id'})
    script = TagProp('script', i18nattrs | {'id'})

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

    componentattrs = {'id', 'class', 'style', 'title'}
    i18nattrs = {'lang', 'dir'}
    eventattrs = {
        'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmousemove',
        'onmouseover', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup'
    }
    focusattrs = {'accesskey', 'tabindex', 'onfocus', 'onblur'}
    cellhalignattrs = {'align', 'char', 'charoff'}
    cellvalignattrs = {'valign'}
    allattrs = componentattrs | i18nattrs | eventattrs

    # The HTML tags
    # -------------

    a = TagProp('a', allattrs | focusattrs | {
        'charset', 'type', 'name', 'href', 'hreflang', 'rel',
        'rev', 'shape', 'coords', 'target', 'oncontextmenu'
    })
    abbr = TagProp('abbr', allattrs)
    acronym = TagProp('acronym', allattrs)
    address = TagProp('address', allattrs)
    applet = TagProp('applet', componentattrs | {
        'codebase', 'archive', 'code', 'object', 'alt', 'name', 'width',
        'height', 'align', 'hspace', 'vspace'
    })
    area = TagProp('area', allattrs | focusattrs | {'shape', 'coords', 'href', 'nohref', 'alt', 'target'})
    b = TagProp('b', allattrs)
    basefont = TagProp('basefont', componentattrs | i18nattrs | {'id', 'size', 'color', 'face'})
    bdo = TagProp('bdo', componentattrs | eventattrs | {'lang', 'dir'})
    big = TagProp('big', allattrs)
    blockquote = TagProp('blockquote', allattrs | {'cite'})
    body = TagProp('body', allattrs | {
        'onload', 'onunload', 'onfocus', 'background', 'bgcolor', 'text',
        'link', 'vlink', 'alink', 'leftmargin', 'topmargin', 'marginwidth', 'marginheight'
    })
    br = TagProp('br', componentattrs | {'clear'})
    button = TagProp('button', allattrs | focusattrs | {'name', 'value', 'type', 'disabled'})
    caption = TagProp('caption', allattrs | {'align'})
    center = TagProp('center', allattrs)
    cite = TagProp('cite', allattrs)
    code = TagProp('code', allattrs)
    col = TagProp('col', allattrs | cellhalignattrs | cellvalignattrs | {'span', 'width'})
    colgroup = TagProp('colgroup', allattrs | cellhalignattrs | cellvalignattrs | {'span', 'width'})
    dd = TagProp('dd', allattrs)
    del_ = TagProp('del', allattrs | {'cite', 'datetime'})
    dfn = TagProp('dfn', allattrs)
    dir = TagProp('dir', allattrs | {'compact'})
    div = TagProp('div', allattrs | {'align'})
    dl = TagProp('dl', allattrs | {'compact'})
    dt = TagProp('dt', allattrs)
    em = TagProp('em', allattrs)
    embed = TagProp('embed', {
        'width', 'height', 'src', 'controller', 'href', 'target',
        'border', 'pluginspage', 'quality', 'type', 'bgcolor', 'menu'
    })
    fieldset = TagProp('fieldset', allattrs)
    font = TagProp('font', componentattrs | i18nattrs | {'face', 'size', 'color'})
    form = TagProp('form', allattrs | {
        'action', 'method', 'name', 'enctype',
        'onsubmit', 'onreset', 'accept_charset', 'target'
    })
    frame = TagProp('frame', set())
    frameset = TagProp('frameset', componentattrs | {
        'rows', 'cols', 'onload', 'onunload', 'framespacing', 'border',
        'marginwidth', 'marginheight', 'frameborder', 'noresize', 'scrolling'
    })
    h1 = TagProp('h1', allattrs | {'align'})
    h2 = TagProp('h2', allattrs | {'align'})
    h3 = TagProp('h3', allattrs | {'align'})
    h4 = TagProp('h4', allattrs | {'align'})
    h5 = TagProp('h5', allattrs | {'align'})
    h6 = TagProp('h6', allattrs | {'align'})
    hr = TagProp('hr', allattrs | {'align', 'noshade', 'size', 'width', 'color'})
    html = TagProp('html', i18nattrs | {'id'})
    i = TagProp('i', allattrs)
    iframe = TagProp('iframe', componentattrs | {
        'longdesc', 'name', 'src', 'frameborder', 'marginwidth', 'marginheight',
        'noresize', 'scrolling', 'align', 'height', 'width', 'hspace', 'vspace', 'bordercolor',
    })
    img = TagProp('img', allattrs | {
        'src', 'alt', 'name', 'longdesc', 'width', 'height', 'usemap',
        'ismap', 'align', 'border', 'hspace', 'vspace', 'lowsrc'
    })
    input = TagProp('input', allattrs | focusattrs | {
        'type', 'name', 'value', 'checked', 'disabled', 'readonly', 'size', 'maxlength',
        'src', 'alt', 'usemap', 'onselect', 'onchange', 'accept', 'align', 'border'
    })
    ins = TagProp('ins', allattrs | {'cite', 'datetime'})
    isindex = TagProp('isindex', componentattrs | i18nattrs | {'prompt'})
    kbd = TagProp('kbd', allattrs)
    label = TagProp('label', allattrs | {'for', 'accesskey', 'onfocus', 'onblur'})
    legend = TagProp('legend', allattrs | {'accesskey', 'align'})
    li = TagProp('li', allattrs | {'type', 'value'})
    map = TagProp('map', i18nattrs | eventattrs | {'id', 'class', 'style', 'title', 'name'})
    menu = TagProp('menu', allattrs | {'compact'})
    noframes = TagProp('noframes', allattrs)
    noscript = TagProp('noscript', allattrs)
    object = TagProp('object', allattrs | {
        'declare', 'classid', 'codebase', 'data', 'type', 'codetype',
        'archive', 'standby', 'height', 'width', 'usemap', 'name',
        'tabindex', 'align', 'border', 'hspace', 'vspace'
    })
    ol = TagProp('ol', allattrs | {'type', 'compact', 'start'})
    optgroup = TagProp('optgroup', allattrs | {'disabled', 'label'})
    option = TagProp('option', allattrs | {'selected', 'disabled', 'label', 'value'})
    p = TagProp('p', allattrs | {'align'})
    param = TagProp('param', {'id', 'name', 'value', 'valuetype', 'type'})
    pre = TagProp('pre', allattrs | {'width'})
    q = TagProp('q', allattrs | {'cite'})
    s = TagProp('s', allattrs)
    samp = TagProp('samp', allattrs)
    script = TagProp('script', {'id', 'charset', 'type', 'language', 'src', 'defer'})
    select = TagProp('select', allattrs | {
        'name', 'size', 'multiple', 'disabled', 'tabindex',
        'onfocus', 'onblur', 'onchange', 'rows'
    })
    small = TagProp('small', allattrs)
    span = TagProp('span', allattrs)
    strike = TagProp('strike', allattrs)
    strong = TagProp('strong', allattrs)
    style = TagProp('style', i18nattrs | {'id', 'type', 'media', 'title'})
    sub = TagProp('sub', allattrs)
    sup = TagProp('sup', allattrs)
    table = TagProp('table', componentattrs | i18nattrs | {'prompt'})
    tbody = TagProp('tbody', allattrs | cellhalignattrs | cellvalignattrs)
    td = TagProp('td', allattrs | cellhalignattrs | cellvalignattrs | {
        'abbr', 'axis', 'headers', 'scope', 'rowspan',
        'colspan', 'nowrap', 'bgcolor', 'width', 'height',
        'background', 'bordercolor'
    })
    textarea = TagProp('textarea', allattrs | focusattrs | {
        'name', 'rows', 'cols', 'disabled',
        'readonly', 'onselect', 'onchange', 'wrap'
    })
    tfoot = TagProp('tfoot', allattrs | cellhalignattrs | cellvalignattrs)
    th = TagProp('th', allattrs | cellhalignattrs | cellvalignattrs | {
        'abbr', 'axis', 'headers', 'scope', 'rowspan',
        'colspan', 'nowrap', 'bgcolor', 'width', 'height'
        'background', 'bordercolor'
    })
    thead = TagProp('thead', allattrs | cellhalignattrs | cellvalignattrs)
    tr = TagProp('tr', allattrs | cellhalignattrs | cellvalignattrs | {'bgcolor', 'nowrap', 'width', 'background'})
    tt = TagProp('tt', allattrs)
    u = TagProp('u', allattrs)
    ul = TagProp('ul', allattrs | {'type', 'compact'})
    var = TagProp('var', allattrs)

#    frame = TagProp('frame', componentattrs | {'longdesc', 'name', 'src', 'frameborder', 'marginwidht', 'marginheight',
#                                                                  'noresize', 'scrolling', 'framespacing', 'border', 'marginwidth', 'marginheight',
#                                                                  'frameborder', 'noresize', 'scrolling'})
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
            with h.li('Hello'):
                pass
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
