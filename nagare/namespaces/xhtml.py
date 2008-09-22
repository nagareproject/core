#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The XHTML renderer

This renderer is dedicated to the framework
"""

from __future__ import with_statement

import types, urllib, imghdr

from lxml import etree as ET
import peak.rules

from nagare import security, ajax, presentation

from nagare.namespaces import xml
from nagare.namespaces.xml import TagProp
from nagare.namespaces import xhtml_base

# ---------------------------------------------------------------------------

# Generic methods to add an attribute to a tag
# --------------------------------------------

@peak.rules.when(xml.add_attribut, (xml._Tag, basestring, ajax.Update))
def add_attribut(self, name, value):
    """Add an attribute with a ``ajax.Update`` value
    
    In:
      - ``self`` -- the tag
      - ``name`` -- name of the attribute
      - ``value`` -- ``ajax.Update`` value
    """
    # Generate a XHR request
    add_attribut(self, name, value.generate_action(3, self.renderer))

@peak.rules.when(xml.add_attribut, (xml._Tag, basestring, types.FunctionType))
def add_attribut(self, name, value):
    """Add an attribut with a function value
    
    In:
      - ``self`` -- the tag
      - ``name`` -- name of the attribute
      - ``value`` -- function value
    """
    # Transcode the function to javascript
    add_attribut(self, name, ajax.JS(value))

@peak.rules.when(xml.add_attribut, (xml._Tag, basestring, types.MethodType))
def add_attribut(self, name, value):
    """Add an attribut with a method value
    
    In:
      - ``self`` -- the tag
      - ``name`` -- name of the attribute
      - ``value`` -- method value
    """
    # Transcode the method to javascript
    add_attribut(self, name, ajax.JS(value))

@peak.rules.when(xml.add_attribut, (xml._Tag, basestring, ajax.JS))
def add_attribut(self, name, value):
    """Add an attribut with a ``ajax.JS`` value
    
    In:
      - ``self`` -- the tag
      - ``name`` -- name of the attribute
      - ``value`` -- ``ajax.JS`` value
    """
    self.set(name, value.generate_action(None, self.renderer))

# ---------------------------------------------------------------------------

def absolute_url(url, static):
    """Convert a relative URL of a static content to an absolute one
    
    In:
      - ``url`` -- url to convert
      - ``static`` -- URL prefix of the static contents
      
    Return:
      - an absolute URL
    """
    i = url.find(':')
    if ((i == -1) or not url[:i].isalpha()) and url and (url[0] != '/'):
        # If this is a relative URL, it's relative to the statics directory
        if not static.endswith('/') and not url.startswith('/'):
            url = static + '/' + url
        else:
            url = static + url
        
    return url
        

class HeadRenderer(xhtml_base.HeadRenderer):
    """The XHTML head Renderer
    
    This renderer knows about the static contents of the application
    """    
    def __init__(self, static):
        super(HeadRenderer, self).__init__()

        # Directory where are located the static contents of the application
        self.static = static
        self.anonymous = 0

    def add_script(self, script, url):
        if url:
            self.javascript_url(url)
        else:
            self.javascript(self.anonymous, script)
            self.anonymous += 1
        
    def add_css(self, css):
        self.css(self.anonymous, css)
        self.anonymous += 1

    def css_url(self, url):
        """Memorize a css style URL
        
        In:
          - ``url`` -- the css style URL
          
        Return:
          - ``()``
        """
        return super(HeadRenderer, self).css_url(absolute_url(url, self.static))

    def javascript(self, name, script):
        """Memorize a in-line javascript code
        
        In:
          - ``name`` -- unique name of this javascript code (to prevent double definition)
          - ``script`` -- a function, a method or a javascript code
          
        Return:
          - ``()``
        """
        if callable(script):
            # Transcode the function or the method to javascript code
            script = ajax.javascript(script)

        if isinstance(script, ajax.JS):
            # Transcoded javascript needs a helper
            self.javascript_url('/static/nagare/pyjslib.js')
            script = script.javascript

        return super(HeadRenderer, self).javascript(name, script)

    def javascript_url(self, url):
        """Memorize a javascript URL
        
        In:
          - ``url`` -- the javascript URL
          
        Return:
          - ``()``
        """
        return super(HeadRenderer, self).javascript_url(absolute_url(url, self.static))

@presentation.render_for(HeadRenderer)
def render(self, h, *args):
    """
    Generate the ``<head>`` tree
    
    In:
      - ``h`` -- *not used*
      
    Return:
      - the ``<head>`` tree
    """
    
    # Create the tags to include the CSS styles and the javascript codes

    css_url = [self.link(rel='stylesheet', type='text/css', href='%s' % url) for url in self._get_css_url()]
    
    css = self._get_css()
    if css:
        css = self.style(css, type='text/css')

    javascript_url = [self.script(src=url, type='text/javascript') for url in self._get_javascript_url()]
    javascript = [self.script(script.encode('utf-8'), type='text/javascript') for script in self._get_javascript()]

    head = self.root

    if isinstance(head, ET.ElementBase) and (head.tag == 'head'):
        # If a ``<head>`` tag already exist, take its content
        head = self.head(head[:], dict(head.attrib))
    else:
        head = self.head(head)
    
    return head(css_url, css, javascript_url, javascript, '\n')


# ----------------------------------------------------------------------------------

class _HTMLActionTag(xhtml_base._HTMLTag):
    """Base class of all the tags with a ``.action()`` method
    """
    def action(self, action, permissions=None, subject=None):
        """Register an action
        
        In:
          - ``action`` -- action
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on
          
        Return:
          - ``self``
        """
        if isinstance(action, ajax.Update):
            self._async_action(self.renderer, action, permissions, subject)
        else:
            # Double dispatch with the renderer
            self.renderer.action(self, action, permissions, subject)
        
        return self

    def sync_action(self, renderer, action, permissions, subject):
        """Register a synchronous action
        
        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- the action
        """
        if permissions is not None:
            # Wrapper the ``action`` into a wrapper that will check the user permissions
            action = security.permissions_with_subject(permissions, subject or self._renderer.component())(action)

        self.set(self._actions[1], renderer.register_callback(self._actions[0], action))

    async_action = sync_action
    
    def _async_action(self, renderer, action, permissions, subject):
        """Register a asynchronous action
        
        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- the action
        """
        if callable(action):
            action = ajax.Update(renderer.model, action, None)
        
        self.set(self._actions[2], action.generate_action(self._actions[0], renderer))

# ----------------------------------------------------------------------------------

class Form(xhtml_base._HTMLTag):
    """ The ``<form>`` tag
    """
    def init(self, renderer):
        """Initialisation
        
        In:
          - ``renderer`` -- the current renderer
          
        Return:
          - ``self``
        """
        super(Form, self).init(renderer)

        # Set the default attributes : send the form with a POST, in utf-8
        self.set('enctype', 'multipart/form-data')
        self.set('method', 'post')
        self.set('accept-charset', 'utf-8')

        self.set('action', '?')
        #self.append(renderer.input(name='_charset_', value='utf-8', type='hidden'))

        # Add into the form the hidden fields of the session and continuation ids
        self._renderer.add_sessionid_in_form(self)
        return self

    def add_child(self, child):
        """Add a child to this ``<form>`` tag
        
        Delete the existing ``<form>`` tags in the child tree
        """
        if isinstance(child, ET.ElementBase):
            for f in child.findall('form'):
                f.replace(f.getchildren()[1:])

        if isinstance(child, Form):
            child = child.getchildren()[1:]

        super(Form, self).add_child(child)

    def pre_action(self, action, permissions=None, subject=None):
        """Register an action that will be executed **before** the actions of the
        form elements
        
        In:
          - ``action`` -- action
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on
          
        Return:
          - ``self``
        """
        if permissions is not None:
            # Wrapper the ``action`` into a wrapper that will check the user permissions            
            action = security.permissions_with_subject(permissions, subject or self._renderer.component())(action)

        # Generate a hidden field with the action attached
        self.append(self.renderer.input(type='hidden', name=self.renderer.register_callback(0, action)))
        return self
        
    def post_action(self, action, permissions=None, subject=None):
        """Register an action that will be executed **after** the actions of the
        form elements
        
        In:
          - ``action`` -- action
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on
          
        Return:
          - ``self``
        """
        if permissions is not None:
             # Wrapper the ``action`` into a wrapper that will check the user permissions
             action = security.permissions_with_subject(permissions, subject or self._renderer.component())(action)

        # Generate a hidden field with the action attached
        self.append(self.renderer.input(type='hidden', name=self.renderer.register_callback(3, action)))
        return self
    
# ----------------------------------------------------------------------------------

class TextInput(_HTMLActionTag):
    """Dispatcher class for all the ``<input>`` tags
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous actions
    #   - name of the attribute for then asynchronous actions
    _actions = (1, 'name', 'onchange')

    def __call__(self, *children, **attrib):
        t = attrib.get('type', 'text')
        if t == 'text':
            # ``<input>`` with ``type=text``
            return super(TextInput, self).__call__(*children, **attrib)

        element = self.renderer.makeelement(t + '_input')
        element.tag = self.tag
        if hasattr(self, '_authorized_attribs'):
            element._authorized_attribs = self._authorized_attribs

        return element(*children, **attrib)


