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

gettext.install('Hs602controller')


class Controller(object):
    """HS602 Controller."""

    def __init__(self, **kwargs):
        """The following are optional:

        :param addr: Host address, set to None for discovery.
        :param broadcast: Address to send/get discovery messages on.
        :param timeout: TCP/UDP socket timeout - default 10.
        :param tcp: TCP (command) port - default 8087.
        :param udp: UDP (broadcast) port - default 8086.
        :param ping: UDP ping message - default "HS602".
        :param pong: Expected UDP pong reply - default "YES".
        :param encoding: Message encoding - default UTF-8.
        :param cmd_len: Per-message command length - default 15.
        """
        # Defaults.
        self._addr = None
        self._broadcast = '<broadcast>'
        self._timeout = 10
        self._tcp = 8087
        self._udp = 8086
        self._ping = 'HS602'
        self._pong = 'YES'
        self._encoding = 'utf-8'
        self._cmd_len = 15

        self.__socket = None

        for key, value in kwargs.items():
            if hasattr(self, '{}'.format(key)):
                setattr(self, key, value)

    @staticmethod
    def _str(value):
        """Return true if string value is 1 - 255 in length."""
        value = '{}'.format(value)
        if len(value) in range(1, 256):
            return True
        raise ValueError(_('invalid value, requires a string of 1-255 '
                           'in length'))

    @staticmethod
    def _int(value):
        """Return true if int value is 0 - 255."""
        value = round(int(value))
        if value in range(0, 256):
            return True
        raise ValueError(_('invalid value, requires a number between '
                           '0 and 255'))

    @staticmethod
    def _port(value):
        """Return true if port int value is 0 - 65535."""
        value = round(int(value))
        if value in range(0, 65536):
            return True
        raise ValueError(_('invalid value, requires a port number '
                           'between 0 and 65535'))

    @staticmethod
    def _bytes(value, encoding='utf-8'):
        """Return the encoded bytes of value.

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
    def _echo(first, second):
        """Check if two variables are equal.

        :param first: First object.
        :param second: Second object.
        """
        return first == second

    @staticmethod
    def _pad(data, pad=None):
        """Pad data

        :param data: Data to pad, must be a list!
        :param pad: Size required - default 15.
        """
        pad = pad or 15
        data = bytes(data)
        return data.ljust(pad, b'\0')

    @staticmethod
    def _udp_msg(addr, port, msg, reply=True, timeout=10,
                 encoding='utf-8'):
        """Send a UDP message.

        :param addr: Host address.
        :param port: Port to send the message on.
        :param msg: Message to send (will be converted to bytes).
        :param reply: Optional, is reply needed? - default True.
        :param timeout: Optional socket timeout - default 10.
        :param encoding: Optional message encoding - default utf-8.
        """
        msg = __class__._bytes(msg, encoding)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(timeout)
            s.bind(('', port))

            replies = list()
            sent = 0
            while True:
                # Send message.
                if msg:
                    sent = s.sendto(msg, (addr, port))
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
                except (socket.error, socket.gaierror,
                        socket.herror, socket.timeout, OSError):
                    break
            return replies

    @staticmethod
    def _knock(addr, port):
        """Send a message to the device asking it to open the TCP
        command port.

        :param addr: Address of device.
        :param port: Port on which to send the message.
        """
        try:
            addr = socket.gethostbyname(addr)
            ip = reversed(str(addr).split('.'))
            msg = [67] + [int(octal) for octal in ip]
            __class__._udp_msg(addr, port, msg, False)
        except Exception as exc:
            raise Exception(_('failed to knock device')) from exc

    @staticmethod
    def _new_command_socket(addr, port, timeout):
        """Return a new command connection.

        :param addr: Address of host.
        :param port: Port of host.
        :param timeout: Socket timeout.
        """
        try:
            # Create the command connection.
            sock = socket.socket(family=socket.AF_INET,
                                 type=socket.SOCK_STREAM,
                                 proto=socket.IPPROTO_TCP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(timeout)
            sock.connect((addr, port))
            return sock
        except Exception as exc:
            raise Exception(_('can\'t connect')) from exc

    def addr(self, value=None):
        """Get or set host address.

        :param value: Optional host IPv4 address or hostname,

        Setting an address will close existing TCP connection.
        If no address is defined, discovery will be called & the first
        device to respond is used.
        """
        if value:
            self._str(value)
            self.close()
            self._addr = value
        return self._addr

    addr = property(_addr, _addr)

    def broadcast(self, value=None):
        """Get or set Broadcast address.

        :param value: Optional network broadcast address,
        default '<broadcast>'.
        """
        if value:
            self._str(value)
            self._broadcast = value
        return self._broadcast

    broadcast = property(broadcast, broadcast)

    def timeout(self, value=None):
        """Get or set UDP/TCP socket timeout.

        :param value: Optional socket timeout in seconds,
        0 - 255 - default 10.
        """
        if value:
            self._int(value)
            self._timeout = value
        return self._timeout

    timeout = property(timeout, timeout)

    def tcp(self, value=None):
        """Get or set TCP command port.

        :param value: Optional TCP command port - default 8087.
        """
        if value:
            self._port(value)
            self.close()
            self._tcp = value
        return self._tcp

    tcp = property(tcp, tcp)

    def udp(self, value=None):
        """Get or set UDP broadcast port.

        :param value: Optional UDP message port - default 8086.
        """
        if value:
            self._port(value)
            self._udp = value
        return self._udp

    udp = property(udp, udp)

    def ping(self, value=None):
        """Get or set device ping message.

        :param value: Optional message to broadcast - default 'HS602'.

        Return as bytes.
        """
        if value:
            self._str(value)
            self._ping = value
        return bytes(self._ping, self.encoding)

    ping = property(ping, ping)

    def pong(self, value=None):
        """Get or set device pong reply.

        :param value: Optional expected pong response from devices
        - default 'YES'.

        Return as bytes.
        """
        if value:
            self._str(value)
            self._pong = value
        return bytes(self._pong, self.encoding)

    pong = property(pong, pong)

    def encoding(self, value=None):
        """Get or set message encoding.

        :param value: Optional message encoding - default utf-8.
        """
        if value:
            self._str(value)
            self._encoding = value
        return self._encoding

    encoding = property(encoding, encoding)

    def cmd_len(self, value=None):
        """Get or set command length.

        :param value: Optional message command length, 0 - 255
        - default 15.
        """
        if value:
            self._int(value)
            self._cmd_len = value
        return self._cmd_len

    cmd_len = property(cmd_len, cmd_len)

    def close(self):
        """Kill active TCP connection."""
        try:
            # If this fails we can ignore it.
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
        except (socket.error, socket.gaierror, socket.herror,
                socket.timeout, OSError, AttributeError):
            pass
        self.__socket = None

    disconnect = close

    def discover(self):
        """Get a list of available devices."""
        try:
            ret = __class__._udp_msg(self.broadcast, self.udp,
                                     self.ping)
        except Exception as exc:
            raise Exception('discovery failure') from exc
        return [rep[0] for rep in ret if rep[2] == self.pong]

    def _cmd(self, msg, **kwargs):
        """Send command to device.

        :param msg: Message to send.
        :param knock: Do we ask the device to open the command
        connection?
        :param retry: Is this a retry?
        """
        msg = __class__._bytes(msg, self.encoding)
        data_len = self.cmd_len

        # We need an address!
        if not self.addr:
            self._addr = self.discover()[0]

        # Do we require a new socket?
        if not self.__socket or kwargs.get('retry', False):
            __class__._knock(self.addr, self.udp)
            # Connect!
            self.__socket = __class__._new_command_socket(self.addr,
                                                          self.tcp,
                                                          self.timeout)
        # Send!
        try:
            self.__socket.sendall(msg, 0)
            data = bytes()
            # Don't loop if data_len is zero.
            while True and int(data_len) > 0:
                # Receive reply.
                buf = self.__socket.recv(2048)
                if not buf:
                    self.__socket = None
                    break
                data += buf
                if len(data) >= data_len:
                    break
        except (socket.error, socket.gaierror, socket.herror,
                socket.timeout, OSError) as exc:
            # Is this a retry?
            if kwargs.get('retry', False):
                raise Exception(_('failed to send command')) from exc
            return self._cmd(msg, knock=False, retry=True)

        # Return the response
        return data[:data_len]

    def rtmp(self, param, value=None):
        """Get or set an RTMP value.

        :param param: Desired value: url, key, username or password.
        :param value: Optional value to set.
        """
        params = {
            'url': 16,
            'key': 17,
            'username': 20,
            'password': 21,
        }
        # Whats the param?
        param = params.get(str(param).lower())
        cmd = [param, 0]
        if not param:
            raise Exception(_('unknown rtmp param, must be one of: '
                              '{}'.format(list(params.keys()))))
        # Setting.
        if value:
            # Is what we're setting too long?
            __class__._str(value)
            for pos, char in enumerate(value):
                char_cmd = __class__._pad(cmd + [pos, ord(char)],
                                          self.cmd_len)
                if not __class__._echo(char_cmd, self._cmd(char_cmd)):
                    raise Exception(_('setting of rtmp value failed'))
            # Has the box accepted the setting?
            cmd = __class__._pad(cmd + [len(value), 0], self.cmd_len)
            return __class__._echo(cmd, self._cmd(cmd))

        # Getting.
        cmd = [param, 1]
        buf = ''
        for pos in range(0, 255):
            dec = int(self._cmd(cmd + [pos])[0] & 255)
            if not dec:
                break
            buf += chr(dec)
        return buf

    def url(self, value=None):
        """Get or set the RTMP URL.

        :param value: Optional RTMP URL to set.
        """
        if value:
            return self.rtmp('url', value)
        return self.rtmp('url')

    def key(self, value=None):
        """Get or set the RTMP key.

        :param value: Optional RTMP key to set.
        """
        if value:
            return self.rtmp('key', value)
        return self.rtmp('key')

    def username(self, value=None):
        """Get or set the RTMP username.

        :param value: Optional RTMP username to set.
        """
        if value:
            return self.rtmp('username', value)
        return self.rtmp('username')

    def password(self, value=None):
        """Get or set the RTMP password.

        :param value: Optional RTMP password to set.
        """
        if value:
            return self.rtmp('password', value)
        return self.rtmp('password')

    def colour(self, param, value=None):
        """Get or set a colour value.

        :param param: Desired value: brightness, contrast, hue or
        saturation.
        param value: Optional value to set, 0 - 255
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
        if value:
            __class__._int(value)
            cmd = __class__._pad([10, 0, param, value], self.cmd_len)
            return __class__._echo(cmd, self._cmd(cmd))

        # Get colour.
        return int(self._cmd([10, 1, param])[0] & 255)

    color = colour

    def brightness(self, value=None):
        """Get or set the colour brightness.

        :param value: Optional brightness level, 0 - 255 - default 128.
        """
        if value:
            return self.colour('brightness', value)
        return self.colour('brightness')

    def contrast(self, value=None):
        """Get or set the colour contrast.

        :param value: Optional contrast level, 0 - 255 - default 128.
        """
        if value:
            return self.colour('contrast', value)
        return self.colour('contrast')

    def hue(self, value=None):
        """Get or set the colour hue.

        :param value: Optional hue level, 0 - 255 - default 128.
        """
        if value:
            return self.colour('hue', value)
        return self.colour('hue')

    def saturation(self, value=None):
        """Get or set the colour saturation.

        :param value: Optional saturation level, 0 - 255 - default 128.
        """
        if value:
            return self.colour('saturation', value)
        return self.colour('saturation')

    def hdmi(self, value=None):
        """Get or set current input source.

        :param value: Optional, set to true to switch to HDMI or
        false to switch to analogue.

        If no value is passed this will return true if input is
        HDMI or false if analogue.
        """
        # Set input.
        if value in [True, False]:
            cmd = [1, 0, 3]
            if value is False:
                cmd = [1, 0, 2]
            cmd = __class__._pad(cmd, self.cmd_len)
            return __class__._echo(cmd, self._cmd(cmd))

        # Get value.
        ret = self._cmd(__class__._pad([1, 1], self.cmd_len))[0] & 255
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
        ret = self._cmd(__class__._pad([4, 1], self.cmd_len))[0] & 255
        if not resolutions.get(ret):
            raise Exception(_('unknown resolution value returned'))
        return resolutions.get(ret)

    def picture(self, value=None):
        """Get or set RTMP output picture size.

        :param value: Optional RTMP picture size. Set as two values,
        e.g, "1920, 1080".

        This is width by height.
        """
        w_range = range(0, 1921)
        h_range = range(0, 1081)

        if value:
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
            cmd = __class__._pad([3, 0] + width + height, self.cmd_len)
            return __class__._echo(cmd, self._cmd(cmd))

        # Get the picture width/height.
        ret = self._cmd(__class__._pad([3, 1], self.cmd_len))

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
        """Get or set the average RTMP bitrate.

        :param value: Optional average bitrate to set,
        500 - 15000 - default 15000.
        """
        # Set bitrate.
        if value:
            try:
                average = int(value)
                if average not in range(500, 15001):
                    raise ValueError
            except (TypeError, ValueError):
                average = 15000
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
            cmd = __class__._pad([2, 0] + average + low + high,
                                 self.cmd_len)
            return __class__._echo(cmd, self._cmd(cmd))

        # Get value.
        ret = self._cmd(__class__._pad([2, 1]))
        onezero = (ret[1] & 255) << 8 | (ret[0] & 255)
        twothree = (ret[2] & 255) << 16 | (ret[3] & 255) << 24
        return onezero | twothree

    def toggle(self, value=None):
        """Get or set RTMP stream state.

        :param value: Set to toggle RTMP streaming state.
        """
        # Toggle!
        if value:
            cmd = __class__._pad([15, 0], self.cmd_len)
            return __class__._echo(cmd, self._cmd(cmd))
        # Get current value.
        cmd = __class__._pad([15, 1], self.cmd_len)
        return bool(self._cmd(cmd)[0] & 255)

    def fps(self, value=None):
        """Get or set RTMP frames-per-second.

        :param value: Frames-per-second, 1 - 60.
        """
        if value:
            __class__._int(value)
            if value not in range(1, 61):
                value = 60
            value = round(int(value))
            fps = [
                value & 255,
                (value >> 8) & 255,
                (value >> 16) & 255,
                (value >> 24) & 255,
            ]
            return __class__._echo(__class__._pad([19, 0] + fps),
                                   self.cmd_len)
        # Get!
        return self._cmd(__class__._pad([19, 1], self.cmd_len))[0] & 255

    def led(self):
        """Flash the LED."""
        cmd = [55, 0, 1]
        cmd = __class__._pad(cmd, self.cmd_len)
        return __class__._echo(cmd, self._cmd(cmd))

    def hdcp(self):
        """Get HDCP status."""
        cmd = [5, 1]
        cmd = __class__._pad(cmd, self.cmd_len)
        return bool(self._cmd(cmd)[0] & 255)

    def mode(self, value=None):
        """Get or set RTP/UDP stream mode.

        :param value: Desired stream mode: unicast, broadcast, tcp
        hls or multicast

        Output is on port 8085.
        """
        modes = {
            0: 'unicast',
            1: 'broadcast',
            2: 'tcp',
            3: 'hls',  # HLS requires http server on box.
            4: 'multicast',
        }
        # Set.
        if value:
            __class__._str(value)

            mode = None
            for key, val in modes.items():
                if val == value:
                    mode = key
            if value.lower() not in modes.values() or mode is None:
                err = _('unknown stream mode, must be one '
                        'of: {}'.format(list(modes.values())))
                raise Exception(err)
            cmd = __class__._pad([8, 0, mode], self.cmd_len)
            return __class__._echo(cmd, self._cmd(cmd))

        # Get.
        mode = self._cmd(__class__._pad([8, 1], self.cmd_len))[0] & 255
        return modes.get(mode)

    def firmware(self):
        """Get firmware version."""
        ret = self._cmd(__class__._pad([56, 1], self.cmd_len))
        major, minor, revision = [
            ret[0] & 255,
            ret[1] & 255,
            ret[2] & 255
        ]
        return '{}.{}.{}'.format(major, minor, revision)

    def clients(self):
        """Get client id number and total connected clients. """
        ret = self._cmd(__class__._pad([50, 1], self.cmd_len))
        return ret[0] & 255, ret[1] & 255
