#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Controller.py
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

import socket
import gettext

gettext.install('Hs602_controller')


class Controller(object):
    """HS602 Controller."""
    def __init__(self, addr, **kwargs):
        """Initialise the controller.

        :param addr: Address of device.
        :param tcp: TCP (command) port - default 8087.
        :param udp: UDP (broadcast) port - default 8086.
        :param listen: Stream input port - default 8085.
        :param timeout: TCP/UDP socket timeout - default 10.
        """
        self.addr = __class__.str(addr)
        self.tcp = int(kwargs.get('tcp', 8087))
        self.udp = int(kwargs.get('udp', 8086))
        self.listen = int(kwargs.get('listen', 8085))
        self.timeout = int(kwargs.get('timeout', 10))

        self.socket = None
        self.cmd_len = 15

    @staticmethod
    def str(value):
        """Value is string of 1 - 255 in length.

        :param value: Value to check.
        """
        value = '{}'.format(value).strip()
        if len(value) in range(1, 256):
            return value
        raise ValueError(_('invalid value, requires a string of 1-255 '
                           'in length'))

    @staticmethod
    def int(value):
        """Value is int 0 - 255.

        :param value: Value to check.
        """
        value = round(int(value))
        if value in range(0, 256):
            return value
        raise ValueError(_('invalid value, requires a number between '
                           '0 and 255'))

    @staticmethod
    def port(value):
        """Value is int 0 - 65535.

        :param value: Value to check.
        """
        value = round(int(value))
        if value in range(0, 65536):
            return value
        raise ValueError(_('invalid value, requires a port number '
                           'between 0 and 65535'))

    @staticmethod
    def echo(first, second):
        """Test if two variables are equal.

        :param first: First object.
        :param second: Second object.
        """
        return first == second

    @staticmethod
    def pad(data, pad=15):
        """Pad data.

        :param data: Data to pad, must be a list!
        :param pad: Size required - default 15.
        """

        pad = __class__.int(pad)
        data = bytes(data)
        return data.ljust(pad, b'\0')

    @staticmethod
    def bytes(value, encoding='utf-8'):
        """Encode bytes.

        :param value: Data to encode.
        :param encoding: Data encoding.
        """
        try:
            value = bytes(value, encoding)
        except TypeError:
            pass
        value = bytes(value)
        return value

    @staticmethod
    def udp_msg(addr, port, msg, reply=True, timeout=5,
                encoding='utf-8'):
        """Send a UDP message.

        :param addr: Host address.
        :param port: Port to send the message on.
        :param msg: Message to send (will be converted to bytes).
        :param reply: Is reply needed?
        :param timeout: Socket timeout.
        :param encoding: Message encoding.
        """
        msg = __class__.bytes(msg, encoding)
        with __class__.sock(addr='', port=port, timeout=timeout,
                            udp=True) as sock:
            replies = list()
            sent = 0
            while True:
                # Send message.
                if msg:
                    sent = sock.sendto(msg, (addr, port))
                    if not sent > 0:
                        break
                    msg = msg[sent:]
                    continue

                # Receive message?
                if not reply:
                    return True
                try:
                    data, [addr, port] = sock.recvfrom(2048)
                    replies += [[addr, port, data]]
                except (socket.error, socket.gaierror,
                        socket.herror, socket.timeout, OSError):
                    break
            return replies

    @staticmethod
    def sock(addr, port, timeout, bind=False, udp=False):
        """Make a new connection.

        :param addr: Address of host.
        :param port: Port of host.
        :param timeout: Socket timeout.
        :param bind: Bind rather than connect.
        :param udp: Create a UDP socket - will bind automatically.
        """
        port = __class__.port(port)
        timeout = __class__.int(timeout)
        try:
            if udp:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET,
                                socket.SO_BROADCAST, 1)
                bind = True
            else:
                sock = socket.socket(family=socket.AF_INET,
                                     type=socket.SOCK_STREAM,
                                     proto=socket.IPPROTO_TCP)
                sock.setsockopt(socket.IPPROTO_TCP,
                                socket.TCP_NODELAY, 1)

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(timeout)
            if bind:
                sock.bind(('', port))
            else:
                sock.connect((__class__.str(addr), port))
            return sock
        except Exception as exc:
            raise Exception(_('can\'t connect or bind')) from exc

    @staticmethod
    def discover(**kwargs):
        """Get a list of available devices.

        :param ping: Ping message - default 'HS602'.
        :param pong: Pong message - default 'YES'.
        :param encoding: Message encoding - default 'utf-8'.
        :param broadcast: Address to send message - default
        '<broadcast>'.
        :param udp: Port on which to send message - default
        8086.
        """
        broadcast = str(kwargs.get('broadcast', '<broadcast>'))
        encoding = str(kwargs.get('encoding', 'utf-8'))
        udp = int(kwargs.get('udp', 8086))
        ping = __class__.bytes(kwargs.get('ping') or 'HS602', encoding)
        pong = __class__.bytes(kwargs.get('pong') or 'YES', encoding)

        try:
            ret = __class__.udp_msg(addr=broadcast, port=udp, msg=ping,
                                    encoding=encoding)
        except Exception as exc:
            raise Exception('discovery failure') from exc
        return [rep[0] for rep in ret if rep[2] == pong]

    def cmd(self, msg, **kwargs):
        """Send command to device.

        :param msg: Message to send.
        """
        msg = __class__.bytes(msg)
        data_len = self.cmd_len

        # We need an address!
        if not self.addr:
            raise ValueError(_('an address is required'))

        # Do we require a new socket?
        if not self.socket or kwargs.get('retry', False):
            try:
                # Knock.
                addr = socket.gethostbyname(self.addr)
                ip = reversed(addr.split('.'))
                knock = [67] + [int(octal) for octal in ip]
                __class__.udp_msg(addr=addr, port=self.udp, msg=knock,
                                  reply=False)
            except Exception as exc:
                raise Exception(_('failed to knock device')) from exc

            # Connect!
            self.socket = __class__.sock(addr=self.addr, port=self.tcp,
                                         timeout=self.timeout)
        try:
            # Send!
            self.socket.sendall(msg, 0)
            data = bytes()

            while True:
                # Receive reply.
                buf = self.socket.recv(1024)
                if not buf:
                    raise OSError(_('socket dead'))
                data += buf
                # Return the response.
                if len(data) >= data_len:
                    return data
        except Exception as exc:
            self.close()
            raise Exception(_('failed to send command')) from exc

    def close(self):
        """Close connection(s)."""
        try:
            # If this fails we can ignore it.
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except (socket.error, socket.gaierror, socket.herror,
                socket.timeout, OSError, AttributeError):
            pass
        self.socket = None

    stop = close

    def rtmp(self, param, value=None):
        """Set/Get RTMP value.

        :param param: Desired value: url, key, username or password.
        :param value: Value to set.
        """
        params = {
            'url': 16,
            'key': 17,
            'username': 20,
            'password': 21,
            'name': 23,
        }
        # Whats the param?
        param = params.get(str(param).lower())
        cmd = [param, 0]
        if not param:
            raise Exception(_('unknown rtmp param, must be one of: '
                              '{}'.format(list(params.keys()))))
        # Set.
        if value:
            # Is what we're setting too long?
            __class__.str(value)
            for pos, char in enumerate(value):
                char_cmd = __class__.pad(cmd + [pos, ord(char)],
                                         self.cmd_len)
                if not __class__.echo(char_cmd, self.cmd(char_cmd)):
                    raise Exception(_('setting rtmp value failed'))
            # Has the box accepted the setting?
            cmd = __class__.pad(cmd + [len(value), 0], self.cmd_len)
            return __class__.echo(cmd, self.cmd(cmd))

        # Get.
        cmd = [param, 1]
        buf = ''
        for pos in range(0, 255):
            dec = int(self.cmd(cmd + [pos])[0] & 255)
            if not dec:
                break
            buf += chr(dec)
        return buf

    def url(self, value=None):
        """Set/Get the RTMP URL.

        :param value: RTMP URL to set.
        """
        if value is not None:
            return self.rtmp('url', value)
        return self.rtmp('url')

    def key(self, value=None):
        """Set/Get the RTMP key.

        :param value: RTMP key to set.
        """
        if value is not None:
            return self.rtmp('key', value)
        return self.rtmp('key')

    def username(self, value=None):
        """Set/Get the RTMP username.

        :param value: RTMP username to set.
        """
        if value is not None:
            return self.rtmp('username', value)
        return self.rtmp('username')

    def password(self, value=None):
        """Set/Get the RTMP password.

        :param value: RTMP password to set.
        """
        if value is not None:
            return self.rtmp('password', value)
        return self.rtmp('password')

    def name(self, value=None):
        """Set/Get the RTMP channel name.

        :param value: RTMP name to set.
        """
        if value is not None:
            return self.rtmp('name', value)
        return self.rtmp('name')

    def colour(self, param, value=None):
        """Set/Get a colour value.

        :param param: Desired value: brightness, contrast, hue or
        saturation.
        param value: Value to set, 0 - 255
        """
        params = {
            'brightness': 0,
            'contrast': 1,
            'hue': 2,
            'saturation': 3,
        }
        param = params.get(str(param).lower(), None)
        if param is None:
            raise Exception(_('unknown colour param, must be one of: '
                              '{}'.format(list(params.keys()))))
        # Set colour.
        if value is not None:
            __class__.int(value)
            cmd = __class__.pad([10, 0, param, value], self.cmd_len)
            return __class__.echo(cmd, self.cmd(cmd))

        # Get colour.
        return int(self.cmd([10, 1, param])[0] & 255)

    def brightness(self, value=None):
        """Set/Get brightness.

        :param value: Brightness level, 0 - 255 - default 128.
        """
        if value is not None:
            return self.colour('brightness', value)
        return self.colour('brightness')

    def contrast(self, value=None):
        """Set/Get contrast.

        :param value: Contrast level, 0 - 255 - default 128.
        """
        if value is not None:
            return self.colour('contrast', value)
        return self.colour('contrast')

    def hue(self, value=None):
        """Set/Get hue.

        :param value: Hue level, 0 - 255 - default 128.
        """
        if value is not None:
            return self.colour('hue', value)
        return self.colour('hue')

    def saturation(self, value=None):
        """Set/Get saturation.

        :param value: Saturation level, 0 - 255 - default 128.
        """
        if value is not None:
            return self.colour('saturation', value)
        return self.colour('saturation')

    def hdmi(self, value=None):
        """Set/Get source input - HDMI or Analogue.

        :param value: True for HDMI, False for analogue.
        """
        if value is not None:
            cmd = [1, 0, 2]
            if value:
                cmd = [1, 0, 3]

            cmd = __class__.pad(cmd, self.cmd_len)
            self.cmd(cmd)

        # Get value.
        ret = self.cmd(__class__.pad([1, 1], self.cmd_len))[0] & 255
        if ret not in [2, 3]:
            raise Exception(_('invalid source number returned'))
        return True if ret is 3 else False

    def resolution(self):
        """Get current input resolution."""
        resolutions = {
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
        }
        ret = self.cmd(__class__.pad([4, 1], self.cmd_len))[0] & 255
        if not resolutions.get(ret):
            raise Exception(_('invalid resolution value returned'))
        return resolutions.get(ret)

    def picture(self, value=None):
        """Set/Get RTMP output picture size.

        :param value: RTMP picture size. Set as two values,
        e.g, "1920, 1080".

        This is width by height.
        """
        w_range = range(0, 1921)
        h_range = range(0, 1081)

        if value is not None:
            # Try a string split.
            try:
                value = value.split(',', 2)
            except AttributeError:
                pass

            try:
                width = int(value[0])
                height = int(value[1])
                if width not in w_range or height not in h_range:
                    raise ValueError
            except (TypeError, IndexError, ValueError) as exc:
                raise Exception(_('invalid width or height, max width '
                                  '1920, height 1080 - set as two  '
                                  'values e.g, 1920, 1080')) from exc
            # Set the value.
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
            cmd = __class__.pad([3, 0] + width + height, self.cmd_len)
            return __class__.echo(cmd, self.cmd(cmd))

        # Get the picture width/height.
        ret = self.cmd(__class__.pad([3, 1], self.cmd_len))

        height = (
            ret[0] & 255 +
            (ret[1] & 255) << 8 +
            (ret[2] & 255) << 16 +
            (ret[3] & 255) << 24
        )
        width = (
            ret[4] & 255 +
            (ret[5] & 255) << 8 +
            (ret[6] & 255) << 16 +
            (ret[7] & 255) << 24
        )

        if width not in w_range or height not in h_range:
            raise Exception(_('invalid width/height returned - '
                              'width:{} height:{}').format(width,
                                                           height))
        return width, height

    def bitrate(self, value=None):
        """Set/Get the average RTMP bitrate.

        :param value: Average bitrate to set, 500 - 20000.
        """
        if value is not None:
            try:
                average = int(value)
                if average not in range(500, 20001):
                    raise ValueError
            except (TypeError, ValueError):
                average = 20000
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

            cmd = __class__.pad([2, 0] + average + low + high,
                                self.cmd_len)
            return __class__.echo(cmd, self.cmd(cmd))

        # Get value.
        ret = self.cmd(__class__.pad([2, 1]))
        onezero = (ret[1] & 255) << 8 | (ret[0] & 255)
        twothree = (ret[2] & 255) << 16 | (ret[3] & 255) << 24
        return onezero | twothree

    def toggle(self, value=None):
        """Set/Get RTMP stream state.

        :param value: Set to toggle RTMP streaming state.
        """
        if value:
            cmd = __class__.pad([15, 0], self.cmd_len)
            return __class__.echo(cmd, self.cmd(cmd))
        # Get current value.
        cmd = __class__.pad([15, 1], self.cmd_len)
        return bool(self.cmd(cmd)[0] & 255)

    def fps(self, value=None):
        """Set/Get RTMP frames-per-second.

        :param value: Frames-per-second, 1 - 60.
        """
        if value is not None:
            __class__.int(value)
            if value not in range(1, 61):
                value = 60
            value = round(int(value))
            fps = [
                value & 255,
                (value >> 8) & 255,
                (value >> 16) & 255,
                (value >> 24) & 255,
            ]
            return __class__.echo(__class__.pad([19, 0] + fps),
                                  self.cmd_len)
        # Get!
        return self.cmd(__class__.pad([19, 1], self.cmd_len))[0] & 255

    def mode(self, value=None):
        """Set/Get RTP/UDP stream mode.

        :param value: Desired stream mode: unicast, broadcast, tcp.

        The device (by default) outputs on port 8085.
        """

        modes = ['unicast', 'broadcast', 'tcp']
        if value is not None:
            value = __class__.str(value).lower()
            try:
                mode = modes.index(value)
            except ValueError as exc:
                raise ValueError(_('unknown stream mode - supported '
                                   'modes: {}'.format(modes))) from exc
            cmd = __class__.pad([8, 0, mode], self.cmd_len)
            return __class__.echo(cmd, self.cmd(cmd))

        # Get.
        mode = self.cmd(__class__.pad([8, 1], self.cmd_len))[0] & 255
        return modes[mode]

    def base_port(self, value):
        """Set device base port.

        :param value: Port number.

        The device default is 8085!
        """
        port = __class__.port(value)
        cmd = bytes([14, 0]) + port.to_bytes(2, byteorder='little')
        cmd = __class__.pad(cmd, self.cmd_len)
        return __class__.echo(cmd, self.cmd(cmd))

    def led(self):
        """Flash the LED."""
        cmd = [55, 0, 1]
        cmd = __class__.pad(cmd, self.cmd_len)
        return __class__.echo(cmd, self.cmd(cmd))

    def hdcp(self):
        """Get HDCP status."""
        cmd = [5, 1]
        cmd = __class__.pad(cmd, self.cmd_len)
        return bool(self.cmd(cmd)[0] & 255)

    def firmware(self):
        """Get firmware version."""
        ret = self.cmd(__class__.pad([56, 1], self.cmd_len))
        major, minor, revision = [
            ret[0] & 255,
            ret[1] & 255,
            ret[2] & 255
        ]
        return '{}.{}.{}'.format(major, minor, revision)

    def clients(self):
        """Client ID and total connected clients. """
        ret = self.cmd(__class__.pad([50, 1], self.cmd_len))
        return ret[0] & 255, ret[1] & 255

    def keepalive(self, value=None):
        """Connection keepalive."""
        cmd = [0]
        cmd = __class__.pad(cmd, self.cmd_len)
        return __class__.echo(cmd, self.cmd(cmd))

    def settings(self, settings=None):
        """Set/Get settings.

        param settings: Dictionary of settings.

        Note, you must get settings before you can set them!
        """
        if settings is not None:
            for name, value in settings.items():
                method = getattr(self, '{}'.format(name))
                if value:
                    method(value)
                else:
                    method()

        return {
            'url': self.url(),
            'key': self.key(),
            'username': self.username(),
            'password': self.password(),
            'name': self.name(),
            'brightness': self.brightness(),
            'contrast': self.contrast(),
            'hue': self.hue(),
            'saturation': self.saturation(),
            'hdmi': self.hdmi(),
            'resolution': self.resolution(),
            'picture': self.picture(),
            'bitrate': self.bitrate(),
            'toggle': self.toggle(),
            'fps': self.fps(),
            'hdcp': self.hdcp(),
            'mode': self.mode(),
            'firmware': self.firmware(),
            'clients': self.clients(),
            'address': self.addr,
            'tcp': self.tcp,
            'udp': self.udp,
            'timeout': self.timeout,
        }
