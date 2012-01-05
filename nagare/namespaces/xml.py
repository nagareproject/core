#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""XML renderer"""

from __future__ import with_statement

import types
import copy
import cStringIO
import urllib

import peak.rules

from lxml import etree as ET

from nagare.namespaces import common

CHECK_ATTRIBUTES = False

# Namespace for the ``meld:id`` attribute
_MELD_NS = 'http://www.plope.com/software/meld3'
_MELD_ID = '{%s}id' % _MELD_NS

# ---------------------------------------------------------------------------

class _Tag(ET.ElementBase):
    """A xml tag
    """
    def init(self, renderer):
        """Each tag keeps track of the renderer that created it

        Return:
           - ``self``
        """
        self._renderer = renderer
        return self

    @property
    def renderer(self):
        """Return the renderer that created this tag

        Return:
          - the renderer
        """
        # The renderer is search first, in this tag, else at the root of the tree
        return getattr(self, '_renderer', None) or self.getroottree().getroot()._renderer

    def write_xmlstring(self, encoding='utf-8', pipeline=True, **kw):
        """Serialize in XML the tree beginning at this tag

        In:
          - ``encoding`` -- encoding of the XML
          - ``pipeline`` -- if False, the ``meld:id`` attributes are deleted

        Return:
          - the XML
        """
        if not pipeline:
            for element in self.xpath('.//*[@meld:id]', namespaces={ 'meld' : _MELD_NS }):
                del element.attrib[_MELD_ID]

        return ET.tostring(self, encoding=encoding, method='xml', **kw)

    def xpath(self, *args, **kw):
        """Override ``xpath()`` to associate a renderer to all the returned nodes
        """
        nodes = super(_Tag, self).xpath(*args, **kw)

        renderer = self.renderer
        for node in nodes:
            node._renderer = renderer

        return nodes

    def findmeld(self, id, default=None):
        """Find a tag with a given ``meld:id`` value

        In:
          - ``id`` -- value of the ``meld:id`` attribute to search
          - ``default`` -- value returned if the tag is not found

        Return:
          - the tag found, else the ``default`` value
        """
        nodes = self.xpath('.//*[@meld:id="%s"]' % id, namespaces={ 'meld' : _MELD_NS })

        if len(nodes) != 0:
            # Return only the first tag found
            return nodes[0]

        return default

    def append_text(self, text):
        """Append a text to this tag

        In:
          - ``text`` -- text to add
        """
        if len(self) != 0:
            self[-1].tail = (self[-1].tail or '') + text
        else:
            self.text = (self.text or '') + text

    def add_child(self, child):
        """Append a child to this tag

        In:
          - ``child`` -- child to add
        """
        # Forward the call to the generic method
        add_child(self, child)

    def meld_id(self, id):
        """Set the value of the attribute ``meld:id`` of this tag

        In:
          - ``id`` - value of the ``meld;id`` attribute

        Return:
          - ``self``
        """
        self.add_child({ _MELD_ID : id })
        return self

    def fill(self, *children, **attrib):
        """Change all the child and append attributes of this tag

        In:
          - ``children`` -- list of the new children of this tag
          - ``attrib`` -- dictionnary of attributes of this tag

        Return:
          - ``self``
        """
        self[:] = []
        self.text = None

        return self.__call__(*children, **attrib)

    def replace(self, *children):
        """Replace this tag by others

        In:
          - ``children`` -- list of tags to replace this tag
        """
        parent = self.getparent()

        # We can not replace the root of the tree
        if parent is not None:
            tail = self.tail
            l = len(parent)

            i = parent.index(self)
            parent.fill(parent.text or '', parent[:i], children, self.tail or '', parent[i+1:])

            if len(parent) >= l:
                parent[i-l].tail = tail

    def repeat(self, iterable, childname=None):
        """Iterate over a sequence, cloning a new child each time

        In:
          - ``iterable`` -- the sequence
          - ``childname`` -- If ``None``, clone this tag each time else
            clone each time the tag that have ``childname`` as ``meld:id`` value

        Return:
          - list of tuples (cloned child, item of the sequence)
        """
        # Find the child to clone
        if childname is None:
            element = self
        else:
            element = self.findmeld(childname)

        parent = element.getparent()
        parent.remove(element)

        for thing in iterable:
            clone = copy.deepcopy(element)
            clone._renderer = element.renderer
            parent.append(clone)

            yield (clone, thing)

    def __call__(self, *children, **attrib):
        """Append child and attributes to this tag

        In:
          - ``children`` -- children to add
          - ``attrib`` -- attributes to add

        Return:
          - ``self``
        """
        if attrib:
            self.add_child(attrib)

        nb = len(children)
        if nb != 0:
            if nb == 1:
                children = children[0]
            self.add_child(children)

        if CHECK_ATTRIBUTES and self._authorized_attribs and not frozenset(self.attrib).issubset(self._authorized_attribs):
            raise AttributeError("Bad attributes for element <%s>: " % self.tag + ', '.join(list(frozenset(self.attrib) - self._authorized_attribs)))

        return self

    def __enter__(self):
        return self.renderer.enter(self)

    def __exit__(self, exception, data, tb):
        if exception is None:
            self.renderer.exit()

