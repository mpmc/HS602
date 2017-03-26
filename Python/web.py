#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  web.py
#
#  Copyright 2017 Mark Clarkstone <git@markclarkstone.co.uk>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
"""Import needed modules."""
import os
from bottle import route, run, template, static_file, response
from json import dumps
from HS602 import HS602
from time import time
"""JSON status."""
@route('/status')
def status():
    """Load and display details from device."""
    box = HS602()
    streaming = box.is_streaming()
    size = box.size()
    source = box.source(None, True)
    rtmp_url = box.stream('rtmpurl')
    bitrate = box.bitrate()
    ip = box.addr
    """Dump details."""
    content = {'ip': ip,
               'time': int(time()),
               'streaming': streaming,
               'bitrate': bitrate,
               'rtmp_url': rtmp_url,
               'source': source,
               'size': {'height': size[0], 'width': size[1]}}
    response.content_type = 'application/json'
    return dumps(content)
"""Run!"""
if __name__ == '__main__':
    run(host='localhost', port=8080)
else:
    app = application = bottle.default_app()
