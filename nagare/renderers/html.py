# --
# Copyright (c) 2008-2020 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""The XHTML renderer

This renderer is dedicated to the Nagare framework
"""

import json
import imghdr

import webob
import pkg_resources

from nagare import partial
from nagare.action import ActionBase, Action, Remote, Update

from nagare.renderers.xml import TagProp
from nagare.renderers import xml, html_base


NAGARE_VERSION = pkg_resources.get_distribution('nagare').version


class _HTMLActionTag(html_base.Tag):
    """Base class of all the tags with a ``.action()`` method
    """
    ACTION_ATTR = 'name'

    def set_sync_action(self, action_id, params):
        self.set(
            self.ACTION_ATTR,
            action_id + (('#' + params) if params else '')
        )

    def set_async_action(self, action_id, params):
        self.set_sync_action(action_id, params)

    @partial.max_number_of_args(2)
    def action(self, action, args, with_request=False, **kw):
        """Register an action

        In:
          - ``action`` -- action
          - ``args``, ``kw`` -- ``action`` parameters
          - ``with_request`` -- will the request and response objects be passed to the action?

        Return:
          - ``self``
        """
        self.renderer.register_callback(self, self.ACTION_PRIORITY, action, with_request, *args, **kw)
        return self


class A(html_base.HrefAttribute, _HTMLActionTag):
    """ ``<a>`` tags
    """
    ACTION_ATTR = 'href'
    ACTION_PRIORITY = 5

    def absolute_url(self, url):
        return self.renderer.absolute_url(url)

    def set_sync_action(self, action_id, params):
        """Register a synchronous action

        In:
          - ``renderer`` -- the current renderer
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action?
        """
        params = {'_p': params} if params else {}
        params[action_id] = ''

        href = self.get('href', '')
        href = self.renderer.add_sessionid_in_url(href, params)

        super(A, self).set_sync_action(href, {})

    def set_async_action(self, action_id, params):
        super(A, self).set_async_action(action_id, params)
        self(data_nagare=self.ACTION_PRIORITY)


class Img(html_base.Img, _HTMLActionTag):
    """ ``<img>`` tags
    """
    ACTION_ATTR = 'src'
    ACTION_PRIORITY = 2

    def set_sync_action(self, action_id, params):
        params = {'_p': params} if params else {}
        params[action_id] = ''

        href = self.get('src', '')
        href = self.renderer.add_sessionid_in_url(href, params)

        super(Img, self).set_sync_action(href, {})

    @classmethod
    def generate(cls, request, response, action, with_request, **kw):
        """Generate the image and guess its format

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object
          - ``action`` -- function to call to generate the image data
          - ``with_request`` -- will the request and response objects be passed to the action?

        Return:
          - new response object raised
        """
        e = webob.exc.HTTPOk(headerlist=[('Content-Type', '')])
        img = action(request, e, **kw) if with_request else action(**kw)

        # If no ``Content-Type`` is already set, use the ``imghdr`` module
        # to guess the format of the image
        e.content_type = e.content_type or ('image/' + (imghdr.what(None, img[:32]) or '*'))
        e.body = img

        raise e

    @partial.max_number_of_args(2)
    def action(self, action, args, with_request=False, **kw):
        f = partial.Partial(self.generate, action=action, with_request=with_request, **kw)
        return super(Img, self).action(f, with_request=True, *args, **kw)


class Form(_HTMLActionTag):
    """ The ``<form>`` tag
    """
    PRE_ACTION_PRIORITY = 0
    ACTION_PRIORITY = POST_ACTION_PRIORITY = 4
    DEFAULT_ATTRS = {
        'enctype': 'multipart/form-data',
        'method': 'post',
        'accept-charset': 'utf-8',
        'action': '?'
    }

    def init(self, renderer):
        """Initialisation

        In:
          - ``renderer`` -- the current renderer
        """
        super(Form, self).init(renderer)

        # Set the default attributes: send the form with a POST, in utf-8
        self(self.DEFAULT_ATTRS)

        # Add into the form the hidden fields of the session and continuation ids
        self.renderer.add_sessionid_in_form(self)

    def clean(self):
        """Delete the existing ``<form>`` tags in the child tree
        """
        for form in self.findall('.//form'):
            form.tag = 'div'
            for attr in self.DEFAULT_ATTRS:
                form.attrib.pop(attr, None)

            for e in form.xpath('descendant::*[contains(@class, "nagare-session-data")]'):
                e.getparent().remove(e)

    @partial.max_number_of_args(2)
    def pre_action(self, action, args, with_request=False, **kw):
        """Register an action that will be executed **before** the actions of the
        form elements

        In:
          - ``action`` -- action
          - ``args``, ``kw`` -- ``action`` parameters
          - ``with_request`` -- will the request and response objects be passed to the action?

        Return:
          - ``self``
        """
        self.renderer.register_callback(self, self.PRE_ACTION_PRIORITY, action, with_request, *args, **kw)
        return self

    @partial.max_number_of_args(2)
    def post_action(self, action, args, with_request=False, **kw):
        """Register an action that will be executed **after** the actions of the
        form elements

        In:
          - ``action`` -- action
          - ``args``, ``kw`` -- ``action`` parameters
          - ``with_request`` -- will the request and response object be passed to the action?

        Return:
          - ``self``
        """
        self.renderer.register_callback(self, self.POST_ACTION_PRIORITY, action, with_request, *args, **kw)
        return self

    def set_sync_action(self, action_id, params):
        input_ = self.renderer.input(type='hidden', name=action_id, class_='nagare-generated nagare-session-data')
        self.append(input_)


class TextArea(_HTMLActionTag):
    """ ``<textarea>`` tags
    """
    ACTION_PRIORITY = 1

    @classmethod
    def clean_input(cls, action, args, v, **kw):
        return action(*(args + (v.replace('\r', ''),)), **kw)

    @classmethod
    def clean_input_with_request(cls, action, args, request, response, v, **kw):
        return cls.clean_input(action, (request, response) + args, v, **kw)

    @partial.max_number_of_args(2)
    def action(self, action, args, with_request=False, **kw):
        """Register an action


        In:
          - ``action`` -- action
          - ``args``, ``kw`` -- ``action`` parameters
          - ``with_request`` -- will the request and response object be passed to the action?

        Return:
          - ``self``
        """
        # The content sent to the action will have the '\r' characters deleted
        if not isinstance(action, ActionBase):
            f = self.clean_input_with_request if with_request else self.clean_input
            action = partial.Partial(f, action, args)
            args = ()

        return super(TextArea, self).action(action, with_request=with_request, *args, **kw)

# ----------------------------------------------------------------------------------


class RadioInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=radio`` attributes
    """
    ACTION_ATTR = 'value'
    ACTION_PRIORITY = 2

    def selected(self, flag):
        """(de)Select the tag

        In:
          - ``flag`` -- boolean to deselect / select the tag

        Return:
          - ``self``
        """
        self.attrib.pop('checked', None)

        if flag:
            self.set('checked', 'checked')

        return self


class CheckboxInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=checkbox`` attributes
    """
    ACTION_PRIORITY = 1

    def selected(self, flag):
        """(de)Select the tag

        In:
          - ``flag`` -- boolean to deselect / select the tag

        Return:
          - ``self``
        """
        self.attrib.pop('checked', None)

        if flag:
            self.set('checked', 'checked')

        return self


class SubmitInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=submit`` attributes
    """
    ACTION_PRIORITY = 6

    def set_async_action(self, action_id, params):
        super(SubmitInput, self).set_async_action(action_id, params)
        self.set('data-nagare', str(self.ACTION_PRIORITY))


class FileInput(_HTMLActionTag):
    """ ``<input>`` tags with ``type=file`` attributes
    """
    ACTION_PRIORITY = 1

    def init(self, renderer):
        """Initialisation

        In:
          - ``renderer`` -- the current renderer

        Return:
          - ``self``
        """
        super(FileInput, self).init(renderer)
        self.set('name', 'file')


class ImageInput(html_base.Input, _HTMLActionTag):
    """ ``<input>`` tags with ``type=image`` attributes
    """
    ACTION_PRIORITY = 6

    def set_async_action(self, action_id, params):
        self.set('data-nagare', str(self.ACTION_PRIORITY))


class TextInput(_HTMLActionTag):
    """Dispatcher class for all the ``<input>`` tags
    """
    ACTION_PRIORITY = 1
    TYPES = {
        'radio': RadioInput,
        'checkbox': CheckboxInput,
        'submit': SubmitInput,
        'file': FileInput,
        'image': ImageInput
    }

    def __call__(self, *children, **attrib):
        type_ = attrib.get('type', 'text')
        if type_ not in self.TYPES:
            return super(TextInput, self).__call__(*children, **attrib)

        element = self.TYPES[type_]()
        element.init(self.renderer)
        element.tag = self.tag

        return element(*children, **dict(self.attrib, **attrib))

