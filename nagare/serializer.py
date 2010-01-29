#--
# Copyright (c) 2008, 2009, 2010 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Generate the content to return to the browser"""

import peak.rules
import lxml.html

from nagare.namespaces import xml, xhtml_base

@peak.rules.abstract
def serialize(output, request, response, declaration):
    """Generic method to generate the content for the browser

    *no default implementation*

    In:
      - ``output`` -- the rendered content
      - ``request`` -- the web request object
      - ``response`` -- the web response object
      - ``declaration`` -- has the declaration to be outputed ?

    Return:
      - the content
    """
    pass


@peak.rules.when(serialize, (xhtml_base._HTMLTag,))
def serialize(output, request, response, declaration):
    """Generic method to generate (X)HTML from a tree

    In:
      - ``output`` -- the tree
      - ``request`` -- the web request object
      - ``response`` -- the web response object
      - ``declaration`` -- has the declaration to be outputed ?

    Return:
      - the content
    """
    if 'xmlns' in output.attrib:
        # Let ``lxml`` generate the correct namespaces
        del output.attrib['xmlns']

    content_type = request.content_type

    if response.xhtml_output or (content_type and content_type.startswith('application/xhtml+xml')):
        # The browser accepts XHTML
        response.content_type = 'application/xhtml+xml'

        r = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n' if declaration else ''
        return r + output.write_xmlstring()
    else:
        # The browser accepts HTML only
        response.content_type = 'text/html'
        lxml.html.xhtml_to_html(output)

        r = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n' if declaration else ''
        return r + output.write_htmlstring(pretty_print=True)


@peak.rules.when(serialize, (xml._Tag,))
def serialize(output, request, response, declaration):
    """Generic method to generate XML from a tree

    In:
      - ``output`` -- the tree
      - ``request`` -- the web request object
      - ``response`` -- the web response object
      - ``declaration`` -- has the declaration to be outputed ?

    Return:
      - the content
    """
    response.content_type = 'text/xml'

    r = '<?xml version="1.0" encoding="UTF-8"?>\n' if declaration else ''
    return r + output.write_xmlstring()


@peak.rules.when(serialize, (str,))
def serialize(output, request, response, declaration):
    """Generic method to generate a text (or a binary content)

    In:
      - ``output`` -- the text
      - ``request`` -- the web request object
      - ``response`` -- the web response object
      - ``declaration`` -- has the declaration to be outputed ?

    Return:
      - the content
    """
    if not response.content_type:
        response.content_type = 'text/plain'

    return output


@peak.rules.when(serialize, (unicode,))
def serialize(output, request, response, declaration):
    """Generic method to generate a text from unicode

    In:
      - ``output`` -- the text
      - ``request`` -- the web request object
      - ``response`` -- the web response object
      - ``declaration`` -- has the declaration to be outputed ?

    Return:
      - the content
    """
    if not response.content_type:
        response.content_type = 'text/plain'

    return output.encode('utf-8')
