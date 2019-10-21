# --
# Copyright (c) 2008-2019 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from webassets import Bundle


bundles = {
    'nagare_js': Bundle('*.js', filters=['rjsmin'], output='nagare.js')
}