# ----------------------------------------------------------------------------------


class Option(html_base.Tag):
    """ ``<options>`` tags
    """
    def selected(self, values):
        """(de)Select the tags

        In:
          - ``values`` -- name or list of names of the tags to select

        Return:
          - ``self``
        """
        self.attrib.pop('selected', None)

        if isinstance(values, bool):
            if values:
                self.set('selected', 'selected')
        else:
            if not isinstance(values, (list, tuple, set)):
                values = (values,)

            if self.get('value') in values:
                self.set('selected', 'selected')

        return self


class Select(_HTMLActionTag):
    """ ``<select>`` tags
    """
    @property
    def ACTION_PRIORITY(self):
        return 3 if self.get('multiple') else 1

    @classmethod
    def normalize_input(cls, action, args, v, **kw):
        return action(*(args + (v if isinstance(v, (list, tuple)) else (v,),)), **kw)


class Label(html_base.Tag):
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
        self.set('for', renderer.generate_id('id'))  # Generate a unique value for the ``for`` attribute


class Script(html_base.Script):
    def add_children(self, children, attrib=None):
        children = [
            child.render(self.renderer) if isinstance(child, Remote) else child
            for child in children
        ]

        super(Script, self).add_children(children, attrib)

# ----------------------------------------------------------------------------------


class HeadRenderer(html_base.HeadRenderer):

    def render_async(self):
        """Generate a javascript view of the head

        In:
        - ``h`` -- the current renderer

        Return:
        - a javascript string
        """
        if not any((self._named_css, self._css_url, self._named_javascript, self._javascript_url)):
            return ''

        return "nagare_loadAll(%s, %s, %s, %s)" % (
            json.dumps([
                (name, css, attrs)
                for name, (css, attrs, _)
                in sorted(self._named_css.items(), key=lambda e: e[1][2])
            ]),
            json.dumps([
                (self.absolute_asset_url(url), attrs)
                for url, (attrs, _)
                in sorted(self._css_url.items(), key=lambda e: e[1][1])
            ]),
            json.dumps([
                (name, js, attrs)
                for name, (js, attrs, _)
                in sorted(self._named_javascript.items(), key=lambda e: e[1][2])
            ]),
            json.dumps([
                (self.absolute_asset_url(url), attrs)
                for url, (attrs, _)
                in sorted(self._javascript_url.items(), key=lambda e: e[1][1])
            ])
        )


