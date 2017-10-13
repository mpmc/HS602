#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  example.py
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
from hs602 import Controller


addr = Controller().discover()[0]
control = Controller(addr=addr)

# Print device streaming status.
print('Device is streaming: {}'.format(control.streaming_toggle()))

# Set URL & Key.
# Uncomment to set.
# control.rtmp_set('url', 'rtmp://foo.bar/foo')
# control.rtmp_set('key', 'myawesomepassword')

# Show the help.
help(Controller)
