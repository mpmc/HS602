#!/usr/bin/env python3
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
import HS602

t = HS602.HS602()
t.set_string_param("rtmpurl", "rtmp://a.rtmp.youtube.com/live2")
t.set_string_param("rtmpkey", "password")

if t.is_streaming():
    print("The device is streaming.")
else:
    print("The device is not streaming, will ask it to start.")
    t.toggle_streaming()
