#!/usr/bin/env python

# --
# Copyright (c) 2008-2023 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import gzip
import sys


def build_assets():
    from dukpy.webassets import BabelJS
    from webassets import filter, script

    filter.register_filter(BabelJS)

    status = script.main(['-c', 'conf/assets.yaml', 'build', '--no-cache']) or 0
    if status == 0:
        with open('src/nagare/static/nagare.js', 'rb') as f, gzip.open('src/nagare/static/nagare.js.gz', 'wb') as g:
            g.write(f.read())

        return status


if __name__ == '__main__':
    sys.exit(build_assets())
