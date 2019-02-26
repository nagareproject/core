# --
# Copyright (c) 2008-2019 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""The XHTML5 renderer
"""

from nagare.renderers.xml import TagProp
from nagare.renderers import html_base, html5_base, html


class Source(html_base.SrcAttribute):
    """The <source> tag
    """
    ASSET_ATTR = 'src'


class _Renderer(html5_base.Renderer):
    """The XHTML5 synchronous renderer
    """
    source = TagProp('source', factory=Source)


class Renderer(html._SyncRenderer, _Renderer):
    pass


class AsyncRenderer(html._AsyncRenderer, _Renderer):
    sync_renderer_factory = Renderer


Renderer.async_renderer_factory = AsyncRenderer
