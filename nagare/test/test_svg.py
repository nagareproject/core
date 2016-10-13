# Encoding: utf-8

#--
# Copyright (c) 2008-2016 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import unittest

from nagare.namespaces.svg import SVGRenderer


class SVG(unittest.TestCase):
    def test_attributes(self):
        all_attribs = ('a', 'altGlyph', 'altGlyphDef', 'altGlyphItem', 'animate', 'animateColor', 'animateMotion',
                       'animateTransform', 'circle', 'clipPath', 'color-profile', 'cursor', 'defs', 'desc', 'ellipse',
                       'feBlend', 'feColorMatrix', 'feComponentTransfer', 'feComposite', 'feConvolveMatrix',
                       'feDiffuseLighting', 'feDisplacementMap', 'feDistantLight', 'feFlood', 'feFuncA', 'feFuncB',
                       'feFuncG', 'feFuncR', 'feGaussianBlur', 'feImage', 'feMerge', 'feMergeNode', 'feMorphology',
                       'feOffset', 'fePointLight', 'feSpecularLighting', 'feSpotLight', 'feTile', 'feTurbulence',
                       'filter', 'font', 'font-face', 'font-face-format', 'font-face-name', 'font-face-src',
                       'font-face-uri', 'foreignObject', 'g', 'glyph', 'glyphRef', 'hkern', 'image', 'line',
                       'linearGradient', 'marker', 'mask', 'metadata', 'missing-glyph', 'mpath', 'path', 'pattern',
                       'polygon', 'polyline', 'radialGradient', 'rect', 'script', 'set', 'stop', 'style', 'svg',
                       'switch', 'symbol', 'text', 'textPath', 'view', 'title', 'tref', 'vkern', 'tspan', 'use')
        for attr in all_attribs:
            attr_name = attr.replace('-', '_')
            attrib = SVGRenderer.__dict__.get(attr_name)
            self.assertIsNotNone(attrib, '{} not found in SVGRenderer'.format(attr))
            self.assertEqual(attrib._name, attr, '{} has wrong name in SVGRenderer'.format(attr))
