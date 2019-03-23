#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  example.py
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
import time
from hs602.controller import Controller


def main(*args):
    input('This is an example script to control the HS602 capture '
          'device..\nPress enter to continue, or ctrl+c to exit.')
    print('Please wait..')
    print(''.ljust(80, '-'))

    # Create a new object..
    #
    # You can pass a number of options as keywords here..
    # There is usually no need to set an addr (unless you have more than
    # one device or if none are discovered automatically).
    #
    devices = Controller.discover()

    try:
        device = Controller(devices[0])
    except Exception as exc:
        raise Exception('No device? Perhaps it/they\'ve '
                        'crashed?') from exc

    # Device firmware version.
    print("Device firmware version: {}".format(device.firmware()))

    # Device address.
    print('Device address: {}'.format(device.addr))

    # Connected clients.
    print('Current client ID / Total clients: {}'.format(device.clients()))

    # Flash the LED while get/set-ting device information.
    device.led()

    # Set HDMI (True) or Analogue (False)
    # device.hdmi(True)

    # Get input source.
    print('Input source: {}'.format('HDMI' if device.hdmi() else 'Analogue'))

    # Get input resolution.
    print('Input resolution: {}'.format(device.resolution()))

    # Get HDCP value.
    print('Input HDCP: {}'.format(device.hdcp()))

    # Get frames-per-second.
    print('FPS: {}'.format(device.fps()))

    # Set frames-per-second -  Uncomment (remove "# " to execute).
    # device.fps = 60

    # Set picture settings - Uncomment (remove "# " to execute).
    # 0 - 255, default 128.
    # device.picture("1920, 1080")
    # device.brightness(128)
    # device.contrast(128)
    # device.hue(128)
    # device.saturation(128)

    # Get picture settings/colours.
    print('Picture size: {}'.format(device.picture()))
    print('Picture brightness: {}'.format(device.brightness()))
    print('Picture contrast: {}'.format(device.contrast()))
    print('Picture hue: {}'.format(device.hue()))
    print('Picture saturation: {}'.format(device.saturation()))

    # Set RTMP - Max 255 in length, uncomment (remove "# " to execute).
    # device.username('demo')
    # device.password('demo')
    # device.url('rtmp://stream.demo.com/demo')
    # device.key('demo_password')
    # device.name('demo_channel_name')

    # Get rtmp details.
    print('RTMP username: {}'.format(device.username()))
    print('RTMP password: {}'.format(device.password()))
    print('RTMP url: {}'.format(device.url()))
    print('RTMP key: {}'.format(device.key()))
    print('RTMP channel name: {}'.format(device.name()))

    # Set stream average bitrate - 500 - 20000.
    device.bitrate(10000)

    # Get bitrate.
    print('Output bitrate: {}kbps'.format(device.bitrate()))

    # RTMP Streaming.
    # You can set any value here, uncomment (remove # to execute).
    # device.toggle(True)

    toggle = 'Yes ' if device.toggle() else 'No'
    print('Streaming to RTMP server: {}'.format(toggle))

    print(''.ljust(80, '-'))
    print("Start stream? Type:-\n\tu for unicast (default)\n\tb for "
          "multicast (on broadcast)\n\tt for TCP.\n\nWARNING: "
          "TCP mode will lock up the device if you do not have a TCP "
          "socket already listening, use something like "
          "'nc -l 8085 >> /tmp/hs602.ts'.")
    print(''.ljust(80, '-'))
    q = input('-> ').lower()

    if q == 'b':
        choice = 'broadcast'
        print('Stream will be available network wide on udp/rtp://@:8085\n'
              '\nWarning, This is pretty much untested, and be aware that '
              'multicast to broadcast is bandwidth heavy and may swamp '
              'your network. If this happens use unicast instead.')

    elif q == 't':
        choice = 'tcp'
        print('The stream will be pushed locally to port 8085 over tcp.')

    else:
        choice = 'unicast'
        print('Stream will be available locally on udp/rtp://@:8085.')

    device.mode(choice)
    while True:
        device.keepalive()
        time.sleep(5)
    # Done
    input('Goodbye! Press any key to exit.')


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