# ---------------------------------------------------------------------------

# Generic methods to add a child to a tag
# ---------------------------------------

def add_child(self, o):
    """Default method to add an object to a tag

    In:
      - ``self`` -- the tag
      - ``o`` -- object to add

    Try to add the result of ``o.render()`` to the tag
    """
    render = getattr(o, 'render', None)
    if render is None:
        raise TypeError("Can't append a '%s' to element <%s>" % (type(o), self.tag))

    self.add_child(render(self.renderer))

@peak.rules.when(add_child, (_Tag, basestring))
def add_child(self, s):
    """Add a string to a tag

    In:
      - ``self`` -- the tag
      - ``s`` - str or unicode string to add
    """
    self.append_text(s)

@peak.rules.when(add_child, (_Tag, tuple))
def add_child(self, t):
    """Add a tuple to a tag

    In:
      - ``self`` -- the tag
      - ``t`` -- tuple to add

    Add each items of the tuple
    """
    for child in t:
        self.add_child(child)

@peak.rules.when(add_child, (_Tag, list))
def add_child(self, l):
    """Add a list to a tag

    In:
      - ``self`` -- the tag
      - ``l`` -- list to add

    Add each items of the list
    """
    for child in l:
        self.add_child(child)

@peak.rules.when(add_child, (_Tag, types.GeneratorType))
def add_child(self, g):
    """Add a generator to a tag

    In:
      - ``self`` -- the tag
      - ``l`` -- generator to add

    Add each items produced
    """
    for child in g:
        self.add_child(child)

@peak.rules.when(add_child, (_Tag, int))
def add_child(self, i):
    """Add an integer to a tag

    In:
      - ``self`` -- the tag
      - ``i`` -- integer to add

    Convert the integer to string and then add it
    """
    self.append_text(str(i))

@peak.rules.when(add_child, (_Tag, long))
def add_child(self, l):
    """Add a long integer to a tag

    In:
      - ``self`` -- the tag
      - ``l`` -- long integer to add

    Convert the long integer to string and then add it
    """
    self.append_text(str(l))

@peak.rules.when(add_child, (_Tag, float))
def add_child(self, f):
    """Add a float to a tag

    In:
      - ``self`` -- the tag
      - ``f`` -- float to add

    Convert the float to string and then add it
    """
    self.append_text(str(f))

@peak.rules.when(add_child, (_Tag, ET.ElementBase))
def add_child(self, element):
    """Add a tag to a tag

    In:
      - ``self`` -- the tag
      - ``element`` -- the tag to add
    """
    if hasattr(element, '_renderer'):
        del element._renderer

    self.append(element)

@peak.rules.when(add_child, (_Tag, ET._Comment))
def add_child(self, element):
    """Add a comment element to a tag

    In:
      - ``self`` -- the tag
      - ``element`` -- the comment to add
    """
    if hasattr(element, '_renderer'):
        del element._renderer

    self.append(element)

@peak.rules.when(add_child, (_Tag, ET._ProcessingInstruction))
def add_child(self, element):
    """Add a PI element to a tag

    In:
      - ``self`` -- the tag
      - ``element`` -- the PI to add

    Do nothing
    """
    pass

@peak.rules.when(add_child, (_Tag, dict))
def add_child(self, d):
    """Add a dictionary to a tag

    In:
      - ``self`` -- the tag
      - ``element`` -- the dictionary to add

    Each key/value becomes an attribute of the tag

    Attribute name can end with a '_' which is removed
    """
    for (name, value) in d.items():
        if name.endswith('_'):
            name = name[:-1]

        add_attribute(self, name, value)

# ---------------------------------------------------------------------------

# Generic methods to add an attribute to a tag
# --------------------------------------------

def add_attribute(self, name, value):
    """Default method to add an attribute to a tag

    In:
      - ``self`` -- the tag
      - ``name`` -- name of the attribute to add
      - ``value`` -- value of the attribute to add
    """
    add_attribute(self, name, unicode(value))

@peak.rules.when(add_attribute, (_Tag, basestring, basestring))
def add_attribute(self, name, value):
    self.set(name, value)

# ---------------------------------------------------------------------------

