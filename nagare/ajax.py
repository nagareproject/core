#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Asynchronous update objects and Python to javascript transcoder"""

import types, inspect, compiler, cStringIO, re

import peak.rules
import pyjs

from nagare import presentation, namespaces, serializer

YUI_INTERNAL_PREFIX = '/static/nagare/yui/build'
YUI_EXTERNAL_PREFIX = 'http://yui.yahooapis.com/2.9.0/build'

# ---------------------------------------------------------------------------

YUI_PREFIX = YUI_INTERNAL_PREFIX

class ViewToJs(object):
    def __init__(self, js, id, renderer, output):
        """Wrap a view into a javascript code

        In:
          - ``js`` -- name of the function to call, on the client, to change the
            DOM element
          - ``id`` -- id of the DOM element to replace on the client
          - ``renderer`` -- the current renderer
          - ``output`` -- the view (or ``None``)
        """
        self.js = js
        self.id = id
        self.renderer = renderer
        self.output = output


def serialize_body(view_to_js, content_type, doctype):
    """Wrap a view body into a javascript code

    In:
      - ``view_to_js`` -- the view
      - ``content_type`` -- the rendered content type
      - ``doctype`` -- the (optional) doctype
      - ``declaration`` -- is the XML declaration to be outputed ?

    Return:
      - Javascript to evaluate on the client
    """
    # Get the HTML or XHTML of the view
    body = serializer.serialize(view_to_js.output, content_type, doctype, False)[1]

    # Wrap it into a javascript code
    return "%s('%s', %s)" % (view_to_js.js, view_to_js.id, py2js(body, view_to_js.renderer))


@peak.rules.when(serializer.serialize, (ViewToJs,))
def serialize(self, content_type, doctype, declaration):
    """Wrap a view into a javascript code

    In:
      - ``content_type`` -- the rendered content type
      - ``doctype`` -- the (optional) doctype
      - ``declaration`` -- is the XML declaration to be outputed ?

    Return:
      - a tuple ('text/plain', Javascript to evaluate on the client)
    """
    if self.output is None:
        return ('text/plain', '')

    # Get the javascript for the header
    head = presentation.render(self.renderer.head, self.renderer, None, None)

    # Wrap the body and the header into a javascript code
    return ('text/plain', serialize_body(self, content_type, doctype) + '; ' + head)


def javascript_dependencies(renderer):
    head = renderer.head

    head.javascript_url(YUI_PREFIX+'/yahoo/yahoo-min.js')
    head.javascript_url(YUI_PREFIX+'/event/event-min.js')
    head.javascript_url(YUI_PREFIX+'/connection/connection-min.js')
    head.javascript_url(YUI_PREFIX+'/get/get-min.js')

    head.javascript('_nagare_content_type_', 'NAGARE_CONTENT_TYPE="%s"' % ('application/xhtml+xml' if renderer.response.xml_output else 'text/html'))


