#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The XHTML renderer

This renderer is dedicated to the Nagare framework
"""

from __future__ import with_statement

import operator, types, urllib, imghdr

from lxml import etree as ET
import peak.rules
import webob

from nagare import security, ajax, presentation

from nagare.namespaces import xml
from nagare.namespaces.xml import TagProp
from nagare.namespaces import xhtml_base

# ---------------------------------------------------------------------------

# Generic methods to add an attribute to a tag
# --------------------------------------------

@peak.rules.when(xml.add_attribute, (xml._Tag, basestring, ajax.Update))
def add_attribute(self, name, value):
    """Add an attribute with a ``ajax.Update`` value

    In:
      - ``self`` -- the tag
      - ``name`` -- name of the attribute
      - ``value`` -- ``ajax.Update`` value
    """
    # Generate a XHR request
    xml.add_attribute(self, name, value.generate_action(self._actions[0], self.renderer))

@peak.rules.when(xml.add_attribute, (xml._Tag, basestring, types.FunctionType))
def add_attribute(self, name, value):
    """Add an attribute with a function value

    In:
      - ``self`` -- the tag
      - ``name`` -- name of the attribute
      - ``value`` -- function value
    """
    # Transcode the function to javascript
    xml.add_attribute(self, name, ajax.JS(value))

@peak.rules.when(xml.add_attribute, (xml._Tag, basestring, types.MethodType))
def add_attribute(self, name, value):
    """Add an attribute with a method value

    In:
      - ``self`` -- the tag
      - ``name`` -- name of the attribute
      - ``value`` -- method value
    """
    # Transcode the method to javascript
    xml.add_attribute(self, name, ajax.JS(value))

@peak.rules.when(xml.add_attribute, (xml._Tag, basestring, ajax.JS))
def add_attribute(self, name, value):
    """Add an attribute with a ``ajax.JS`` value

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
    if url.startswith('#'):
        return url

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
    def __init__(self, static_url):
        """Renderer initialisation

        The ``HeadRenderer`` keeps track of the javascript and css used by every views,
        to be able to concatenate them into the ``<head>`` section.
        """
        super(HeadRenderer, self).__init__()

        # Directory where are located the static contents of the application
        self.static_url = static_url

        self._named_css = {}        # CSS code
        self._css_url = {}          # CSS URLs
        self._named_javascript = {} # Javascript code
        self._javascript_url = {}   # Javascript URLs

        self._order = 0             # Memorize the order of the javascript and css

    def css(self, name, style, **kw):
        """Memorize an in-line named css style

        In:
          - ``name`` -- unique name of this css style (to prevent double definition)
          - ``style`` -- the css style
          - ``kw`` -- attributes of the generated ``<style>`` tag

        Return:
          - ``()``
        """
        self._named_css.setdefault(name, (self._order, style, kw))
        self._order += 1
        return ()

    def css_url(self, url, **kw):
        """Memorize a css style URL

        In:
          - ``url`` -- the css style URL
          - ``kw`` -- attributes of the generated ``<link>`` tag

        Return:
          - ``()``
        """
        self._css_url.setdefault(absolute_url(url, self.static_url), (self._order, kw))
        self._order += 1
        return ()

    def javascript(self, name, script, **kw):
        """Memorize an in-line named javascript code

        In:
          - ``name`` -- unique name of this javascript code (to prevent double definition)
          - ``script`` -- the javascript code
          - ``kw`` -- attributes of the generated ``<script>`` tag

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

        self._named_javascript.setdefault(name, (self._order, script, kw))
        self._order += 1
        return ()

    def javascript_url(self, url, **kw):
        """Memorize a javascript URL

        In:
          - ``url`` -- the javascript URL
          - ``kw`` -- attributes of the the generated ``<script>`` tag

        Return:
          - ``()``
        """
        self._javascript_url.setdefault(absolute_url(url, self.static_url), (self._order, kw))
        self._order += 1
        return ()

    def _style(self, append, tag, style):
        append(tag, style)

    def _script(self, append, tag, script):
        append(tag, script)

    def _get_named_css(self):
        """Return the list of the in-line named css styles, sorted by order of insertion

        Return:
          - list of (name, css style, attributes)
        """

        return [(name, style, attributes) for (name, (order, style, attributes)) in sorted(self._named_css.items(), key=operator.itemgetter(1))]

    def _get_css_url(self):
        """Return the list of css URLs, sorted by order of insertion

        Return:
          - list of css (URLs, attributes)
        """
        return [(url, attributes) for (url, (order, attributes)) in sorted(self._css_url.items(), key=operator.itemgetter(1))]

    def _get_named_javascript(self):
        """Return the list of named javascript codes, sorted by order of insertion

        Return:
          - list of (name, javascript code, attributes)
        """
        return [(name, js, attributes) for (name, (order, js, attributes)) in sorted(self._named_javascript.items(), key=operator.itemgetter(1))]

    def _get_javascript_url(self):
        """Return the list of javascript URLs, sorted by order of insertion

        Return:
          - list of javascript (URLs, attributes)
        """
        return [(url, attributes) for (url, (order, attributes)) in sorted(self._javascript_url.items(), key=operator.itemgetter(1))]

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

    head = self.root

    if isinstance(head, ET.ElementBase) and (head.tag == 'head'):
        # If a ``<head>`` tag already exist, take its content
        head = self.head(head[:], dict(head.attrib))
    else:
        head = self.head(head)

    head.extend([self.link(rel='stylesheet', type='text/css', href=url, **attributes) for (url, attributes) in self._get_css_url()])
    head.extend([self.script(type='text/javascript', src=url, **attributes) for (url, attributes) in self._get_javascript_url()])

    head.extend([self.style(css, type='text/css', **attributes) for (name, css, attributes) in self._get_named_css()])
    head.extend([self.script(js, type='text/javascript', **attributes) for (name, js, attributes) in self._get_named_javascript()])

    return head

# ----------------------------------------------------------------------------------

class _HTMLActionTag(xhtml_base._HTMLTag):
    """Base class of all the tags with a ``.action()`` method
    """
    def action(self, action, with_request=False, permissions=None, subject=None):
        """Register an action

        In:
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        Return:
          - ``self``
        """
        if isinstance(action, ajax.Update):
            self._async_action(self.renderer, action, with_request, permissions, subject)
        else:
            # Double dispatch with the renderer
            self.renderer.action(self, action, with_request, permissions, subject)

        return self

    def sync_action(self, renderer, action, with_request, permissions, subject):
        """Register a synchronous action

        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on
        """
        if permissions is not None:
            # Wrap the ``action`` into a wrapper that will check the user permissions
            action = security.permissions_with_subject(permissions, subject or self._renderer.component())(action)

        self.set(self._actions[1], renderer.register_callback(self._actions[0], action, with_request))

    async_action = sync_action

    def _async_action(self, renderer, action, with_request, permissions, subject):
        """Register an asynchronous action

        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on
        """
        if callable(action):
            action = ajax.Update(action=action, with_request=with_request)

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
            for f in child.findall('.//form'):
                f.replace(f.getchildren()[1:])

        if isinstance(child, Form):
            child = child.getchildren()[1:]

        super(Form, self).add_child(child)

    def pre_action(self, action, with_request=False, permissions=None, subject=None):
        """Register an action that will be executed **before** the actions of the
        form elements

        In:
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        Return:
          - ``self``
        """
        if permissions is not None:
            # Wrap the ``action`` into a wrapper that will check the user permissions
            action = security.permissions_with_subject(permissions, subject or self._renderer.component())(action)

        # Generate a hidden field with the action attached
        self.append(self.renderer.div(self.renderer.input(type='hidden', name=self.renderer.register_callback(0, action, with_request))))
        return self

    def post_action(self, action, with_request=False, permissions=None, subject=None):
        """Register an action that will be executed **after** the actions of the
        form elements

        In:
          - ``action`` -- action
          - ``with_request`` -- will the request and response object be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        Return:
          - ``self``
        """
        if permissions is not None:
             # Wrap the ``action`` into a wrapper that will check the user permissions
             action = security.permissions_with_subject(permissions, subject or self._renderer.component())(action)

        # Generate a hidden field with the action attached
        self.append(self.renderer.div(self.renderer.input(type='hidden', name=self.renderer.register_callback(3, action, with_request))))
        return self

# ----------------------------------------------------------------------------------

class TextInput(_HTMLActionTag):
    """Dispatcher class for all the ``<input>`` tags
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous action
    #   - name of the attribute for the asynchronous action
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

        return element(**dict(self.attrib))(*children, **attrib)


