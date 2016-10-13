#--
# Copyright (c) 2008-2016 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""The SVG renderer
"""

from nagare.namespaces.xml import XmlRenderer, TagProp


ANIMATION_ADDITION_ATTRIBUTES = ('additive', 'accumulate')
ANIMATION_ATTRIBUTE_TARGET_ATTRIBUTES = ('attributeType', 'attributeName')
ANIMATION_EVENT_ATTRIBUTES = ('onbegin', 'onend', 'onload', 'onrepeat')
ANIMATION_TIMING_ATTRIBUTES = ('begin', 'dur', 'end', 'min', 'max', 'restart', 'repeatCount', 'repeatDur', 'fill')
ANIMATION_VALUE_ATTRIBUTES = ('calcMode', 'values', 'keyTimes', 'keySplines', 'from', 'to', 'by', 'autoReverse',
                              'accelerate', 'decelerate')
CONDITIONAL_PROCESSING_ATTRIBUTES = ('requiredExtensions', 'requiredFeatures', 'systemLanguage')
CORE_ATTRIBUTES = ('id', 'xml:base', 'xml:lang', 'xml:space', 'tabindex')
DOCUMENT_EVENT_ATTRIBUTES = ('onabort', 'onerror', 'onresize', 'onscroll', 'onunload', 'onzoom')
FILTER_PRIMITIVE_ATTRIBUTES = ('height', 'result', 'width', 'x', 'y')
GRAPHICAL_EVENT_ATTRIBUTES = (
    'onactivate', 'onclick', 'onfocusin', 'onfocusout', 'onload', 'onmousedown', 'onmousemove', 'onmouseout',
    'onmouseover', 'onmouseup')
PRESENTATION_ATTRIBUTES = (
    'alignment-baseline', 'baseline-shift', 'clip', 'clip-path', 'clip-rule', 'color', 'color-interpolation',
    'color-interpolation-filters', 'color-profile', 'color-rendering', 'cursor', 'direction', 'display',
    'dominant-baseline', 'enable-background', 'fill', 'fill-opacity', 'fill-rule', 'filter', 'flood-color',
    'flood-opacity', 'font-family', 'font-size', 'font-size-adjust', 'font-stretch', 'font-style', 'font-variant',
    'font-weight', 'glyph-orientation-horizontal', 'glyph-orientation-vertical', 'image-rendering', 'kerning',
    'letter-spacing', 'lighting-color', 'marker-end', 'marker-mid', 'marker-start', 'mask', 'opacity', 'overflow',
    'pointer-events', 'shape-rendering', 'stop-color', 'stop-opacity', 'stroke', 'stroke-dasharray',
    'stroke-dashoffset', 'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit', 'stroke-opacity', 'stroke-width',
    'text-anchor', 'text-decoration', 'text-rendering', 'unicode-bidi', 'visibility', 'word-spacing', 'writing-mode')
TRANSFER_FUNCTION_ATTRIBUTES = ('type', 'tableValues', 'slope', 'intercept', 'amplitude', 'exponent', 'offset')
XLINK_ATTRIBUTES = ('xlink:href', 'xlink:type', 'xlink:role', 'xlink:arcrole', 'xlink:title', 'xlink:show',
                    'xlink:actuate')


def merge_attrs(*tuples):
    return set(sum(tuples, ()))


class SVGRenderer(XmlRenderer):
    doctype = 'svg'
    content_type = 'image/svg+xml'

    def __init__(self, parent=None):
        super(SVGRenderer, self).__init__(parent)
        self.namespaces = {'svg': 'http://www.w3.org/2000/svg'}
        self._set_default_namespace('svg')

    a = TagProp('a', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                 CORE_ATTRIBUTES,
                                 GRAPHICAL_EVENT_ATTRIBUTES,
                                 PRESENTATION_ATTRIBUTES,
                                 XLINK_ATTRIBUTES,
                                 ('class', 'style', 'externalResourcesRequired', 'transform')))
    altGlyph = TagProp('altGlyph', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                               CORE_ATTRIBUTES,
                                               GRAPHICAL_EVENT_ATTRIBUTES,
                                               PRESENTATION_ATTRIBUTES,
                                               XLINK_ATTRIBUTES,
                                               ('class', 'style', 'externalResourcesRequired')))
    altGlyphDef = TagProp('altGlyphDef', merge_attrs(CORE_ATTRIBUTES))
    altGlyphItem = TagProp('altGlyphItem', merge_attrs(CORE_ATTRIBUTES))
    animate = TagProp('animate', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                             CORE_ATTRIBUTES,
                                             ANIMATION_EVENT_ATTRIBUTES,
                                             XLINK_ATTRIBUTES,
                                             ANIMATION_ATTRIBUTE_TARGET_ATTRIBUTES,
                                             ANIMATION_TIMING_ATTRIBUTES,
                                             ANIMATION_VALUE_ATTRIBUTES,
                                             ANIMATION_ADDITION_ATTRIBUTES,
                                             ('externalResourcesRequired', 'attributeName', 'attributeType', 'from',
                                              'to', 'dur', 'repeatCount')))
    animateColor = TagProp('animateColor', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                                       CORE_ATTRIBUTES,
                                                       ANIMATION_EVENT_ATTRIBUTES,
                                                       XLINK_ATTRIBUTES,
                                                       ANIMATION_ATTRIBUTE_TARGET_ATTRIBUTES,
                                                       ANIMATION_TIMING_ATTRIBUTES,
                                                       ANIMATION_VALUE_ATTRIBUTES,
                                                       ANIMATION_ADDITION_ATTRIBUTES,
                                                       ('externalResourcesRequired',),
                                                       ('by', 'from', 'to')))
    animateMotion = TagProp('animateMotion', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                                         CORE_ATTRIBUTES,
                                                         ANIMATION_EVENT_ATTRIBUTES,
                                                         XLINK_ATTRIBUTES,
                                                         ANIMATION_ATTRIBUTE_TARGET_ATTRIBUTES,
                                                         ANIMATION_TIMING_ATTRIBUTES,
                                                         ANIMATION_VALUE_ATTRIBUTES,
                                                         ANIMATION_ADDITION_ATTRIBUTES,
                                                         ('externalResourcesRequired',),
                                                         ('calcMode', 'path', 'keyPoints', 'rotate', 'origin')))
    animateTransform = TagProp('animateTransform', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                                               CORE_ATTRIBUTES,
                                                               ANIMATION_EVENT_ATTRIBUTES,
                                                               XLINK_ATTRIBUTES,
                                                               ANIMATION_ATTRIBUTE_TARGET_ATTRIBUTES,
                                                               ANIMATION_TIMING_ATTRIBUTES,
                                                               ANIMATION_VALUE_ATTRIBUTES,
                                                               ANIMATION_ADDITION_ATTRIBUTES,
                                                               ('externalResourcesRequired',),
                                                               ('by', 'from', 'to', 'type')))
    circle = TagProp('circle', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                           CORE_ATTRIBUTES,
                                           GRAPHICAL_EVENT_ATTRIBUTES,
                                           ('class', 'style', 'externalResourcesRequired', 'transform', 'cx', 'cy',
                                            'r')))
    clipPath = TagProp('clipPath', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                               CORE_ATTRIBUTES,
                                               PRESENTATION_ATTRIBUTES,
                                               ('class', 'style', 'externalResourcesRequired', 'transform',
                                                'clipPathUnits')))
    color_profile = TagProp('color-profile', merge_attrs(CORE_ATTRIBUTES,
                                                         XLINK_ATTRIBUTES,
                                                         ('local', 'name', 'rendering-intent', 'xlink:href')))
    cursor = TagProp('cursor', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                           CORE_ATTRIBUTES,
                                           XLINK_ATTRIBUTES,
                                           ('externalResourcesRequired', 'x', 'y', 'xlink:href')))
    defs = TagProp('defs', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                       CORE_ATTRIBUTES,
                                       GRAPHICAL_EVENT_ATTRIBUTES,
                                       PRESENTATION_ATTRIBUTES,
                                       ('class', 'style', 'externalResourcesRequired', 'transform')))
    desc = TagProp('desc', merge_attrs(CORE_ATTRIBUTES,
                                       ('class', 'style')))
    ellipse = TagProp('ellipse', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                             CORE_ATTRIBUTES,
                                             GRAPHICAL_EVENT_ATTRIBUTES,
                                             ('class', 'style', 'externalResourcesRequired', 'transform', 'cx', 'cy',
                                              'rx', 'ry')))
    feBlend = TagProp('feBlend', merge_attrs(CORE_ATTRIBUTES,
                                             PRESENTATION_ATTRIBUTES,
                                             FILTER_PRIMITIVE_ATTRIBUTES,
                                             ('class', 'style', 'in', 'in2', 'mode')))
    feColorMatrix = TagProp('feColorMatrix', merge_attrs(CORE_ATTRIBUTES,
                                                         PRESENTATION_ATTRIBUTES,
                                                         FILTER_PRIMITIVE_ATTRIBUTES,
                                                         ('class', 'style', 'in', 'type', 'values')))
    feComponentTransfer = TagProp('feComponentTransfer',
                                  merge_attrs(CORE_ATTRIBUTES,
                                              PRESENTATION_ATTRIBUTES,
                                              FILTER_PRIMITIVE_ATTRIBUTES,
                                              ('class', 'style', 'in')))
    feComposite = TagProp('feComposite', merge_attrs(CORE_ATTRIBUTES,
                                                     PRESENTATION_ATTRIBUTES,
                                                     FILTER_PRIMITIVE_ATTRIBUTES,
                                                     ('class', 'style', 'in', 'in2', 'operator', 'k1', 'k2', 'k3',
                                                      'k4')))
    feConvolveMatrix = TagProp('feConvolveMatrix',
                               merge_attrs(CORE_ATTRIBUTES,
                                           PRESENTATION_ATTRIBUTES,
                                           FILTER_PRIMITIVE_ATTRIBUTES,
                                           ('class', 'style', 'in', 'order', 'kernelMatrix', 'divisor', 'bias',
                                            'targetX', 'targetY', 'edgeMode', 'kernelUnitLength', 'preserveAlpha')))
    feDiffuseLighting = TagProp('feDiffuseLighting',
                                merge_attrs(CORE_ATTRIBUTES,
                                            PRESENTATION_ATTRIBUTES,
                                            FILTER_PRIMITIVE_ATTRIBUTES,
                                            ('class', 'style', 'in', 'surfaceScale', 'diffuseConstant',
                                             'kernelUnitLength')))
    feDisplacementMap = TagProp('feDisplacementMap',
                                merge_attrs(CORE_ATTRIBUTES,
                                            PRESENTATION_ATTRIBUTES,
                                            FILTER_PRIMITIVE_ATTRIBUTES,
                                            ('class', 'style', 'in', 'in2', 'scale', 'xChannelSelector',
                                             'yChannelSelector')))
    feDistantLight = TagProp('feDistantLight', merge_attrs(CORE_ATTRIBUTES,
                                                           ('azimuth', 'elevation')))
    feFlood = TagProp('feFlood', merge_attrs(CORE_ATTRIBUTES,
                                             PRESENTATION_ATTRIBUTES,
                                             FILTER_PRIMITIVE_ATTRIBUTES,
                                             ('class', 'style', 'flood-color', 'flood-opacity')))
    feFuncA = TagProp('feFuncA', merge_attrs(CORE_ATTRIBUTES,
                                             TRANSFER_FUNCTION_ATTRIBUTES))
    feFuncB = TagProp('feFuncB', merge_attrs(CORE_ATTRIBUTES,
                                             TRANSFER_FUNCTION_ATTRIBUTES))
    feFuncG = TagProp('feFuncG', merge_attrs(CORE_ATTRIBUTES,
                                             TRANSFER_FUNCTION_ATTRIBUTES))
    feFuncR = TagProp('feFuncR', merge_attrs(CORE_ATTRIBUTES,
                                             TRANSFER_FUNCTION_ATTRIBUTES))
    feGaussianBlur = TagProp('feGaussianBlur', merge_attrs(CORE_ATTRIBUTES,
                                                           PRESENTATION_ATTRIBUTES,
                                                           FILTER_PRIMITIVE_ATTRIBUTES,
                                                           ('class', 'style', 'in', 'stdDevation')))
    feImage = TagProp('feImage',
                      merge_attrs(CORE_ATTRIBUTES,
                                  PRESENTATION_ATTRIBUTES,
                                  FILTER_PRIMITIVE_ATTRIBUTES,
                                  XLINK_ATTRIBUTES,
                                  ('class', 'style', 'externalResourcesRequired', 'preserveAspectRatio', 'xlink:href')))
    feMerge = TagProp('feMerge',
                      merge_attrs(CORE_ATTRIBUTES,
                                  PRESENTATION_ATTRIBUTES,
                                  FILTER_PRIMITIVE_ATTRIBUTES,
                                  ('class', 'style')))
    feMergeNode = TagProp('feMergeNode', merge_attrs(CORE_ATTRIBUTES,
                                                     ('in',)))
    feMorphology = TagProp('feMorphology', merge_attrs(CORE_ATTRIBUTES,
                                                       PRESENTATION_ATTRIBUTES,
                                                       FILTER_PRIMITIVE_ATTRIBUTES,
                                                       ('class', 'style', 'in', 'operator', 'radius')))
    feOffset = TagProp('feOffset', merge_attrs(CORE_ATTRIBUTES,
                                               PRESENTATION_ATTRIBUTES,
                                               FILTER_PRIMITIVE_ATTRIBUTES,
                                               ('class', 'style', 'in', 'dx', 'dy')))
    fePointLight = TagProp('fePointLight', merge_attrs(CORE_ATTRIBUTES,
                                                       ('x', 'y', 'z')))
    feSpecularLighting = TagProp('feSpecularLighting',
                                 merge_attrs(CORE_ATTRIBUTES,
                                             PRESENTATION_ATTRIBUTES,
                                             FILTER_PRIMITIVE_ATTRIBUTES,
                                             ('class', 'style', 'in', 'surfaceScale', 'specularConstant',
                                              'specularExponent', 'kernelUnitLength')))
    feSpotLight = TagProp('feSpotLight',
                          merge_attrs(CORE_ATTRIBUTES,
                                      ('x', 'y', 'z', 'pointsAtX', 'pointsAtY', 'pointsAtZ', 'specularExponent',
                                       'limitingConeAngle')))
    feTile = TagProp('feTile', merge_attrs(CORE_ATTRIBUTES,
                                           PRESENTATION_ATTRIBUTES,
                                           FILTER_PRIMITIVE_ATTRIBUTES,
                                           ('class', 'style', 'in')))
    feTurbulence = TagProp('feTurbulence',
                           merge_attrs(CORE_ATTRIBUTES,
                                       PRESENTATION_ATTRIBUTES,
                                       FILTER_PRIMITIVE_ATTRIBUTES,
                                       ('class', 'style', 'baseFrequency', 'numOctaves', 'seed', 'stitchTiles',
                                        'type')))
    filter = TagProp('filter', merge_attrs(CORE_ATTRIBUTES,
                                           PRESENTATION_ATTRIBUTES,
                                           XLINK_ATTRIBUTES,
                                           ('class', 'style', 'externalResourcesRequired', 'x', 'y', 'width', 'height',
                                            'filterRes', 'filterUnits', 'primitiveUnits', 'xlink:href')))
    font = TagProp('font', merge_attrs(CORE_ATTRIBUTES,
                                       PRESENTATION_ATTRIBUTES,
                                       ('class', 'style', 'externalResourcesRequired', 'horiz-origin-x',
                                        'horiz-origin-y', 'horiz-adv-z', 'vert-origin-x', 'vert-origin-y',
                                        'vert-adv-z')))
    font_face = TagProp('font-face',
                        merge_attrs(CORE_ATTRIBUTES,
                                    ('font-family', 'font-style', 'font-variant', 'font-weight', 'font-stretch',
                                     'font-size', 'unicode-range', 'units-per-em', 'panose-1', 'stemv', 'stemh',
                                     'slope', 'cap-height', 'x-height', 'accent-height', 'ascent', 'descent', 'widths',
                                     'bbox', 'ideographic', 'alphabetic', 'mathematical', 'hanging', 'v-ideographic',
                                     'v-alphabetic', 'v-mathematical', 'v-hanging', 'underline-position',
                                     'underline-thickness', 'strikethrough-position', 'strikethrough-thickness',
                                     'overline-position', 'overline-thickness')))
    font_face_format = TagProp('font-face-format', merge_attrs(CORE_ATTRIBUTES,
                                                               ('string',)))
    font_face_name = TagProp('font-face-name', merge_attrs(CORE_ATTRIBUTES,
                                                           ('name',)))
    font_face_src = TagProp('font-face-src', merge_attrs(CORE_ATTRIBUTES))
    font_face_uri = TagProp('font-face-uri', merge_attrs(CORE_ATTRIBUTES,
                                                         XLINK_ATTRIBUTES,
                                                         ('xlink:href',)))
    foreignObject = TagProp('foreignObject',
                            merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                        CORE_ATTRIBUTES,
                                        GRAPHICAL_EVENT_ATTRIBUTES,
                                        PRESENTATION_ATTRIBUTES,
                                        ('class', 'style', 'externalResourcesRequired', 'transform', 'x', 'y', 'width',
                                         'height')))
    g = TagProp('g', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                 CORE_ATTRIBUTES,
                                 GRAPHICAL_EVENT_ATTRIBUTES,
                                 PRESENTATION_ATTRIBUTES,
                                 ('class', 'style', 'externalResourcesRequired', 'transform')))
    glyph = TagProp('glyph', merge_attrs(CORE_ATTRIBUTES,
                                         PRESENTATION_ATTRIBUTES,
                                         ('class', 'style', 'd', 'horiz-adv-x', 'vert-origin-x', 'vert-origin-y',
                                          'vert-adv-y', 'unicode', 'glyph-name', 'orientation', 'arabic-form', 'lang')))
    glyphRef = TagProp('glyphRef', merge_attrs(CORE_ATTRIBUTES,
                                               PRESENTATION_ATTRIBUTES,
                                               XLINK_ATTRIBUTES,
                                               ('class', 'style', 'x', 'y', 'dx', 'dy', 'glyphRef', 'format',
                                                'xlink:href')))
    hkern = TagProp('hkern', merge_attrs(CORE_ATTRIBUTES,
                                         ('u1', 'g1', 'u2', 'g2', 'k')))
    image = TagProp('image', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                         CORE_ATTRIBUTES,
                                         GRAPHICAL_EVENT_ATTRIBUTES,
                                         XLINK_ATTRIBUTES,
                                         PRESENTATION_ATTRIBUTES,
                                         ('class', 'style', 'externalResourcesRequired', 'transform', 'x', 'y', 'width',
                                          'height', 'xlink:href', 'preserveAspectRatio')))
    line = TagProp('line', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                       CORE_ATTRIBUTES,
                                       GRAPHICAL_EVENT_ATTRIBUTES,
                                       ('class', 'style', 'externalResourcesRequired', 'transform', 'x1', 'x2', 'y1',
                                        'y2')))
    linearGradient = TagProp('linearGradient',
                             merge_attrs(CORE_ATTRIBUTES,
                                         PRESENTATION_ATTRIBUTES,
                                         XLINK_ATTRIBUTES,
                                         ('class', 'style', 'externalResourcesRequired', 'gradientUnits',
                                          'gradientTransform', 'x1', 'y1', 'x2', 'y2', 'spreadMethod', 'xlink:href')))
    marker = TagProp('marker', merge_attrs(CORE_ATTRIBUTES,
                                           PRESENTATION_ATTRIBUTES,
                                           ('class', 'style', 'externalResourcesRequired', 'viewBox',
                                            'preserveAspectRatio', 'transform', 'markerUnits', 'refX', 'refY',
                                            'markerWidth', 'markerHeight', 'orient')))
    mask = TagProp('mask', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                       CORE_ATTRIBUTES,
                                       PRESENTATION_ATTRIBUTES,
                                       ('class', 'style', 'externalResourcesRequired', 'maskUnits', 'maskContentUnits',
                                        'x', 'y', 'width', 'height')))
    metadata = TagProp('metadata', merge_attrs(CORE_ATTRIBUTES))
    missing_glyph = TagProp('missing-glyph', merge_attrs(CORE_ATTRIBUTES,
                                                         PRESENTATION_ATTRIBUTES,
                                                         ('class', 'style', 'd', 'horiz-adv-x', 'vert-origin-x',
                                                          'vert-origin-y', 'vert-adv-y')))
    mpath = TagProp('mpath', merge_attrs(CORE_ATTRIBUTES,
                                         XLINK_ATTRIBUTES,
                                         ('externalResourcesRequired',),
                                         ('xlink:href',)))
    path = TagProp('path', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                       CORE_ATTRIBUTES,
                                       GRAPHICAL_EVENT_ATTRIBUTES,
                                       PRESENTATION_ATTRIBUTES,
                                       ('class', 'style', 'externalResourcesRequired', 'transform', 'd', 'pathLength')))
    pattern = TagProp('pattern',
                      merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                  CORE_ATTRIBUTES,
                                  PRESENTATION_ATTRIBUTES,
                                  XLINK_ATTRIBUTES,
                                  ('class', 'style', 'externalResourcesRequired', 'viewBox', 'patternUnits',
                                   'patterContentUnits', 'patternTransform', 'x', 'y', 'width', 'height', 'xlink:href',
                                   'preserveAspectRatio')))
    polygon = TagProp('polygon', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                             CORE_ATTRIBUTES,
                                             GRAPHICAL_EVENT_ATTRIBUTES,
                                             ('class', 'style', 'externalResourcesRequired', 'transform', 'points')))
    polyline = TagProp('polyline',
                       merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                   CORE_ATTRIBUTES,
                                   GRAPHICAL_EVENT_ATTRIBUTES,
                                   ('class', 'style', 'externalResourcesRequired', 'transform', 'points')))
    radialGradient = TagProp('radialGradient',
                             merge_attrs(CORE_ATTRIBUTES,
                                         PRESENTATION_ATTRIBUTES,
                                         XLINK_ATTRIBUTES,
                                         ('class', 'style', 'externalResourcesRequired', 'gradientUnits',
                                          'gradientTransform', 'cx', 'cy', 'r', 'fx', 'fy', 'spreadMethod',
                                          'xlink:href')))
    rect = TagProp('rect', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                       CORE_ATTRIBUTES,
                                       GRAPHICAL_EVENT_ATTRIBUTES,
                                       ('class', 'style', 'externalResourcesRequired', 'transform', 'x', 'y', 'width',
                                        'height', 'rx', 'ry')))
    script = TagProp('script', merge_attrs(CORE_ATTRIBUTES,
                                           XLINK_ATTRIBUTES,
                                           ('externalResourcesRequired', 'type', 'xlink:href')))

    stop = TagProp('stop', merge_attrs(CORE_ATTRIBUTES,
                                       PRESENTATION_ATTRIBUTES,
                                       ('class', 'style', 'offset', 'stop-color', 'stop-opacity')))
    style = TagProp('style', merge_attrs(CORE_ATTRIBUTES,
                                         ('type', 'media', 'title')))
    svg = TagProp('svg', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                     CORE_ATTRIBUTES,
                                     DOCUMENT_EVENT_ATTRIBUTES,
                                     GRAPHICAL_EVENT_ATTRIBUTES,
                                     PRESENTATION_ATTRIBUTES,
                                     ('class', 'style', 'externalResourcesRequired', 'version', 'baseProfile', 'x', 'y',
                                      'width', 'height', 'preserveAspectRatio', 'contentScriptType', 'contentStyleType',
                                      'viewBox')))
    switch = TagProp('switch', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                           CORE_ATTRIBUTES,
                                           GRAPHICAL_EVENT_ATTRIBUTES,
                                           PRESENTATION_ATTRIBUTES,
                                           ('class', 'style', 'externalResourcesRequired', 'transform',
                                            'allowReorder')))
    symbol = TagProp('symbol', merge_attrs(CORE_ATTRIBUTES,
                                           GRAPHICAL_EVENT_ATTRIBUTES,
                                           PRESENTATION_ATTRIBUTES,
                                           ('class', 'style', 'externalResourcesRequired', 'preserveAspectRatio',
                                            'viewBox')))
    text = TagProp('text', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                       CORE_ATTRIBUTES,
                                       GRAPHICAL_EVENT_ATTRIBUTES,
                                       PRESENTATION_ATTRIBUTES,
                                       ('class', 'style', 'externalResourcesRequired', 'transform', 'x', 'y', 'dx',
                                        'dy', 'text-anchor', 'rotate', 'textLength', 'lengthAdjust')))
    textPath = TagProp('textPath', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                               CORE_ATTRIBUTES,
                                               GRAPHICAL_EVENT_ATTRIBUTES,
                                               PRESENTATION_ATTRIBUTES,
                                               XLINK_ATTRIBUTES,
                                               ('class', 'style', 'externalResourcesRequired', 'startOffset', 'method',
                                                'spacing', 'xlink:href')))
    title = TagProp('title', merge_attrs(CORE_ATTRIBUTES,
                                         ('class', 'style')))
    tref = TagProp('tref', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                       CORE_ATTRIBUTES,
                                       GRAPHICAL_EVENT_ATTRIBUTES,
                                       PRESENTATION_ATTRIBUTES,
                                       XLINK_ATTRIBUTES,
                                       ('class', 'style', 'externalResourcesRequired', 'xlink:href')))
    tspan = TagProp('tspan', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                         CORE_ATTRIBUTES,
                                         GRAPHICAL_EVENT_ATTRIBUTES,
                                         PRESENTATION_ATTRIBUTES,
                                         ('class', 'style', 'externalResourcesRequired', 'x', 'y', 'dx', 'dy', 'rotate',
                                          'textLength', 'lengthAdjust')))
    use = TagProp('use', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                     CORE_ATTRIBUTES,
                                     GRAPHICAL_EVENT_ATTRIBUTES,
                                     PRESENTATION_ATTRIBUTES,
                                     XLINK_ATTRIBUTES,
                                     ('class', 'style', 'externalResourcesRequired', 'transform', 'x', 'y', 'width',
                                      'height', 'xlink:href')))
    view = TagProp('view', merge_attrs(CORE_ATTRIBUTES,
                                       ('externalResourcesRequired', 'viewBox', 'preserveAspectRatio', 'zoomAndPan',
                                        'viewTarget')))
    vkern = TagProp('vkern', merge_attrs(CORE_ATTRIBUTES,
                                         ('u1', 'g1', 'u2', 'g2', 'k')))
    set = TagProp('set', merge_attrs(CONDITIONAL_PROCESSING_ATTRIBUTES,
                                     CORE_ATTRIBUTES,
                                     ANIMATION_EVENT_ATTRIBUTES,
                                     XLINK_ATTRIBUTES,
                                     ANIMATION_ATTRIBUTE_TARGET_ATTRIBUTES,
                                     ANIMATION_TIMING_ATTRIBUTES,
                                     ('externalResourcesRequired', 'to')))
