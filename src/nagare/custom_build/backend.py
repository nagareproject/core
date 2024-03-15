# --
# Copyright (c) 2008-2024 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import os
import sys

from setuptools.build_meta import build_sdist as _build_sdist
from setuptools.build_meta import build_wheel as _build_wheel
from setuptools.build_meta import build_editable as _build_editable
from setuptools.build_meta import prepare_metadata_for_build_wheel  # noqa: F401

sys.path.insert(0, os.path.dirname(__file__))
from build_assets import build_assets  # noqa: E402


def build_sdist(*args):
    build_assets()
    return _build_sdist(*args)


def build_wheel(*args):
    build_assets()
    return _build_wheel(*args)


def build_editable(*args, **kw):
    build_assets()
    return _build_editable(*args, **kw)
