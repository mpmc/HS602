#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  controller.py
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
import socket


class Controller(object):
    """HS602-T controller."""

    def __init__(self, **kwargs):
        """To override the defaults, pass the following as keyword args:

        :param addr: Address of device.
        :param udp: UDP broadcast port.
        :param tcp: TCP command port.
        :param timeout: Socket timeout. Don't set this to 0 or None.
        :param ping: Message to trigger pong reply.
        :param pong: Expected pong response.
        :param encoding: Message encoding.
        :param cmd_len: Command length. Don't set this to 0 or None.


        If addr isn't set and a method is used, discover() will be
        called automatically, the first device found is used.

        And I'll repeat this again ;), do not set timeout or
        cmd_len to zero (or None).

        All sockets are blocking!
        """
        # Required class attributes and their defaults.
        self.addr = None
        self.socket = None
        self.defaults = {
            'addr': '<broadcast>',
            'udp': 8086,
            'tcp': 8087,
            'timeout': 10,
            'ping': 'HS602',
            'pong': 'YES',
            'encoding': 'utf-8',
            'cmd_len': 15,
        }
        for key, value in self.defaults.items():
            setattr(self, key, kwargs.get(key, value))

        # For colour/color.
        self.color = self.colour
        self.color_set = self.colour_set

    def udp_msg(self, msg, reply=True):
        """Send UDP message.

        :param msg: Message (in bytes) to send.
        :param reply: Do we want to wait for a reply?

        Return a list of replies, an empty list is returned if
        nothing is received.
        """
        msg = bytes(msg)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(self.timeout)
            s.bind(('', self.udp))

            replies = []
            while True:
                # Send message.
                if msg:
                    sent = s.sendto(msg, (self.addr, self.udp))
                    if not sent > 0:
                        break
                    msg = msg[sent:]
                    continue

                # Receive message?
                if not reply:
                    return True
                try:
                    data, [addr, port] = s.recvfrom(2048)
                    replies += [[addr, port, data]]
                except socket.timeout:
                    break
            return replies

    def discover(self):
        """Sends ping to self.addr to see who pongs back.

        Return a list of addresses that respond correctly.
        """
        # Ping/Pong messages should be in bytes with an encoding.
        # Make a (silent) attempt to convert, if that fails use as is.
        try:
            self.ping, self.pong = [self.ping.encode(self.encoding),
                                    self.pong.encode(self.encoding)]
        except UnicodeError:
            pass
        replies = self.udp_msg(self.ping)
        if replies:
            return [rep[0] for rep in replies if rep[2] == self.pong]

    def cmd(self, msg, reply=True):
        """Send command to device.

        :param msg: Message (in bytes) to send.
        :param reply: Do we want to wait for a reply?

        Return the reply. True if
        message was sent without error (when no reply needed).
        """
        msg = bytes(msg)
        # Do we need to discover a device first?
        if self.addr.lower() == self.defaults['addr'].lower():
            self.addr = self.discover()[0]
        # If there is no connection, so tell the device to
        # get ready to accept one.
        #
        # This is just the the "C" char and the IP address of the
        # box in reverse.
        if not self.socket:
            ip = reversed(self.addr.split('.'))
            cmd = [67] + [int(octal) for octal in ip]
            self.udp_msg(cmd, False)
            addr = (self.addr, self.tcp)
            self.socket = socket.create_connection(addr, self.timeout)

        # Send it & get replies (if needed).
        self.socket.sendall(msg)
        if not reply:
            return True
        data = bytes()
        while True:
            buf = self.socket.recv(self.cmd_len)
            if not buf:
                self.socket = None
                break
            data += buf
            if len(data) == self.cmd_len:
                break
        return data

    def pad(self, data, pad_len=None):
        """Return data appended with zero bytes to the size of pad_len.

        :param data: data to pad, can be anything that can be
        converted to bytes.
        :param pad_len: Size required, don't set to use self.cmd_len.
        """
        pad_len = pad_len or self.cmd_len
        data = bytes(data)
        data = data.ljust(pad_len, b'\0')
        return data

    def echo(self, first, second):
        """Return True if first and second match.

        :param first: First object.
        :param second: Second object.
        """
        if first == second:
            return True

    def keepalive(self):
        """Send a keep-alive message."""
        cmd = self.pad([0])
        return self.cmd(cmd, False)

    def streaming_toggle(self):
        """Return current streaming toggle status (True or False)."""
        cmd = self.pad([15, 1])
        return bool(self.cmd(cmd)[0] & 255)

    def streaming_toggle_set(self):
        """Toggle start/stop streaming. Returns True if successful or
           False on error.
        """
        cmd = self.pad([15, 0])
        return self.echo(cmd, self.cmd(cmd))

    def opts(self, opt):
        """Return option parameter dict.

        :param opt: Options to return.

        To return the full dict, set opt to None.
        """
        opt_dict = {
            'rtmp': {
                'url': 16,
                'key': 17,
                'username': 20,
                'password': 21,
            },
            'colour': {
                'brightness': 0,
                'contrast': 1,
                'hue': 2,
                'saturation': 3,
            },
            'source': {
                2: 'ypbpr',
                3: 'hdmi',
            },
            'resolution': {
                0: '1920x1080 60Hz',
                1: '1280x720 60Hz',
                2: '720x480 60Hz',
                3: '720x480 60Hz',
                4: '720x480 60Hz',
                5: '1920x1080 50Hz',
                6: '1280x720 50Hz',
                7: '720x576 50Hz',
                8: '720x576 50Hz',
                9: '720x576 50Hz',
                10: '1920x1080 60Hz',
                11: '1280x720 60Hz',
                12: '720x480 60Hz',
                13: '720x480 60Hz',
                14: '1920x1080 50Hz',
                15: '1280x720 50Hz',
                16: '720x576 50Hz',
                17: '720x576 50Hz',
                18: '720x480 60Hz',
                19: '720x576 50Hz',
                20: '1920x1080 25Hz',
                21: '1920x1080 30Hz',
                22: '0x0 60Hz',
                23: '640x480 60Hz',
                24: '1920x1080 30Hz',
                25: '1920x1080 25Hz',
                26: '1920x1080 50Hz',
                27: '1920x1080 60Hz',
                28: '1920x1080 24Hz',
                29: '1920x1080 60Hz',
                30: '1920x1080 50Hz',
                31: '1920x1080 24Hz',
                32: '800x600 60Hz',
                33: '1024x768 60Hz',
                34: '1152x864 60Hz',
                35: '1280x768 60Hz',
                36: '1280x800 60Hz',
                37: '1280x960 60Hz',
                38: '1280x1024 60Hz',
                39: '1360x768 60Hz',
                40: '1440x900 60Hz',
                41: '1600x900 60Hz',
                42: '1680x1050 60Hz',
            },
        }

        # Return the full list?
        if not opt:
            return opt_dict

        opt = opt.lower()

        # Color/Colour
        if opt == 'color':
            opt = 'colour'

        return opt_dict[opt]

    def rtmp(self, param):
        """Get RTMP value.

        :param param: See opts('rtmp').

        Return the RTMP value currently used by the device (str).
        """
        opt = self.opts('rtmp')
        cmd = [opt[param.lower()], 1]
        index = 0
        buf = ''
        while index < 254:
            result = self.pad(cmd + [index])
            dec = int(self.cmd(result)[0] & 255)
            if dec == 0:
                break
            buf += chr(dec)
            index += 1
        return buf

    def rtmp_set(self, param, value):
        """Set RTMP values.

        :param param: See opts('rtmp').
        :param value: Value to set, max length 255.
        """
        opt = self.opts('rtmp')
        cmd = [opt[param.lower()], 0]
        # Too long?
        if len(value) > 255 or len(value) == 0:
            raise ValueError

        # Send each char.
        for index, char in enumerate(value):
            char_cmd = self.pad(cmd + [index, ord(char)])
            # Ack?
            if not self.echo(char_cmd, self.cmd(char_cmd)):
                return

        # Finally, send the total length.
        cmd = self.pad(cmd + [len(value), 0])
        return self.echo(cmd, self.cmd(cmd))

    def colour(self, param):
        """Get colour parameter value.

        :param param: See opts('colour').

        Return "param" value as int (0-255).
        """
        opt = self.opts('colour')
        # What colour param?
        cmd = self.pad([10, 1, opt[param.lower()]])
        result = int(self.cmd(cmd)[0] & 255)
        return result

    def colour_set(self, param, value):
        """Set colour parameter value.

        :param param: See opts('colour')
        :param value: Value to set, 0 - 255.
        """
        opt = self.opts('colour')
        # What colour param?
        cmd = self.pad([10, 0, opt[param.lower()], value & 255])
        return self.echo(cmd, self.cmd(cmd))

    def source(self, text=False):
        """Returns current input source.

        :param text: Return text value?

        Returns int (2 or 3) or text representation if text is True.
        """
        cmd = self.pad([1, 1])
        inputs = self.opts('source')
        cur = self.cmd(cmd)[0] & 255
        if text:
            return inputs[cur]
        return cur

    def source_set(self, source):
        """Set source.

        :param source: See opts('source').
        """
        cmd = self.pad([1, 0, source & 255])
        return bool(self.cmd(cmd)[0] & 255)

    def resolution(self, text=False):
        """Returns the currently-reported input resolution.

        :param text: Return text value?

        Returns int or text representation if text is True.
        """
        modes = self.opts('resolution')
        cmd = self.pad([4, 1])
        result = self.cmd(cmd)[0] & 255
        resolution = modes[result]

        if text:
            return resolution
        return result

    def size(self):
        """Return current (output) picture size as a height, width
        tuple.
        """
        cmd = self.pad([3, 1])
        result = self.cmd(cmd)
        height = (
            result[0] & 255 +
            (result[1] & 255) << 8 +
            (result[2] & 255) << 16 +
            (result[3] & 255) << 24
        )
        width = (
            result[4] & 255 +
            (result[5] & 255) << 8 +
            (result[6] & 255) << 16 +
            (result[7] & 255) << 24
        )
        return height, width

    def size_set(self, height, width):
        """Set picture size.

        :param height: Picture height.
        :param width: Picture width.
        """
        height = [
            height & 255,
            (height >> 8) & 255,
            (height >> 16) & 255,
            (height >> 24) & 255,
        ]
        width = [
            width & 255,
            (width >> 8) & 255,
            (width >> 16) & 255,
            (width >> 24) & 255,
        ]
        cmd = self.pad([3, 0] + height + width)
        return self.echo(cmd, self.cmd(cmd))

    def bitrate(self):
        """Return current streaming bitrate (int)."""
        cmd = self.pad([2, 1])
        result = self.cmd(cmd)
        # This is split like this to make it less ugly (still is).
        onezero = (result[1] & 255) << 8 | (result[0] & 255)
        twothree = (result[2] & 255) << 16 | (result[3] & 255) << 24
        return onezero | twothree

    def bitrate_set(self, average):
        """Set the bitrate.

        :param average: The average bitrate to use.
        """
        average = int(average)
        average = average if average >= 500 else 500
        average = average if average <= 8000 else 8000
        low = int(average * 7 / 10)
        high = int(average * 13 / 10)
        average = [
            average & 255,
            (average >> 8) & 255,
            (average >> 16) & 255,
            (average >> 24) & 255,
        ]
        low = [
            low & 255,
            (low >> 8) & 255,
            (low >> 16) & 255,
            (low >> 24) & 255,
        ]
        high = [
            high & 255,
            (high >> 8) & 255,
            (high >> 16) & 255,
            (high >> 24) & 255,
        ]
        cmd = self.pad([2, 0] + average + low + high)
        return self.echo(cmd, self.cmd(cmd))
