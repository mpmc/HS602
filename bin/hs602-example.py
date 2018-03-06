#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hs602-example.py
#
#  Copyright 2018 Mark Clarkstone <git@markclarkstone.co.uk>
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
from time import sleep
from hs602 import Controller

input('This is an example script to control the HS602 capture '
      'device..\nPress enter to continue, or ctrl+c to exit.')

print('Please wait..')
print(''.ljust(80, '-'))

# Create a new object..
#
# You can pass a number of options as keywords here..
# There is usually no need to set an addr (unless you have more than
# one device or none are discovered automatically).
#
device = Controller()
# device = Controller(addr='192.168.1.237')

# Device firmware version.
print("Device firmware version: {}".format(device.firmware_version_str))

# Device address.
print('Device address: {}'.format(device.addr))

# Connected clients.
print('Current client ID / Total clients: {}'.format(device.clients))

# Flash the LED while get/set-ting device information.
device.led = True

# Set input source - Uncomment (remove "# " to execute).
# use 1 to set analogue / anything else to set hdmi
# device.source = 0

# Get input source.
# Can be just device.source if desired.
print('Input source: {}'.format(device.source_str))

# Get input resolution.
print('Input resolution: {}'.format(device.resolution_str))

# Get HDCP value.
print('Input HDCP: {}'.format(device.hdcp))

# Get frames-per-second.
print('FPS: {}'.format(device.fps))

# Set frames-per-second -  Uncomment (remove "# " to execute).
# device.fps = 60

# Set picture settings - Uncomment (remove "# " to execute).
# 0 - 255, default 128.
# device.size = 1920, 1080
# device.brightness = 128
# device.contrast = 128
# device.hue = 128
# device.saturation = 128

# Get picture settings/colours.
print('Picture size: {}'.format(device.size_str))
print('Picture brightness: {}'.format(device.brightness))
print('Picture contrast: {}'.format(device.contrast))
print('Picture hue: {}'.format(device.hue))
print('Picture saturation: {}'.format(device.hue))

# Set rtmp - Max 255 in length, uncomment (remove "# " to execute).
# device.username = 'demo'
# device.password = 'demo'
# device.url = 'rtmp://stream.demo.com/demo'
# device.key = 'demo'

# Get rtmp details.
print('RTMP username: {}'.format(device.username))
print('RTMP password: {}'.format(device.password))
print('RTMP url: {}'.format(device.url))
print('RTMP key: {}'.format(device.key))

# Set stream average bitrate - 500 - 8000
# Uncomment (remove "# " to execute).
# device.bitrate = 10000

# Get streaming bitrate.
print('Stream (output) bitrate: {}kbps'.format(device.bitrate))

# Toggle streaming - you can set any value here, uncomment (remove
# "# " to execute).
# device.toggle = True

# Stop multi/uni-cast.
device.multicast = False
device.unicast = False

q = input('Start UDP stream? (type u for unicast or m for multicast '
          '(unstable!)) -> ')

if q.lower() == 'm':
    device.multicast = True
    print('Stream is available network wide on udp(or rtp)://@:8085\n\n'
          'Warning, This is pretty much untested, and be aware that '
          'multicast is bandwidth heavy and may swamp your '
          'network. If this happens, use unicast instead.')

elif q.lower() == 'u':
    device.unicast = True
    print('Stream is available locally on udp(or rtp)://@:8085).\n'
          'Press ctrl + c or close this window to stop streaming..')

else:
    print('Invalid input, not streaming.')

while device.socket:
    print('Streaming: {}'.format(device.toggle))
    print('Client number {}, Client Total: {}'.format(*device.clients))
    sleep(6)

# Done
print(''.ljust(80, '-'))
input('Goodbye, press any key to exit.')