class TextArea(_HTMLActionTag):
    """ ``<textarea>`` tags
    """
    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous action
    #   - name of the attribute for the asynchronous action
    _actions = (1, 'name', 'onchange')

    def action(self, action, with_request=False, permissions=None, subject=None):
        """Register an action

        In:
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        Return:
          - ``self``
        """
        # The content sent to the action will have the '\r' characters deleted
        if with_request:
            f = lambda request, response, v: action(request, response, v.replace('\r', ''))
        else:
            f = lambda v: action(v.replace('\r', ''))

        return super(TextArea, self).action(f, with_request, permissions, subject)


class PasswordInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=password`` attributes
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous action
    #   - name of the attribute for the asynchronous action
    _actions = (1, 'name', 'onchange')


class RadioInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=radio`` attributes
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous action
    #   - name of the attribute for the asynchronous action
    _actions = (2, 'value', 'onclick')

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
    #   - name of the attribute for the synchronous action
    #   - name of the attribute for the asynchronous action
    _actions = (1, 'name', 'onclick')

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
    #   - name of the attribute for the synchronous action
    #   - name of the attribute for the asynchronous action
    _actions = (4, 'name', 'onclick')

    def async_action(self, renderer, action, with_request, permissions, subject):
        """Register an asynchronous action

        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on
        """
        return self._async_action(renderer, action, with_request, permissions, subject)

class HiddenInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=hidden`` attributes
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous action
    #   - name of the attribute for the asynchronous action
    _actions = (1, 'name', 'onchange')


class FileInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=file`` attributes
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous action
    #   - name of the attribute for the asynchronous action
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
    #   - name of the attribute for the synchronous action
    #   - name of the attribute for the asynchronous action
    _actions = (5, 'name', 'onclick')

    def async_action(self, renderer, action, with_request, permissions, subject):
        """Register an asynchronous action

        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on
        """
        return self._async_action(renderer, action, with_request, permissions, subject)

    def add_child(self, child):
        """Add attributes to the image input

        In:
          - ``child`` -- attributes dictionary
        """
        super(ImageInput, self).add_child(child)

        # If this is a relative URL, it's relative to the statics directory
        # of the application
        src = self.get('src')
        if src is not None:
            self.set('src', absolute_url(src, self.renderer.head.static_url))

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

        if self.get('value') in map(unicode, values):
            self.set('selected', 'selected')

        return self


class Select(_HTMLActionTag):
    """ ``<select>`` tags
    """

    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous action
    #   - name of the attribute for the asynchronous action
    _actions = (1, 'name', 'onchange')

    def action(self, action, with_request=False, permissions=None, subject=None):
        """Register an action

        In:
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        Return:
          - ``self``
        """
        if self.get('multiple') is not None:
            # If this is a multiple select, the value sent to the action will
            # always be a list, even if only 1 item was selected
            if with_request:
                action = lambda request, response, v, action=action: action(request, response, v if isinstance(v, (list, tuple)) else (v,))
            else:
                action = lambda v, action=action: action(v if isinstance(v, (list, tuple)) else (v,))

        return super(Select, self).action(action, with_request, permissions, subject)

# ----------------------------------------------------------------------------------

