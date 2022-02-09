#!/usr/bin/env python

# --
# Copyright (c) 2008-2022 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import sys
import gzip


def build_assets():
    from webassets import filter, script
    from dukpy.webassets import BabelJS

    filter.register_filter(BabelJS)

    status = script.main(['-c', 'conf/assets.yaml', 'build', '--no-cache']) or 0
    if status == 0:
        with open('nagare/static/js/nagare.js', 'rb') as f, gzip.open('nagare/static/js/nagare.js.gz', 'wb') as g:
            g.write(f.read())

        return status


if __name__ == '__main__':
    sys.exit(build_assets())