class _SyncRenderer(object):
    """The XHTML synchronous renderer
    """
    head_renderer_factory = HeadRenderer
    default_action = Action

    # Redefinition of the he HTML tags with actions
    # ---------------------------------------------

    a = TagProp('a', html_base.allattrs | html_base.focusattrs | {
        'charset', 'type', 'name', 'href', 'hreflang', 'rel', 'rev', 'shape', 'coords', 'target', 'oncontextmenu'
    }, A)
    area = TagProp('area', html_base.allattrs | html_base.focusattrs | {
        'shape', 'coords', 'href', 'nohref', 'alt', 'target'
    }, A)
    button = TagProp('button', html_base.allattrs | html_base.focusattrs | {
        'name', 'value', 'type', 'disabled'
    }, SubmitInput)
    form = TagProp('form', html_base.allattrs | {
        'action', 'method', 'name', 'enctype', 'onsubmit', 'onreset', 'accept_charset', 'target'
    }, Form)
    img = TagProp('img', html_base.allattrs | {
        'src', 'alt', 'name', 'longdesc', 'width', 'height', 'usemap', 'ismap'
        'align', 'border', 'hspace', 'vspace', 'lowsrc'
    }, Img)
    input = TagProp('input', html_base.allattrs | html_base.focusattrs | {
        'type', 'name', 'value', 'checked', 'disabled', 'readonly', 'size', 'maxlength', 'src'
        'alt', 'usemap', 'onselect', 'onchange', 'accept', 'align', 'border'
    }, TextInput)
    label = TagProp('label', html_base.allattrs | {'for', 'accesskey', 'onfocus', 'onblur'}, Label)
    option = TagProp('option', html_base.allattrs | {'selected', 'disabled', 'label', 'value'}, Option)
    select = TagProp('select', html_base.allattrs | {
        'name', 'size', 'multiple', 'disabled', 'tabindex', 'onfocus', 'onblur', 'onchange', 'rows'
    }, Select)
    textarea = TagProp('textarea', html_base.allattrs | html_base.focusattrs | {
        'name', 'rows', 'cols', 'disabled', 'readonly', 'onselect', 'onchange', 'wrap'
    }, TextArea)
    script = TagProp('script', {'id', 'charset', 'type', 'language', 'src', 'defer'}, Script)

    _async_root = None

    def __init__(
            self,
            parent=None,
            session_id=None, state_id=None,
            request=None, response=None,
            static_url='', static_path='',
            url='', component=None, view=0,
    ):
        """Renderer initialisation

        In:
          - ``session`` -- the session object
          - ``request`` -- the request object
          - ``response`` -- the response object
          - ``static_url`` -- url of the static contents of the application
          - ``static_path`` -- path of the static contents of the application
          - ``url`` -- url prefix of the application
        """
        super(_SyncRenderer, self).__init__(parent, static_url=static_url)

        if parent is None:
            self.session_id = session_id
            self.state_id = state_id
            self.request = request
            self.response = response
            self.static_path = static_path
            self.url = url
            self.component = component
            self.view = view
        else:
            self.session_id = parent.session_id
            self.state_id = parent.state_id
            self.request = parent.request
            self.response = parent.response
            self.static_path = parent.static_path
            self.url = parent.url
            self.component = component or parent.component
            self.view = view or parent.view

        if (component is not None) and component.url:
            self.url = self.url.rstrip('/') + '/' + component.url

    def SyncRenderer(self, *args, **kw):
        """Create an associated synchronous HTML renderer

        Return:
          - a new synchronous renderer
        """
        # If no arguments are given, this renderer becomes the parent of the
        # newly created renderer
        if not args:
            kw.setdefault('parent', self)

        return self.__class__(*args, **kw)

    def AsyncRenderer(self, *args, **kw):
        """Create an associated asynchronous HTML renderer

        Return:
          - a new asynchronous renderer
        """
        # If no arguments are given, this renderer becomes the parent of the
        # newly created renderer
        if not args:
            kw.setdefault('parent', self)

        return self.async_renderer_factory(*args, **kw)

    @property
    def is_async_root(self):
        return self.parent._async_root

    @property
    def async_root(self):
        async_root = self.is_async_root
        if async_root is None:
            return None, (None, None)

        return (self, async_root) if async_root else self.parent.async_root

    def absolute_url(self, url, url_prefix=None, always_relative=False, **params):
        return super(_SyncRenderer, self).absolute_url(
            url,
            url_prefix if url_prefix is not None else self.url,
            always_relative,
            **params
        )

    def add_sessionid_in_form(self, form):
        """Add the session and continuation ids into a ``<form>``

        In:
          - ``form`` -- the form tag
        """
        if self.session_id is not None:
            form(
                self.div(
                    self.input(name='_s', value=self.session_id, type='hidden'),
                    self.input(name='_c', value='%05d' % self.state_id, type='hidden') if self.state_id is not None else '',
                    class_='nagare-generated nagare-session-data'
                )
            )

    def add_sessionid_in_url(self, url, params):
        """Add the session and continuation ids into an url

        In:
          - ``u`` -- the url
          - ``params`` -- query string of the url

        Return:
          - the completed url
        """
        if self.session_id is not None:
            params['_s'] = self.session_id
            if self.state_id is not None:
                params['_c'] = '%05d' % self.state_id

        return self.absolute_url(url, self.url, always_relative=False, **params)

    def register_callback(self, tag, action_type, action, with_request=False, *args, **kw):
        """Register a (a)synchronous action on a tag

        In:
          - ``tag`` -- the tag
          - ``action`` -- action
          - ``with_request`` -- will the request and response objects be passed to the action?
        """
        component = self.component
        if component is not None:
            if not isinstance(action, ActionBase):
                action = self.default_action(action)

            return action.register(self, component, tag, action_type, self.view or None, with_request, args, kw)

    def start_rendering(self, args, kw):
        pass

    def end_rendering(self, output):
        return output

    def decorate_error(self, element, error=''):
        """During the rendering, highlight an element that has an error

        In:
          - ``element`` -- the element in error
          - ``error`` -- the error text
        """
        if error is None:
            return element

        return self.div(
            self.div(element, class_='nagare-error-input'),
            error and self.div(error, class_='nagare-error-message'),
            class_='nagare-generated nagare-error-field'
        )

    def include_nagare_js(self):
        self.head.javascript_url('/static/nagare/nagare.js?ver={}'.format(NAGARE_VERSION))


