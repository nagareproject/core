#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Asynchronous update objects and Python to javascript transcoder"""

import types
import inspect
import compiler
import StringIO

import peak.rules
import pyjs

from nagare import presentation, namespaces, serializer

YUI_INTERNAL_PREFIX = '/static/nagare/yui/build'
YUI_EXTERNAL_PREFIX = 'http://yui.yahooapis.com/2.5.2/build'

# ---------------------------------------------------------------------------

YUI_PREFIX = YUI_INTERNAL_PREFIX

class ViewToJs(object):
    def __init__(self, js, id, renderer, output):
        """Wrap a view into a callable javascript
        
        In:
          - ``js`` -- name of the function to call, on the client, to change the
            DOM element
          - ``id`` -- id of the DOM element to replace on the client
          - ``renderer`` -- the current renderer
          - ``output`` -- the view
          
        Return:
          - Javascript to be evaluated on the client
        """
        self.js = js
        self.id = id
        self.renderer = renderer
        self.output = output

@peak.rules.when(serializer.serialize, (ViewToJs,))
def serialize(self, request, response, declaration):
    """Wrap a view into a callable javascript

    In:
      - ``output`` -- the text
      - ``request`` -- the web request object
      - ``response`` -- the web response object      
      - ``declaration`` -- has the declaration to be outputed ?
      
    Return:
      - the content

    Return:
      - Javascript to be evaluated on the client
    """
    # Get the javascript for the header
    head = presentation.render(self.renderer.head, self.renderer, None, model='async')
    
    # Get the HTML or XHTML of the view
    body = serializer.serialize(self.output, request, response, False)
    body = body.replace("'", r"\'").replace('\n', '')

    response.content_type = 'text/plain'
    
    # Wrap all into a javascript code
    return "%s('%s', '%s'); %s" % (self.js, self.id, body, head)


def view_to_js(js, id, comp, renderer, model):
    """Render components and wrap the generate view into a callable javascript
    
    In:
      - ``js`` -- name of the function to call, on the client, to change the
        DOM element    
      - ``id`` -- id of the DOM element to replace on the client
      - ``comp`` -- component to renderer
      - ``renderer`` -- the current renderer
      - ``model`` -- name of the view to render
      
    Return:
      - Javascript to evaluate on the client
    """
    return ViewToJs(js, id, renderer, comp.render(namespaces.xhtml.AsyncRenderer(renderer), model=model))


class Update(object):
    """Asynchronous updater objects
    
    Send a XHR request that can do an action, render a component and finally
    update the HTML with the rendered view
    """
    def __init__(self, render=None, action=lambda: None, component_to_update=None):
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
        """
        self.render = render
        self.action = action
        self.component_to_update = component_to_update

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
        request = renderer.request
        
        if request:
            if not request.is_xhr and ('_a' not in request.params):
                head = renderer.head
                
                head.javascript_url(YUI_PREFIX+'/yahoo/yahoo-min.js')
                head.javascript_url(YUI_PREFIX+'/event/event-min.js')
                head.javascript_url(YUI_PREFIX+'/connection/connection-min.js')
                
                head.javascript('_nagare_content_type_', 'NAGARE_CONTENT_TYPE="%s"' % ('application/xhtml+xml' if request.xhtml_output else 'text/html'))
                head.javascript_url('/static/nagare/ajax.js')

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
        if render is None:
            render = lambda r: ''
        elif callable(render):
            render = lambda r, render=render: ViewToJs(js, component_to_update, r, render(r))
        else:
            async_root = renderer.get_async_root()
            render = lambda r, comp=async_root.component, render=async_root.model: view_to_js(js, component_to_update, comp, r, render)
            
        return renderer.register_callback(priority, self.action, render)

    def generate_action(self, priority, renderer):
        """Generate the javascript action
        
        In:
          - ``priority`` -- type of the action (see ``callbacks.py``)
          - ``renderer`` -- the current renderer
          
        Return:
          - the javascript code
        """
        if priority == 1:
            return 'nagare_getAndEval("%s;_a;%s="+escape(this.value))' % (renderer.add_sessionid_in_url(sep=';'), self._generate_replace(1, renderer))
        elif priority == 4:
            return 'return nagare_postAndEval(this.form, "%s")' % self._generate_replace(4, renderer)
        elif priority == 41:
            return 'nagare_getAndEval("%s;_a;%s")' % (renderer.add_sessionid_in_url(sep=';'), self._generate_replace(4, renderer))
        elif priority == 2:
            return 'nagare_getAndEval("%s;_a;%s")' % (renderer.add_sessionid_in_url(sep=';'), self._generate_replace(2, renderer))
        else:
            return ''


class JS(object):
    """Transcode a Python function to javascript
    """
    def __init__(self, f):
        """Transcode the Python function
        
        In:
          - ``f`` -- Python function to transcode
        """
        if hasattr(f, '_js_name'):
            # Function already transcoded
            self.name = f._js_name
            self.javascript = f._js_code
        else:
            if f.__module__ == '__main__':
                self.name = module = ''
            else:
                module = f.__module__.replace('.', '_')
                self.name = module + '_'

            self.name += f.func_name

            src = inspect.getsource(f)
            indent = inspect.indentsize(src)
            src = ''.join([s.expandtabs()[indent:] for s in src.splitlines(True)])

            output = StringIO.StringIO()
            pyjs.Translator(module, compiler.parse(src), output)
            self.javascript = output.getvalue()

            # Keep the transcoded javascript
            f._js_name = self.name
            f._js_code = self.javascript

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
def py2js(value, h):
    """No default transcodage
    """
    pass

@peak.rules.when(py2js, (types.NoneType,))
def py2js(value, h=None):
    """Generic method to transcode ``None``
    
    In:
      - ``value`` -- ``None``
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return 'null'

@peak.rules.when(py2js, (bool,))
def py2js(value, h=None):
    """Generic method to transcode a boolean
    
    In:
      - ``value`` -- a boolean
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return str(value).lower()

@peak.rules.when(py2js, (int,))
def py2js(value, h=None):
    """Generic method to transcode an integer
    
    In:
      - ``value`` -- an integer
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return str(value)

@peak.rules.when(py2js, (float,))
def py2js(value, h=None):
    """Generic method to transcode a float
    
    In:
      - ``value`` -- a float
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """
    return str(value)

@peak.rules.when(py2js, (dict,))
def py2js(d, h=None):
    """Generic method to transcode a dictionary
    
    In:
      - ``value`` -- a dictionary
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """    
    return '{ ' + ', '.join(['%s : %s' % (name, py2js(value, h)) for (name, value) in d.items()]) + '}'

@peak.rules.when(py2js, (types.FunctionType,))
def py2js(value, h=None):
    """Generic method to transcode a function
    
    In:
      - ``value`` -- a fonction
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """    
    if h is not None:
        h.head.javascript_url('/static/nagare/pyjslib.js')

    return py2js(JS(value), h)

@peak.rules.when(py2js, (JS,))
def py2js(value, h):
    """Generic method to transcode an alread transcoded function
    
    In:
      - ``value`` -- a transcoded fonction
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """    
    return value.javascript

@peak.rules.when(py2js, (basestring,))
def py2js(value, h):
    """Generic method to transcode a string
    
    In:
      - ``value`` -- a string
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """    
    return '"'+value+'"'

@peak.rules.when(py2js, (list,))
def py2js(l, h):
    """Generic method to transcode a list
    
    In:
      - ``value`` -- a list
      - ``h`` -- the current renderer

    Return:
      - transcoded javascript
    """    
    return '[ ' + ', '.join([py2js(value, h) for value in l]) + ']'

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
