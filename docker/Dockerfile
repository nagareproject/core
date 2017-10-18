# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

FROM ubuntu:16.04
LABEL description="Ubuntu 16.04 | Stackless Python 2.7.14"

WORKDIR /root

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gcc libbz2-dev libgdbm-dev \
       libc6-dev libreadline6-dev libsqlite3-dev libssl-dev make xz-utils zlib1g-dev libyaml-dev \
       libxml2-dev libxslt1-dev ssh git \
    && rm -rf /var/lib/apt/lists/* \
    && curl http://www.stackless.com/binaries/stackless-2714-export.tar.xz | tar -xJC /tmp \
    && cd /tmp/stackless-2714-export \
    && ./configure --prefix=/opt/stackless \
    && make && make install \
    && cd /root; rm -rf /tmp/stackless-2714-export \
    && /opt/stackless/bin/python -mensurepip \
    && /opt/stackless/bin/easy_install lxml

#ADD pip.conf .pip/
ADD pydistutils.cfg .pydistutils.cfg
#ADD pypirc .pypirc