class TagProp(object):
    """Tag factory with a behavior of an object attribute

    Each time this attribute is read, a new tag is created
    """
    def __init__(self, name, authorized_attribs=None, factory=None):
        """Initialization

        In:
          - ``name`` -- name of the tags to create
          - ``authorized_attribs`` -- names of the valid attributes
          - ``factory`` -- special factory to create the tag
        """
        self._name = name
        self._factory = factory

        if CHECK_ATTRIBUTES:
            self._authorized_attribs = frozenset(authorized_attribs) if authorized_attribs is not None else None

    def __get__(self, renderer, cls):
        """Create a new tag each time this attribute is read

        In:
          - ``renderer`` -- the object that has this attribute
          - ``cls`` -- *not used*

        Return:
          - a new tag
        """
        element = renderer.makeelement(self._name)

        if CHECK_ATTRIBUTES:
            element._authorized_attribs = self._authorized_attribs

        return element


class RendererMetaClass(type):
    """Meta class for the renderer class

    Discover the tags that have a special factory and pass them to the
    ``class_init()`` method of the class
    """
    def __new__(self, cls_name, bases, ns):
        """Creation of the class

        In:
          - ``cls_name`` -- name of the class to create
          - ``bases`` -- tuple of the base classes of the class to create
          - ``ns`` -- namespace of the class to create

        Return:
          - the new class
        """
        cls = super(RendererMetaClass, self).__new__(self, cls_name, bases, ns)

        special_tags = {}

        for (k, v) in ns.items():
            if isinstance(v, TagProp):
                if v._factory is not None:
                    special_tags[v._name] = v._factory
                del v._factory

        cls.class_init(special_tags)

        return cls

# -----------------------------------------------------------------------

class XmlRenderer(common.Renderer):
    """The base class of all the renderers that generate a XML dialect
    """
    __metaclass__ = RendererMetaClass

    doctype = ''
    content_type = 'text/xml'

    @classmethod
    def class_init(cls, special_tags):
        """Class initialisation

        In:
          -- ``special_tags`` -- tags that have a special factory
        """
        # Create a XML parser that generate ``_Tag`` nodes
        cls._xml_parser = ET.XMLParser()
        cls._xml_parser.setElementClassLookup(ET.ElementDefaultClassLookup(element=_Tag))

    def __init__(self, parent=None):
        """Renderer initialisation

        In:
          - ``parent`` -- parent renderer
        """
        if parent is None:
            self.namespaces = None
            self._default_namespace = None
        else:
            # This renderer use the same XML namespaces than its parent
            self.namespaces = parent.namespaces
            self._default_namespace = parent._default_namespace

        self.parent = parent
        self._prefix = ''

        # The stack, contening the last tag push by a ``with`` statement
        # Initialized with a dummy root
        self._stack = [self.makeelement('_renderer_root_')]

        # Each renderer created has a unique id
        self.id = self.generate_id('id')

    def _get_default_namespace(self):
        """Return the default_namespace

        Return:
          - the default namespace or ``None`` if no default namespace was set
        """
        return self._default_namespace

    def _set_default_namespace(self, namespace):
        """Change the default namespace

        The namespace must be a key of the ``self.namespaces`` dictionary or be
        ``None``

        For example:

        .. code-block:: python

          x.namespaces = { 'xsl' : 'http://www.w3.org/1999/XSL/Transform' }
          x.set_default_namespace('xsl')
        """
        self._default_namespace = namespace

        if namespace is None:
            self._prefix = ''
        else:
            self._prefix = '{%s}' % self.namespaces[namespace]
    default_namespace = property(_get_default_namespace, _set_default_namespace)

    @property
    def root(self):
        """Return the first tag(s) sent to the renderer

        .. warning::
            A list of tags can be returned

        Return:
          - the tag(s)
        """
        children = self._stack[0].getchildren()

        text = self._stack[0].text

        if text is not None:
            children.insert(0, text)

        if not children:
            return ''

        if len(children) == 1:
            return children[0]

        return children

    def enter(self, current):
        """A new tag is pushed by a ``with`` statement

        In:
          - ``current`` -- the tag

        Return:
          - ``current``
        """
        self << current     # Append the tag to its parent
        self._stack.append(current) # Push it onto the stack

        return current

    def exit(self):
        """End of a ``with`` statement
        """
        self._stack.pop()   # Pop the current tag from the stack

    def _makeelement(self, tag, parser):
        """Make a tag, in the default namespace set

        In:
          - ``tag`` -- name of the tag to create
          - ``parser`` -- parser used to create the tag

        Return:
          - the new tag
        """
        # 1. Create the tag with in the default namespace
        element = parser.makeelement(self._prefix+tag, nsmap=self.namespaces)
        # 2. Initialize it with this renderer
        return element.init(self)

    def makeelement(self, tag):
        """Make a tag, in the default namespace set

        In:
          - ``tag`` -- name of the tag to create

        Return:
          - the new tag
        """
        # Create the tag with the XML parser
        return self._makeelement(tag, self._xml_parser)

    def __lshift__(self, current):
        """Add a tag tag the last tag pushed by a ``with`` statement

        In:
          - ``current`` -- tag to add

        Return:
          - ``self``, the renderer
        """
        add_child(self._stack[-1], current)
        return self

    def comment(self, text=''):
        """Create a comment element

        In:
          - ``text`` -- text of the comment

        Return:
          - the new comment element
        """
        return ET.Comment(text)

    def parse_xml(self, source, fragment=False, no_leading_text=False, **kw):
        """Parse a XML file

        In:
          - ``source`` -- can be a filename or a file object
          - ``fragment`` -- if ``True``, can parse a XML fragment i.e a XML without
            a unique root
          - ``no_leading_text`` -- if ``fragment`` is ``True``, ``no_leading_text``
            is ``False`` and the XML to parsed begins by a text, this text is keeped
          - ``kw`` -- keywords parameters are passed to the XML parser

        Return:
          - the root element of the parsed XML, if ``fragment`` is ``False``
          - a list of XML elements, if ``fragment`` is ``True``
        """
        if isinstance(source, basestring):
            if source.startswith(('http://', 'https://', 'ftp://')):
                source = urllib.urlopen(source)
            else:
                source = open(source)

        # Create a dedicated XML parser with the ``kw`` parameter
        parser = ET.XMLParser(**kw)
        # This parser will generate nodes of type ``_Tag``
        parser.setElementClassLookup(ET.ElementDefaultClassLookup(element=_Tag))

        if not fragment:
            # Parse a XML file
            # ----------------

            root = ET.parse(source, parser).getroot()
            source.close()

            # Attach the renderer to the root
            root._renderer = self
            return root

        # Parse a XML fragment
        # --------------------

        # Create a dummy root
        xml = cStringIO.StringIO('<dummy>%s</dummy>' % source.read())
        source.close()

        root = ET.parse(xml, parser).getroot()
        for e in root[:]:
            # Attach the renderer to each roots
            e._renderer = self

        # Return the children of the dummy root
        return ([root.text] if root.text and not no_leading_text else []) + root[:]

    def parse_xmlstring(self, text, fragment=False, no_leading_text=False, **kw):
        """Parse a XML string

        In:
          - ``text`` -- can be a ``str`` or ``unicode`` string
          - ``fragment`` -- if ``True``, can parse a XML fragment i.e a XML without
            a unique root
          - ``no_leading_text`` -- if ``fragment`` is ``True``, ``no_leading_text``
            is ``False`` and the XML to parsed begins by a text, this text is keeped
          - ``kw`` -- keywords parameters are passed to the XML parser

        Return:
          - the root element of the parsed XML, if ``fragment`` is ``False``
          - a list of XML elements, if ``fragment`` is ``True``
        """
        if type(text) == unicode:
            text = text.encode(kw.setdefault('encoding', 'utf-8'))

        return self.parse_xml(cStringIO.StringIO(text), fragment, no_leading_text, **kw)