class A(_HTMLActionTag):
    """ ``<a>`` tags
    """
    # Tuple:
    #   - action type
    #   - name of the attribute for the synchronous action
    #   - name of the attribute for the asynchronous action
    _actions = (41, None, 'onclick')

    def sync_action(self, renderer, action, with_request, permissions, subject):
        """Register a synchronous action

        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        """
        if permissions is not None:
            # Wrap the ``action`` into a wrapper that will check the user permissions
            action = security.permissions_with_subject(permissions, subject or self._renderer.component())(action)

        href = self.get('href', '').partition('#')
        self.set('href', renderer.add_sessionid_in_url(href[0], (renderer.register_callback(4, action, with_request),))+href[1]+href[2])

    def _async_action(self, renderer, action, with_request, permissions, subject):
        """Register an asynchronous action

        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on
        """
        super(A, self)._async_action(renderer, action, with_request, permissions, subject)
        self.set('href', '#')
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

@peak.rules.when(xml.add_attribute, (A, basestring, basestring))
def add_attribute(next_method, self, name, value):
    if name == 'href':
        value = absolute_url(value, self._renderer.url)

    next_method(self, name, value)

# ----------------------------------------------------------------------------------

class Img(_HTMLActionTag):
    """ ``<img>`` tags
    """
    def _set_content_type(self, request, action, with_request):
        """Generate the image and guess its format

        In:
          - ``request`` -- the web request object
          - ``action`` -- function to call to generate the image data
          - ``with_request`` -- will the request and response objects be passed to the action ?

        Return:
          - new response object raised
        """
        e = webob.exc.HTTPOk(headerlist=[('Content-Type', '')])
        img = action(request, e) if with_request else action()
        e.body = img

        content_type = e.content_type
        if not content_type:
            # If no ``Content-Type`` is already set, use the ``imghdr`` module
            # to guess the format of the image
            content_type = 'image/'+(imghdr.what(None, img[:32]) or '*')
        e.content_type = content_type

        raise e

    def sync_action(self, renderer, action, with_request, permissions, subject):
        """Register a synchronous action

        The action will have to return the image data

        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on
        """
        if permissions is not None:
            # Wrap the ``action`` into a wrapper that will check the user permissions
            action = security.permissions_with_subject(permissions, subject or self._renderer.component())(action)

        f = lambda request, response, action=action: self._set_content_type(request, action, with_request)
        self.set('src', renderer.add_sessionid_in_url(sep=';') + ';' + renderer.register_callback(2, f, with_request=True))
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
            self.set('src', absolute_url(src, self.renderer.head.static_url))

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

class Script(xhtml_base._HTMLTag):
    pass

@peak.rules.when(xml.add_child, (xhtml_base._HTMLTag, Script))
def add_child(next_method, self, script):
    """Add a <script> to a tag

    In:
      - ``self`` -- the tag
      - ``script`` -- the script to add
    """
    self.renderer.head._script(next_method, self, script)
    return ''


class Style(xhtml_base._HTMLTag):
    pass

@peak.rules.when(xml.add_child, (xhtml_base._HTMLTag, Style))
def add_child(next_method, self, style):
    """Add a <style> to a tag

    In:
      - ``self`` -- the tag
      - ``style`` -- the style to add
    """
    self.renderer.head._style(next_method, self, style)
    return ''


# ----------------------------------------------------------------------------------

