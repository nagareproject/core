# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Add ``<html><head><body>`` around a tree"""

import types

from lxml import etree

from nagare import presentation


def search_element(element_name, l):
    """Search an element with ``element_name`` name as the first element in ``l``

    Skip the comments and processing instructions at the start of ``l``

    In:
      - ``element_name`` -- name of the element to search
      - ``l`` -- list of elements

    Return:
      - if found: (position of the next element, element found)
      - else: (0, None)
    """
    for i, element in enumerate(l):
        if isinstance(element, (etree._Comment, etree._ProcessingInstruction)):
            continue

        if isinstance(element, etree._Element) and element.tag.endswith(element_name):
            return i + 1, element

    return 0, None


def wrap(content_type, h, content):
    """Add the tags ``<html>``, ``<head>`` and ``<body>`` is they don't exist

    In:
      - ``content_type`` -- the content type to send to the browser
      - ``h`` -- the current renderer
      - ``content`` -- the rendered tree

    Return:
      - new tree with ``<html>``, ``<head>`` and ``<body>``
    """
    if 'html' not in content_type:
        return content

    if h.response.xml_output:
        h.namespaces = {None: 'http://www.w3.org/1999/xhtml'}

    if not isinstance(content, (list, tuple, types.GeneratorType)):
        content = [content]

    i, html = search_element('html', content)
    if html is None:
        html = content

    j, head = search_element('head', html)
    _, body = search_element('body', html[j:])

    if body is None:
        # No ``<body>`` found, add it
        html[j:] = [h.body(html[j:])]

    if head is None:
        # No ``<head>`` found, add it
        head = h.head.head
        html.insert(0, head)

    if i == 0:
        # No ``<html>`` found, add it
        content = h.html(content)

    head1 = presentation.render(h.head, None, None, None)  # The automatically generated ``<head>``

    url = h.request.upath_info.strip('/')
    if url and not head1.xpath('./link[@rel="canonical"]'):
        head1.append(h.head.link(rel='canonical', href=h.request.uscript_name + '/' + url))

    # Merge the attributes and child of the automatically generated ``<head>``
    head.attrib.update(head1.attrib.items())
    head.add_child(head1[:])

    return content