class TextArea(_HTMLActionTag):
    """ ``<textarea>`` tags
    """
    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous actions
    #   - name of the attribute for then asynchronous actions
    _actions = (1, 'name', 'onchange')
    
    def action(self, action, permissions=None, subject=None):
        """Register an action
        
        In:
          - ``action`` -- action
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        Return:
          - ``self``
        """
        # The content sent to the action will have the '\r' characters deleted
        return super(TextArea, self).action(lambda v: action(v.replace('\r', '')), permissions, subject)


class PasswordInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=password`` attributes
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous actions
    #   - name of the attribute for then asynchronous actions
    _actions = (1, 'name', 'onchange')


class RadioInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=radio`` attributes
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous actions
    #   - name of the attribute for then asynchronous actions
    _actions = (2, 'value', 'onchange')

    def selected(self, flag):
        """(de)Select the tag
        
        In:
          - ``flag`` -- boolean to deselect / select the tag
          
        Return:
          - ``self``
        """
        if 'checked' in self.attrib:
            del self.attrib['checked']

        if flag:
            self.set('checked', 'checked')
        return self


class CheckboxInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=checkbox`` attributes
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous actions
    #   - name of the attribute for then asynchronous actions
    _actions = (1, 'name', 'onchange')

    def selected(self, flag):
        """(de)Select the tag
        
        In:
          - ``flag`` -- boolean to deselect / select the tag
          
        Return:
          - ``self``
        """
        if 'checked' in self.attrib:
            del self.attrib['checked']

        if flag:
            self.set('checked', 'checked')
        return self


class SubmitInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=submit`` attributes
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous actions
    #   - name of the attribute for then asynchronous actions
    _actions = (4, 'name', 'onclick')
    
    def async_action(self, renderer, action, permissions, subject):
        return self._async_action(renderer, action, permissions, subject)

class HiddenInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=hidden`` attributes
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous actions
    #   - name of the attribute for then asynchronous actions
    _actions = (1, 'name', 'onchange')


class FileInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=file`` attributes
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous actions
    #   - name of the attribute for then asynchronous actions
    _actions = (1, 'name', 'onchange')

    def init(self, renderer):
        """Initialisation
       
        In:
          - ``renderer`` -- the current renderer
          
        Return:
          - ``self``
        """
        super(FileInput, self).init(renderer)

        self.set('name', 'file')
        return self


class ImageInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=image`` attributes
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous actions
    #   - name of the attribute for then asynchronous actions
    _actions = (5, 'name', 'onclick')

# ----------------------------------------------------------------------------------

class Option(xhtml_base._HTMLTag):
    """ ``<options>`` tags
    """    
    def selected(self, values):
        """(de)Select the tags
        
        In:
          - ``values`` -- name or list of names of the tags to select
          
        Return:
          - ``self``
        """        
        if not isinstance(values, (list, tuple)):
            values = (values,)

        if 'selected' in self.attrib:
            del self.attrib['selected']
        
        if self.get('value') in values:
            self.set('selected', 'selected')
            
        return self

    