class Update(object):
    """Asynchronous updater object

    Send a XHR request that can do an action, render a component and finally
    update the HTML with the rendered view
    """
    def __init__(self, render='', action=lambda *args: None, component_to_update=None, with_request=False):
        """Initialisation

        In:
          - ``render`` -- can be:

            - a string -- name of the view that will be rendered on the current
              component
            - a function -- this function will be called and the result sent
              back to the client

          - ``action`` -- action to call

          - ``component_to_update`` -- can be:

            - ``None`` -- the current view will be updated
            - a string -- the DOM id of the HTML to update
            - a tag -- this tag will be updated

          - ``with_request`` -- will the request and response objects be passed to the action ?
        """
        self.render = render
        self.action = action
        self.with_request = with_request
        self.component_to_update = component_to_update

    def _generate_render(self, renderer):
        """Generate the rendering function

        In:
          - ``renderer`` -- the current renderer

        Return:
          - the rendering function
        """
        request = renderer.request

        if request:
            if not request.is_xhr and ('_a' not in request.params):
                javascript_dependencies(renderer)
                renderer.head.javascript_url('/static/nagare/ajax.js')

        js = 'nagare_updateNode'
        component_to_update = self.component_to_update
        if component_to_update is None:
            async_root = renderer.get_async_root()

            # Remember to wrap the root view into a ``<div>``
            component_to_update = async_root.id
            async_root.wrapper_to_generate = True
            js = 'nagare_replaceNode'

        # Get the ``id`` attribute of the target element or, else, generate one
        if isinstance(component_to_update, namespaces.xml._Tag):
            id = component_to_update.get('id')
            if id is None:
                id = renderer.generate_id('id')
                component_to_update.set('id', id)
            component_to_update = id

        render = self.render
        if callable(render):
            render = lambda r, render=render: ViewToJs(js, component_to_update, r, render(r))
        else:
            async_root = renderer.get_async_root()

            render = render if render != '' else async_root.model
            render = lambda r, comp=async_root.component, render=render: ViewToJs(js, component_to_update, r, comp.render(r, model=render))

        return render

    def _generate_replace(self, priority, renderer):
        """Register the action on the server and generate the javascript to
        the client

        In:
          - ``priority`` -- type of the action (see ``callbacks.py``)
          - ``renderer`` -- the current renderer

        Return:
          - a tuple:

            - id of the action registered on the server
            - name of the javascript function to call on the client
            - id of the tag to update on the client
        """
        return renderer.register_callback(priority, self.action, self.with_request, self._generate_render(renderer))

    def generate_action(self, priority, renderer):
        """Generate the javascript action

        In:
          - ``priority`` -- type of the action (see ``callbacks.py``)
          - ``renderer`` -- the current renderer

        Return:
          - the javascript code
        """
        if priority == 1:
            return 'nagare_getAndEval("%s;_a;%s="+get_field_value(this))' % (renderer.add_sessionid_in_url(sep=';'), self._generate_replace(1, renderer))
        elif priority == 4:
            return 'return nagare_postAndEval(this.form, "%s")' % self._generate_replace(4, renderer)
        elif priority == 41:
            return 'return nagare_getAndEval("%s;_a;%s")' % (renderer.add_sessionid_in_url(sep=';'), self._generate_replace(4, renderer))
        elif priority == 2:
            return 'nagare_getAndEval("%s;_a;%s")' % (renderer.add_sessionid_in_url(sep=';'), self._generate_replace(2, renderer))
        elif priority == 5:
            r = 'return nagare_imageInputSubmit(event, this, "%s")' % self._generate_replace(5, renderer)
            renderer.head.javascript_url(YUI_PREFIX+'/dom/dom-min.js')
            return r
        else:
            return ''

# ---------------------------------------------------------------------------

class ViewsToJs(list):
    """A list of ``ViewToJS`` objects
    """
    pass

@peak.rules.when(serializer.serialize, (ViewsToJs,))
def serialize(self, content_type, doctype, declaration):
    """Wrap a view into a javascript code

    In:
      - ``content_type`` -- the rendered content type
      - ``doctype`` -- the (optional) doctype
      - ``declaration`` -- is the XML declaration to be outputed ?

    Return:
      - a tuple ('text/plain', Javascript to evaluate on the client)
    """
    bodies = [serialize_body(view_to_js, content_type, doctype) for view_to_js in self if view_to_js.output is not None]

    if not bodies:
        return ('text/plain', '')

    # Get the javascript for the header
    head = presentation.render(self[0].renderer.head, self[0].renderer, None, None)

    return ('text/plain', '; '.join(bodies) + '; ' + head)


class Updates(Update):
    """A list of ``Update`` objects
    """
    def __init__(self, *updates, **kw):
        """Initialization

        In:
          - ``updates`` -- the list of ``Update`` objects
          - ``action`` -- global action to execute (set by keyword call)
          - ``with_request`` -- will the request and response objects be passed to the global action ? (set by keyword call)
        """
        self._updates = updates
        self._with_request = kw.get('with_request', False)
        self._action = kw.get('action', lambda *args: None)

        super(Updates, self).__init__(action=self.action, with_request=True)

    def action(self, request, response, *args):
        """Execute all the actions of the ``Update`` objects
        """
        if self._with_request:
            self._action(request, response, *args)
        else:
            self._action(*args)

        for update in self._updates:
            if update.with_request:
                update.action(request, response, *args)
            else:
                update.action(*args)

    def _generate_render(self, renderer):
        """Generate the rendering function

        In:
          - ``renderer`` -- the current renderer

        Return:
          - the rendering function
        """
        renders = [update._generate_render(renderer) for update in self._updates]
        return lambda r: ViewsToJs(render(r) for render in renders)

# ---------------------------------------------------------------------------

def str2js(src, namespace):
    """Translate a string with Python code to javascript

    In:
      - ``src`` -- the Python code
      - ``namespace`` -- the namespace of this code

    Return:
      - the javascript code
    """
    output = cStringIO.StringIO()
    pyjs.Translator(namespace, compiler.parse(src), output)

    return output.getvalue()