class Renderer(xhtml_base.Renderer):
    """The XHTML synchronous renderer
    """
    XML_DOCTYPE = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
    HTML_DOCTYPE = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">'

    head_renderer_factory = HeadRenderer

    # Redefinition of the he HTML tags with actions
    # ---------------------------------------------

    a = TagProp('a', set(xhtml_base.allattrs+xhtml_base.focusattrs+('charset', 'type', 'name', 'href', 'hreflang', 'rel', 'rev', 'shape', 'coords', 'target', 'oncontextmenu')), A)
    area = TagProp('area', set(xhtml_base.allattrs + xhtml_base.focusattrs + ('shape', 'coords', 'href', 'nohref', 'alt', 'target')), A)
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

    script = TagProp('script', set(('id', 'charset', 'type', 'language', 'src', 'defer')), Script)
    style = TagProp('style', set(xhtml_base.i18nattrs+('id', 'type', 'media', 'title')), Style)

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

    def __init__(self, parent=None, session=None, request=None, response=None, callbacks=None, static_url='', static_path='', url='/'):
        """Renderer initialisation

        In:
          - ``parent`` -- parent renderer
          - ``session`` -- the session object
          - ``request`` -- the request object
          - ``response`` -- the response object
          - ``callbacks`` -- the registered actions on the tags
          - ``static_url`` -- url of the static contents of the application
          - ``static_path`` -- path of the static contents of the application
          - ``url`` -- url prefix of the application
        """
        super(Renderer, self).__init__(parent, static_url=static_url)

        if parent is None:
            self.session = session
            self.request = request
            self.response = response
            self._callbacks = callbacks
            self.static_path = static_path
            self.url = url
            self._rendered = set()
        else:
            self.session = parent.session
            self.request = parent.request
            self.response = parent.response
            self._callbacks = parent._callbacks
            self.static_path = parent.static_path
            self.url = parent.url
            self._rendered = parent._rendered

        self.component = None
        self.model = None

    def SyncRenderer(self, *args, **kw):
        """Create an associated synchronous HTML renderer

        Return:
          - a new synchronous renderer
        """
        # If no arguments are given, this renderer becomes the parent of the
        # newly created renderer
        if not args and not kw:
            args = (self,)

        return self.__class__(*args, **kw)

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

    def makeelement(self, tag):
        """Make a tag

        In:
          - ``tag`` -- name of the tag to create

        Return:
          - the new tag
        """
        return self._makeelement(tag, self._html_parser)

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
            source = absolute_url(source, self.static_path)

        return super(Renderer, self).parse_xml(source, fragment, no_leading_text, **kw)

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
        if isinstance(source, basestring):
            source = absolute_url(source, self.static_path)

        parser = ET.XMLParser(**kw) if xhtml else ET.HTMLParser(**kw)
        parser.setElementClassLookup(self._custom_lookup)

        return self._parse_html(parser, source, fragment, no_leading_text, **kw)

    @property
    def doctype(self):
        """Generate the DOCTYPE of the document

        If a doctype was set on the response object, use it
        Else, use the HTML ou XHTML doctypes of this renderer

        Return:
          - the doctype
        """
        response = self.response

        if response.doctype is not None:
            return response.doctype

        return self.XML_DOCTYPE if response.xml_output else self.HTML_DOCTYPE

    @property
    def content_type(self):
        """Generate the content type of the document

        If a content type was set on the response object, use it
        Else, use the HTML ou XHTML content type of this renderer

        Return:
          - the content type
        """
        response = self.response

        if response.content_type:
            return response.content_type

        return 'application/xhtml+xml' if response.xml_output else 'text/html'

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

        # Delete all the previous callbacks registered by this component
        if self._callbacks and (component not in self._rendered):
            self._callbacks.unregister_callbacks(component)

        # Memorize all the rendered components
        self._rendered.add(component)

    def action(self, tag, action, with_request, permissions, subject):
        """Register a synchronous action on a tag

        In:
          - ``tag`` -- the tag
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        """
        tag.sync_action(self, action, with_request, permissions, subject)

    def register_callback(self, priority, f, with_request, render=None):
        """Register an action

        Forward the call to the ``callbacks`` object

        In:
          - ``priority`` - -priority of the action
          - ``f`` -- the action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``render`` -- render method to generate the view after the ``f`` action will be called
        """
        return self._callbacks.register_callback(self.component, priority, f, with_request, render)


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
            form(self.div(self.session.sessionid_in_form(self, self.request, self.response)))

    def add_sessionid_in_url(self, u='', params=None, sep='&'):
        """Add the session and continuation ids into an url

        Forward this call to the sessions manager

        In:
          - ``u`` -- the url
          - ``params`` -- query string of the url

        Return:
          - the completed url
        """
        i = u.find(':')
        if ((i == -1) or not u[:i].isalpha()) and (not u or (u[0] != '/')):
            u = self.url + '/' + u

        if params is None:
            params = ()

        if self.session:
            u += '?' + sep.join(self.session.sessionid_in_url(self.request, self.response) + params)

        return u