class Select(_HTMLActionTag):
    """ ``<select>`` tags
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous actions
    #   - name of the attribute for then asynchronous actions
    _actions = (1, 'name', 'onchange')
    
    def action(self, action, permissions=None, subject=None):
        """Register an action
        
        In:
          - ``action`` -- action
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        Return:
          - ``self``
        """        
        if self.get('multiple') is not None:
            # If this is a multiple select, the value sent to the action will
            # always be a list, even if only 1 item was selected
            action = lambda v, action=action: action(v if isinstance(v, (list, tuple)) else (v,))
            
        return super(Select, self).action(action, permissions, subject)

# ----------------------------------------------------------------------------------

class A(_HTMLActionTag):
    """ ``<a>`` tags
    """
    def sync_action(self, renderer, action, permissions, subject):
        """Register a synchronous action
        
        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- action
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        """
        if permissions is not None:
            # Wrapper the ``action`` into a wrapper that will check the user permissions
            action = security.permissions_with_subject(permissions, subject or self._renderer.component())(action)

        self.set('href', renderer.add_sessionid_in_url( self.get('href', ''), (renderer.register_callback(4, action),)))
    
    def _async_action(self, renderer, action, permissions, subject):
        """Register an asynchronous action
        
        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- action
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on
        """
        if callable(action):
            action = ajax.Update(renderer.model, action, None)
        
        self.set('href', '#')
        self.set('onclick', action.generate_action(41, renderer))
    async_action = _async_action
    
    """
    def url(self, *args):
        url = '/'.join([urllib.quote_plus(unicode(u).encode('utf-8'), '') for u in args])
            
        href = self.get('href', '')
        
        if not href.startswith(('#', '?')):
            href = ''

        self.set('href', self._renderer.url + '/' + url + href)

        return self
    """

@peak.rules.when(xml.add_attribut, (A, basestring, basestring))
def add_attribut(next_method, self, name, value):
    if name == 'href':
        value = absolute_url(value, self._renderer.url)

    next_method(self, name, value)

# ----------------------------------------------------------------------------------

class Img(_HTMLActionTag):
    """ ``<img>`` tags
    """    
    def _set_content_type(self, response, img):
        """Guess the image format and set the ``Content-Type`` of the response
        
        In:
          - ``reponse`` -- the response object
          - ``img`` -- the image data
          
        Return:
          - ``img``
        """
        if not response.content_type:
            # If no ``Content-Type`` is already set, use the ``imghdr`` module
            # to guess the format of the image
            img_type = imghdr.what(None, img[:32])
            if img_type is not None:
                response.content_type = 'image/'+img_type
        return img
        
    def sync_action(self, renderer, action, permissions, subject):
        """Register a synchronous action
        
        The action will have to return the image data
        
        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- the action
        """        
        self.set('src', renderer.add_sessionid_in_url(sep=';') + ';' + renderer.register_callback(6, None, lambda h: self._set_content_type(h.response, action(h))))
    async_action = sync_action
  
    def add_child(self, child):
        """Add attributes to the image
        
        In:
          - ``child`` -- attributes dictionary
        """
        super(Img, self).add_child(child)

        # If this is a relative URL, it's relative to the statics directory
        # of the application
        src = self.get('src')
        if src is not None:
            self.set('src', absolute_url(src, self.renderer.head.static))


# ----------------------------------------------------------------------------------

class Label(xhtml_base._HTMLTag):
    """ ``<label>`` tags
    """        
    def init(self, renderer):
        """Initialisation
        
        In:
          - ``renderer`` -- the current renderer
          
        Return:
          - ``self``
        """        
        super(Label, self).init(renderer)

        # Generate a unique value for the ``for`` attribute
        self.set('for', renderer.generate_id('id'))
        return self

# ----------------------------------------------------------------------------------

class DummyRenderer(xhtml_base.DummyRenderer):
    """Root of the ``xhtml.Renderer`` objects"""
    head_renderer_factory = HeadRenderer
        
    def __init__(self, session=None, request=None, response=None, callbacks=None, static='', url='/'):
        """Initialisation
        
        In:
          - ``session`` -- the session object
          - ``request`` -- the request object
          - ``response`` -- the response object
          - ``callbacks`` -- the registered actions on the tags
          - ``static`` -- directory of the static contents of the application
          - ``url`` -- url prefix of the application
        """
        super(DummyRenderer, self).__init__(static)

        self.session = session
        self.request = request
        self.response = response        
        self._callbacks = callbacks
        self._rendered = set()      # List a the component rendered by all the renderers
        self.url = url
        
        self.component = None        
        #self.model = None

class Renderer(xhtml_base.Renderer):
    """The XHTML synchronous renderer
    """
    
    # Redefinition of the he HTML tags with actions
    # ---------------------------------------------

    a = TagProp('a', set(xhtml_base.allattrs+xhtml_base.focusattrs+('charset', 'type', 'name', 'href', 'hreflang', 'rel', 'rev', 'shape', 'coords', 'target', 'oncontextmenu')), A)
    area =  area = TagProp('area', set(xhtml_base.allattrs + xhtml_base.focusattrs + ('shape', 'coords', 'href', 'nohref', 'alt', 'target')), A)
    button = TagProp('button', set(xhtml_base.allattrs + xhtml_base.focusattrs + ('name', 'value', 'type', 'disabled')), SubmitInput)
    form = TagProp('form', set(xhtml_base.allattrs + ('action', 'method', 'name', 'enctype', 'onsubmit', 'onreset', 'accept_charset', 'target')), Form)
    img = TagProp('img', set(xhtml_base.allattrs+('src', 'alt', 'name', 'longdesc', 'width', 'height', 'usemap', 'ismap'
                                                              'align', 'border', 'hspace', 'vspace', 'lowsrc')), Img)
    input = TagProp('input', set(xhtml_base.allattrs + xhtml_base.focusattrs + ('type', 'name', 'value', 'checked', 'disabled', 'readonly', 'size', 'maxlength', 'src'
                                                     'alt', 'usemap', 'onselect', 'onchange', 'accept', 'align', 'border')), TextInput)
    label = TagProp('label', set(xhtml_base.allattrs + ('for', 'accesskey', 'onfocus', 'onblur')), Label)
    option = TagProp('option', set(xhtml_base.allattrs + ('selected', 'disabled', 'label', 'value')), Option)
    select = TagProp('select', set(xhtml_base.allattrs + ('name', 'size', 'multiple', 'disabled', 'tabindex', 'onfocus', 'onblur', 'onchange', 'rows')), Select)
    textarea = TagProp('textarea', set(xhtml_base.allattrs + xhtml_base.focusattrs + ('name', 'rows', 'cols', 'disabled', 'readonly', 'onselect', 'onchange', 'wrap')), TextArea)

    _specialTags = dict(
                    text_input     = TextInput,
                    radio_input    = RadioInput,
                    checkbox_input = CheckboxInput,
                    submit_input   = SubmitInput,
                    hidden_input   = HiddenInput,
                    file_input     = FileInput,
                    password_input = PasswordInput,
                    image_input    = ImageInput
                   )

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

    def makeelement(self, tag):
        """Make a tag
        
        In:
          - ``tag`` -- name of the tag to create
          
        Return:
          - the new tag
        """                
        return self._makeelement(tag, self._html_parser)

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
        parser.setElementClassLookup(self._custom_lookup)
        
        return self._parse_html(parser, source, fragment, no_leading_text, **kw)

    def __init__(self, parent=None):
        """Renderer initialisation
        
        In:
          - ``parent`` -- parent renderer
        """        
        if parent is None:
            parent = DummyRenderer()

        super(Renderer, self).__init__(parent)

        self.session = parent.session
        self.request = parent.request
        self.response = parent.response
        self._callbacks = parent._callbacks
        self._rendered = parent._rendered
        self.component = parent.component
        self.url = parent.url
        self.head = parent.head
        
        self.model = None

    def start_rendering(self, component, model):
        """Method called before to render a component
        
        In:
          - ``component`` -- component to render
          - ``model`` -- name of the view to use
        """
        self.component = component
        self.model = model

        if component.url is not None:
            self.url = self.url + '/' + component.url

        # Delete all the previous callbacks registered by the component
        if self._callbacks and (component not in self._rendered):
            self._callbacks.unregister_callbacks(component)
        
        # Memorize all the component rendered
        self._rendered.add(component)

    def action(self, tag, action, permissions, subject):
        """Register a synchronous action on a tag
        
        In:
          - ``tag`` -- the tag
          - ``action`` -- action
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        """
        tag.sync_action(self, action, permissions, subject)

    def register_callback(self, priority, f, render=None):
        """Register an action
        
        Forward the call to the ``callbacks`` object
        
        In:
          - ``priority`` - -priority of the action
          - ``f`` -- the action
          - ``render`` -- render method to generate the view after
            the ``f`` action will be called
        """
        return self._callbacks.register_callback(self.component, priority, f, render)


    def decorate_error(self, element, error):
        """During the rendering, highlight an element that has an error
        
        In:
          - ``element`` -- the element in error
          - ``error`` -- the error text 
        """
        if error is None:
            return element

        return self.div(
                     self.div(element, class_='nagare-error-input'),
                     self.div(error, class_='nagare-error-message'),
                     class_='nagare-error-field'
                    )


    def add_sessionid_in_form(self, form):
        """Add the session and continuation ids into a ``<form>``
        
        Forward this call to the sessions manager

        In:
          - ``form`` -- the form tag
        """
        if self.session:
            form(self.session.sessionid_in_form(self, self.request, self.response))

    def add_sessionid_in_url(self, u='', params=None, sep='&'):
        """Add the session and continuation ids into an url
        
        Forward this call to the sessions manager

        In:
          - ``u`` -- the url
          - ``params`` -- query string of the url
          
        Return:
          - the completed url
        """
        if not u.startswith('/'):
            u = self.url + '/' + u
        
        if params is None:
            params = ()

        if self.session:
            u += '?' + sep.join(self.session.sessionid_in_url(self.request, self.response) + params)

        return u
    

@presentation.render_for(HeadRenderer, model='async')
def render(self, h, *args):
    """Generate a javascript view of the head
    
    In:
      - ``h`` -- the current renderer
      
    Return:
      - a javascript
    """
    css = ' '.join(self._get_css())         # Inline CSS    
    js = ';'.join(self._get_javascript())   # Javascript codes

    return "nagare_loadAll(%s, %s, '%s', '%s')" % (
                                                 ajax.py2js(self._get_javascript_url(), h),
                                                 ajax.py2js(self._get_css_url(), h),
                                                 css.replace("'", r"\'").replace('\n', ''),
                                                 js.replace("'", r"\'").replace('\n', '').encode('utf-8')
                                                )


class AsyncScript(xhtml_base._HTMLTag):
    pass


@peak.rules.when(xml.add_child, (xhtml_base._HTMLTag, AsyncScript))
def add_child(self, script):
    """Add a script to a tag
    
    In:
      - ``self`` -- the tag
      - ``script`` -- the script to add
    """
    # Don't generate any tags but remember the script text or url
    self.renderer.head.add_script(script.text, script.get('src'))
    return ''


class AsyncStyle(xhtml_base._HTMLTag):
    pass


@peak.rules.when(xml.add_child, (xhtml_base._HTMLTag, AsyncStyle))
def add_child(self, css):
    """Add a css to a tag
    
    In:
      - ``self`` -- the tag
      - ``css`` -- the script to add
    """
    # Don't generate any tags but remember the css text
    self.renderer.head.add_css(css.text)
    return ''


class AsyncRenderer(Renderer):
    """The XHTML asynchronous renderer
    """
    script = TagProp('script', set(('id', 'charset', 'type', 'language', 'src', 'defer')), AsyncScript)
    style = TagProp('style', set(Renderer.i18nattrs+('id', 'type', 'media', 'title')), AsyncStyle)
        
    _specialTags = Renderer._specialTags.copy()

    def __init__(self, parent):
        """Renderer initialisation
        
        In:
          - ``parent`` -- parent renderer
        """        
        super(AsyncRenderer, self).__init__(parent)
        self.async_root = True;
        self.wrapper_to_generate = False    # Add a ``<div>`` around the rendering ?
        
    def action(self, tag, action, permissions, subject):
        """Register an asynchronous action on a tag
        
        In:
          - ``tag`` -- the tag
          - ``action`` -- action
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        """
        tag.async_action(self, action, permissions, subject)

    def start_rendering(self, component, model):
        super(AsyncRenderer, self).start_rendering(component, model)
        self.async_root = False

    def end_rendering(self, output):
        """Method called after a component is rendered
        
        In:
          - ``output`` -- rendered tree
          
        Out:
          - rendered tree
        """
        if self.wrapper_to_generate:
            output = self.div(output, id=self.id)

        return output

    def get_async_root(self):        
        if not isinstance(self.parent, AsyncRenderer):
            #return None
            return self
        
        if self.parent.async_root:
            return self
        
        return self.parent.get_async_root()

# ---------------------------------------------------------------------------

if __name__ == '__main__':
    t = ((1, 'a'), (2, 'b'), (3, 'c'))

    h = Renderer()

    h.head << h.head.title('A test')
    h.head << h.head.javascript('__foo__', 'function() {}')
    h.head << h.head.meta(name='meta1', content='content1')

    with h.body(onload='javascript:alert()'):
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

    print h.html(h.head.head(h.head.render()), h.root).write_htmlstring(pretty_print=True)
