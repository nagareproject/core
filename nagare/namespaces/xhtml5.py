#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The XHTML5 renderer
"""

from __future__ import with_statement

from lxml import etree as ET

from nagare.namespaces.xml import TagProp
from nagare.namespaces import xhtml_base, xhtml

# -----------------------------------------------------------------------------

class Input(xhtml._HTMLActionTag):
    """Class of all the new input types of HTML5
    """
    _actions = (1, 'name', 'onchange')


class ObsoleteTagProp(TagProp):
    """Class of all the HTML4 tags obsolete in HTML5
    """
    def __get__(self, renderer, cls):
        # Raise the same exception as when an attribute doesn't exist
        raise AttributeError("'%s' object has no attribute '%s'" % (renderer.__class__.__name__, self._name))

# -----------------------------------------------------------------------------

class Source(xhtml_base._HTMLTag):
    """The <source> tag
    """
    def add_child(self, child):
        """Add child and attributes
        """
        super(Source, self).add_child(child)

        # If this is a relative URL, it's relative to the statics directory
        # of the application
        src = self.get('src')
        if src is not None:
            self.set('src', xhtml.absolute_url(src, self.renderer.head.static_url))

# -----------------------------------------------------------------------------

class Renderer(xhtml.Renderer):
    """The XHTML5 synchronous renderer
    """

    XML_DOCTYPE = HTML_DOCTYPE = '<!DOCTYPE html>'

    # New HTML5 tags
    # --------------

    section = TagProp('section')
    article = TagProp('article')
    aside = TagProp('aside')
    hgroup = TagProp('hgroup')
    header = TagProp('header')
    footer = TagProp('footer')
    nav = TagProp('nav')
    figure = TagProp('figure')
    figcaption = TagProp('figcaption')
    time = TagProp('time')
    video = TagProp('video')
    audio = TagProp('audio')
    source = TagProp('source', factory=Source)
    embed = TagProp('embed')
    mark = TagProp('mark')
    progress = TagProp('progress')
    meter = TagProp('meter')
    ruby = TagProp('ruby')
    rt = TagProp('rt')
    rp = TagProp('rp')
    wbr = TagProp('wbr')
    canvas = TagProp('canvas')
    command = TagProp('command')
    details = TagProp('details')
    summary = TagProp('summary')
    datalist = TagProp('datalist')
    keygen = TagProp('keygen')
    output = TagProp('output')
    track = TagProp('track')

    # Obsolete HTML4 tags
    # -------------------

    basefont = ObsoleteTagProp('basefont')
    big = ObsoleteTagProp('big')
    center = ObsoleteTagProp('center')
    font = ObsoleteTagProp('font')
    s = ObsoleteTagProp('s')
    strike = ObsoleteTagProp('strike')
    tt = ObsoleteTagProp('tt')
    u = ObsoleteTagProp('u')
    frame = ObsoleteTagProp('frame')
    frameset = ObsoleteTagProp('frameset')
    noframes = ObsoleteTagProp('u')
    acronym = ObsoleteTagProp('acronym')
    abbr = ObsoleteTagProp('abbr')
    applet = ObsoleteTagProp('applet')
    isindex = ObsoleteTagProp('isindex')
    dir = ObsoleteTagProp('dir')

    # New input types
    # ---------------

    _specialTags = dict([(input_type+'_input', Input) for input_type in (
                    'tel', 'search', 'url', 'email',
                    'datetime', 'date', 'datetime-local_input',
                    'month', 'week', 'time', 'number', 'range', 'color'
                   )])
    _specialTags.update(xhtml.Renderer._specialTags)

    @classmethod
    def class_init(cls, specialTags):
        """Class initialisation

        In:
          -- ``special_tags`` -- tags that have a special factory
        """
        class CustomLookup(ET.CustomElementClassLookup):
            def __init__(self, specialTags, defaultLookup):
                super(CustomLookup, self).__init__(defaultLookup)
                self._specialTags = specialTags

            def lookup(self, node_type, document, namespace, name):
                return self._specialTags.get(name)

        cls._specialTags.update(specialTags)

        cls._custom_lookup = CustomLookup(cls._specialTags, ET.ElementDefaultClassLookup(element=xhtml_base._HTMLTag))
        cls._html_parser = ET.HTMLParser()
        cls._html_parser.setElementClassLookup(cls._custom_lookup)

    def AsyncRenderer(self, *args, **kw):
        """Create an associated asynchronous HTML renderer

        Return:
          - a new asynchronous renderer
        """
        # If no arguments are given, this renderer becomes the parent of the
        # newly created renderer
        if not args and not kw:
            args = (self,)

        return AsyncRenderer(*args, **kw)

# -----------------------------------------------------------------------------

class AsyncRenderer(xhtml.AsyncRenderer, Renderer):
    """The XHTML5 asynchronous renderer
    """
    def SyncRenderer(self, *args, **kw):
        """Create an associated synchronous HTML renderer

        Return:
          - a new synchronous renderer
        """
        # If no arguments are given, this renderer becomes the parent of the
        # newly created renderer
        if not args and not kw:
            args = (self,)

        return Renderer(*args, **kw)

# ---------------------------------------------------------------------------

from nagare import presentation

if __name__ == '__main__':
    t = ((1, 'a'), (2, 'b'), (3, 'c'))

    h = Renderer()

    h.head << h.head.title('A test')
    h.head << h.head.javascript('__foo__', 'function() {}')
    h.head << h.head.meta(name='meta1', content='content1')

    with h.body(onload='javascript:alert()'):
        h << h.section(name='name')
        h << h.article
        h << h.aside
        h << h.hgroup
        h << h.header
        h << h.footer
        h << h.nav
        h << h.figure

        h << h.video
        h << h.audio
        h << h.source
        h << h.embed
        h << h.mark
        h << h.progress
        h << h.meter
        h << h.ruby
        h << h.rt
        h << h.rp
        h << h.wbr
        h << h.canvas
        h << h.command
        h << h.details
        h << h.summary
        h << h.datalist
        h << h.keygen
        h << h.output

        with h.ul:
            with h.li('Hello'): pass
            with h.li:
                h << 'world'
            h << h.li('yeah')

        with h.div(class_='foo'):
            with h.h1('moi'):
                h << h.i('foo')

        with h.div:
            h << 'yeah'
            for i in range(3):
                h << i

        with h.table(foo='foo'):
            for row in t:
                with h.tr:
                    for column in row:
                        with h.td:
                            h << column

        with h.form:
            h << h.input(type='url')

    print h.html(presentation.render(h.head, None, None, None), h.root).write_htmlstring(pretty_print=True)