class AsyncHeadRenderer(HeadRenderer):
    def __init__(self, static_url):
        """Renderer initialisation

        The ``HeadRenderer`` keeps track of the javascript and css used by every views,
        to be able to concatenate them into the ``<head>`` section.
        """
        super(AsyncHeadRenderer, self).__init__(static_url=static_url)

        self._anonymous_css = []         # CSS
        self._anonymous_javascript = []  # Javascript code

    def _css(self, style):
        """Memorize an in-line anonymous css style

        In:
          - ``style`` -- the css style
        """
        self._anonymous_css.append((self._order, style))
        self._order += 1

    def _javascript(self, script):
        """Memorize an in-line anonymous javascript code

        In:
          - ``script`` -- the javascript code
        """
        self._anonymous_javascript.append((self._order, script))
        self._order += 1

    def _style(self, append, tag, style):
        self._css(style.text or '')

    def _script(self, append, tag, script):
        url = script.get('src')

        if url:
            self.javascript_url(url)
        else:
            self._javascript(script.text or '')

    def _get_anonymous_css(self):
        """Return the list of the in-line anonymous css styles, sorted by order of insertion

        Return:
          - list of css styles
        """
        return [css for (order, css) in sorted(self._anonymous_css)]


    def _get_anonymous_javascript(self):
        """Return the list of anonymous javascript codes, sorted by order of insertion

        Return:
          - list of javascript codes
        """
        return [js for (order, js) in sorted(self._anonymous_javascript)]


@presentation.render_for(AsyncHeadRenderer)
def render(self, h, *args):
    """Generate a javascript view of the head

    In:
      - ``h`` -- the current renderer

    Return:
      - a javascript string
    """
    return "nagare_loadAll(%s, %s, %s, %s, %s, %s)" % (
                                                         ajax.py2js(self._get_named_css(), h),
                                                         ajax.py2js(r'\n'.join(self._get_anonymous_css()), h),
                                                         ajax.py2js(self._get_css_url(), h),
                                                         ajax.py2js(self._get_named_javascript(), h),
                                                         ajax.py2js(';'.join(self._get_anonymous_javascript()), h),
                                                         ajax.py2js(self._get_javascript_url(), h)
                                                      )


class AsyncRenderer(Renderer):
    """The XHTML asynchronous renderer
    """
    head_renderer_factory = AsyncHeadRenderer

    def __init__(self, parent=None, session=None, request=None, response=None, callbacks=None, static_url='', static_path='', url='/', async_header=False):
        """Renderer initialisation

        In:
          - ``parent`` -- parent renderer
          - ``session`` -- the session object
          - ``request`` -- the request object
          - ``response`` -- the response object
          - ``callbacks`` -- the registered actions on the tags
          - ``static_url`` -- url of the static contents of the application
          - ``static_path`` -- path of the static contents of the application
          - ``url`` -- url prefix of the application
          - ``async_header`` -- is the head renderer to create a synchronous or an asynchronous one?
        """
        super(AsyncRenderer, self).__init__(parent, session, request, response, callbacks, static_url, static_path, url)

        if not (parent or async_header):
            self.head = HeadRenderer(static_url=static_url)

        self.async_root = True;
        self.wrapper_to_generate = False    # Add a ``<div>`` around the rendering ?

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

    def AsyncRenderer(self, *args, **kw):
        """Create an associated asynchronous HTML renderer

        Return:
          - a new asynchronous renderer
        """
        # If no arguments are given, this renderer becomes the parent of the
        # newly created renderer
        if not args and not kw:
            args = (self,)

        return self.__class__(*args, **kw)

    def javascript_url(self, url):
        self.head.javascript_url(url)

    def _javascript(self, js):
        self.head._javascript(js)

    def _css(self, style):
        self.head._css(style)

    def action(self, tag, action, with_request, permissions, subject):
        """Register an asynchronous action on a tag

        In:
          - ``tag`` -- the tag
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action ?
          - ``permissions`` -- permissions needed to execute the action
          - ``subject`` -- subject to test the permissions on

        """
        tag.async_action(self, action, with_request, permissions, subject)

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

    print h.html(presentation.render(h.head, None, None, None), h.root).write_htmlstring(pretty_print=True)