class _AsyncRenderer(_SyncRenderer):
    """The XHTML asynchronous renderer
    """
    sync_renderer_factory = None
    default_action = Update
    _async_root = True

    def SyncRenderer(self, *args, **kw):
        """Create an associated synchronous HTML renderer

        Return:
          - a new synchronous renderer
        """
        # If no arguments are given, this renderer becomes the parent of the
        # newly created renderer
        if not args:
            kw.setdefault('parent', self)

        return self.sync_renderer_factory(*args, **kw)

    def AsyncRenderer(self, *args, **kw):
        """Create an associated asynchronous HTML renderer

        Return:
          - a new asynchronous renderer
        """
        # If no arguments are given, this renderer becomes the parent of the
        # newly created renderer
        if not args:
            kw.setdefault('parent', self)

        return self.__class__(*args, **kw)

    def start_rendering(self, args, kw):
        if self.is_async_root:
            self.parent._async_root = args, kw

        super(_AsyncRenderer, self).start_rendering(args, kw)
        self._async_root = False

    def end_rendering(self, output):
        """Method called after a component is rendered

        In:
          - ``output`` -- rendered tree

        Out:
          - rendered tree
        """
        if self.is_async_root:
            if not isinstance(output, xml.Tag):
                output = self.div(output, class_='nagare-generated nagare-async-view')

            id_ = output.get('id', self.id)
            output.set('id', id_)

        return super(_AsyncRenderer, self).end_rendering(output)


class AsyncRenderer(_AsyncRenderer, html_base.Renderer):
    pass


class Renderer(_SyncRenderer, html_base.Renderer):
    async_renderer_factory = AsyncRenderer


AsyncRenderer.sync_renderer_factory = Renderer