class JS(object):
    """Transcode a Python function or module to javascript code
    """
    def __init__(self, o):
        """Transcode a Python function or module

        In:
          - ``o`` -- Python function or module to transcode
        """
        if hasattr(o, '_js_name'):
            # Already transcoded
            self.name = o._js_name
            self.javascript = o._js_code
            return

        src = inspect.getsource(o)

        classname = ''
        if isinstance(o, types.MethodType):
            classname = o.im_class.__name__
            o = o.im_func

        if isinstance(o, types.FunctionType):
            if o.__module__ == '__main__':
                self.name = module = classname
            else:
                module = o.__module__.replace('.', '_')
                if classname:
                    module += ('_' + classname)
                self.name = module + '_'

            self.name += o.func_name

            indent = inspect.indentsize(src)
            src = ''.join([s.expandtabs()[indent:] for s in src.splitlines(True)])
        else:
            if o.__name__ == '__main__':
                self.name = module = ''
            else:
                self.name = module = o.__name__.replace('.', '_')

        self.javascript = str2js(src, module)

        # Keep the transcoded javascript
        o._js_name = self.name
        o._js_code = self.javascript

    def generate_action(self, priority, renderer):
        """Include the transcoded javascript into ``<head>``

        In:
           - ``priority`` -- *not used*
           - ``renderer`` -- the current renderer

        Return:
          - javascript fragment of the call to the transcoded function
        """
        renderer.head.javascript_url('/static/nagare/pyjslib.js')
        renderer.head.javascript(self.name, self.javascript)

        return self.name+'(this)'

javascript = JS

# ---------------------------------------------------------------------------

@peak.rules.abstract
def py2js(value, h=None):
    """No default transcodage
    """
    pass

@peak.rules.when(py2js, (types.NoneType,))
def py2js(value, h):
    """Generic method to transcode ``None``

    In:
      - ``value`` -- ``None``
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return 'null'

@peak.rules.when(py2js, (bool,))
def py2js(value, h):
    """Generic method to transcode a boolean

    In:
      - ``value`` -- a boolean
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return str(value).lower()

@peak.rules.when(py2js, (int,))
def py2js(value, h):
    """Generic method to transcode an integer

    In:
      - ``value`` -- an integer
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return str(value)

@peak.rules.when(py2js, (long,))
def py2js(value, h):
    """Generic method to transcode a long integer

    In:
      - ``value`` -- a long integer
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return str(value)

@peak.rules.when(py2js, (float,))
def py2js(value, h):
    """Generic method to transcode a float

    In:
      - ``value`` -- a float
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return str(value)

@peak.rules.when(py2js, (dict,))
def py2js(d, h):
    """Generic method to transcode a dictionary

    In:
      - ``value`` -- a dictionary
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return '{' + ', '.join(['%s : %s' % (py2js(name, h), py2js(value, h)) for (name, value) in d.items()]) + '}'

@peak.rules.when(py2js, ((types.FunctionType, types.MethodType),))
def py2js(value, h):
    """Generic method to transcode a function

    In:
      - ``value`` -- a fonction
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return py2js(JS(value), h)

@peak.rules.when(py2js, (types.ModuleType,))
def py2js(value, h):
    """Generic method to transcode a module

    In:
      - ``value`` -- a module
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return py2js(JS(value), h)

@peak.rules.when(py2js, (JS,))
def py2js(value, h):
    """Generic method to transcode an already transcoded function

    In:
      - ``value`` -- a transcoded fonction
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    if h is not None:
        h.head.javascript_url('/static/nagare/pyjslib.js')

    return value.javascript

@peak.rules.when(py2js, (unicode,))
def py2js(value, h):
    """Generic method to transcode an unicode string

    In:
      - ``value`` -- an unicode string
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return py2js(value.encode('utf-8'), h)

not_ascii = re.compile(r'\\x(..)')

@peak.rules.when(py2js, (str,))
def py2js(value, h):
    """Generic method to transcode a string

    In:
      - ``value`` -- a string
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return not_ascii.sub(lambda m: chr(int(m.group(1), 16)), `value`)

@peak.rules.when(py2js, (list,))
def py2js(l, h):
    """Generic method to transcode a list

    In:
      - ``value`` -- a list
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return '[' + ', '.join([py2js(value, h) for value in l]) + ']'

@peak.rules.when(py2js, (tuple,))
def py2js(value, h):
    """Generic method to transcode a tuple

    In:
      - ``value`` -- a tuple
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return py2js(list(value), h)

class js(str):
    """A javascript code object
    """
    pass

@peak.rules.when(py2js, (js,))
def render(self, h):
    """Generic method to transcode a javascript code

    In:
      - ``value`` -- a javascript code
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return str(self)