# ---------------------------------------------------------------------------

class Renderer(XmlRenderer):
    """The XML Renderer

    This renderer generate any tags you give

    .. code-block:: pycon

       >>> xml = xml.Renderer()
       >>> xml.foo(xml.bar).write_xmlstring()
       '<foo><bar/></foo>'
    """
    def __getattr__(self, name):
        """Any attribute access becomes a tag generation

        In:
          - ``name`` -- name of the tag to generate

        Return:
          - the generated tag
        """
        return self.makeelement(name)

# ---------------------------------------------------------------------------

if __name__ == '__main__':
    x = Renderer()
    x.namespaces = { 'meld' : 'http://www.plope.com/software/meld3' }

    with x.contacts:
        with x.contact.meld_id('contact'):
            x << x.name.meld_id('name')
            with x.address.meld_id('addr'):
                x << 'ici, rennes'

    print x.root.write_xmlstring(xml_declaration=True, pretty_print=True)
    print

    for (e, (name, addr)) in x.root.repeat((('bill', 'seatle'), ('steve', 'cupertino')), 'contact'):
         e.findmeld('name').text = name
         e.findmeld('addr').text = addr

    print x.root.write_xmlstring(pretty_print=True)
    print

    # -----------------------------------------------------------------------

    x = Renderer()
    x << x.foo
    x << x.bar

    print x.all(x.root).write_xmlstring(xml_declaration=True, pretty_print=True)
    print

    # -----------------------------------------------------------------------

    t1 = x.parse_xmlstring('''
    <a>avant<x>kjkjkl</x>#<b b='b'>hello</b>apres</a>
    ''')

    t2 = x.parse_xmlstring('''
    <toto>xxx<titi a='a'>world</titi>yyy</toto>
    ''')

    t1[1].replace(t2[0])
    #t1[1].replace('new')
    #t1[1].replace()

    print t1.write_xmlstring()
