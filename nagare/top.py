#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Add ``<html><head><body>`` around a tree"""

#import pkg_resources

from nagare import presentation
from nagare.namespaces import xhtml_base

#VERSION = pkg_resources.get_distribution('nagare').version

def wrap(content_type, h, body):
    """Add the tags is they don't exist or merge them into the existing ones
    
    In:
      - ``content_type`` -- the content type to send to the browser
      - ``h`` -- the current renderer
      - ``body`` -- the rendered tree
      
    Return:
      - new tree with ``<html>``, ``<head>`` and ``<body>``
    """
    if (content_type is None) or ('html' in content_type):
        # Add the tags only for a (x)html content
        
        if not isinstance(body, xhtml_base._HTMLTag) or not body.tag.endswith('html'):
            # No ``<html>`` found, add it
            h.namespaces = { None : 'http://www.w3.org/1999/xhtml' }
            if not isinstance(body, xhtml_base._HTMLTag) or not body.tag.endswith('body'):
                # No ``<body>`` found, add it
                body = h.body(body)
            body = h.html(body)
        
        head1 = presentation.render(h.head, None, None, None) # The automatically generated ``<head>``
        head2 = body[0]
    
        if not head2.tag.endswith('head'):
            # No ``<head>`` found, add the automatically generated ``<head>``
            body.insert(0, head1)
        else:
            # ``<head>`` found, merge the attributes and child of the automatically
            # generated ``<head>`` to it
            head2.attrib.update(head1.attrib.items())
            head2.add_child(head1[:])
    
    return body
