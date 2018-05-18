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
import queue
import gettext

gettext.install('Hs602controller')


class Controller(object):
    """HS602 Controller."""
    def __init__(self, addr, **kwargs):
        """Initialise the controller.

        :param addr: Address of device.
        :param tcp: Optional TCP (command) port - default 8087.
        :param udp: Optional UDP (broadcast) port - default 8086.
        :param timeout: Optional TCP/UDP socket timeout - default 10.
        """
        self.__addr = __class__.str(addr)
        self.__tcp = int(kwargs.get('tcp', 8087))
        self.__udp = int(kwargs.get('udp', 8086))
        self.__timeout = int(kwargs.get('timeout', 10))

        self.__socket = None
        self.__cmd_len = 15
        self.__cache = {}
        self.__queue = queue.Queue()

        if not self.__addr:
            return

        self._cache_()

    @property
    def addr(self):
        """Current device address."""
        return self.__addr

    @property
    def tcp(self):
        """TCP (command) port."""
        return self.__tcp

    @property
    def udp(self):
        """UDP port."""
        return self.__udp

    @property
    def timeout(self):
        """Socket timeout."""
        return self.__timeout

    @timeout.setter
    def timeout(self, value):
        self.__timeout = __class__.int(value)

    @staticmethod
    def str(value):
        """Return true if string value is 1 - 255 in length.

        :param value: value to check.
        """
        value = '{}'.format(value).strip()
        if len(value) in range(1, 256):
            return value
        raise ValueError(_('invalid value, requires a string of 1-255 '
                           'in length'))

    @staticmethod
    def int(value):
        """Return true if int value is 0 - 255.

        :param value: value to check.
        """
        value = round(int(value))
        if value in range(0, 256):
            return value
        raise ValueError(_('invalid value, requires a number between '
                           '0 and 255'))

    @staticmethod
    def port(value):
        """Return true if port int value is 0 - 65535.

        :param value: value to check.
        """
        value = round(int(value))
        if value in range(0, 65536):
            return value
        raise ValueError(_('invalid value, requires a port number '
                           'between 0 and 65535'))

    @staticmethod
    def echo(first, second):
        """Check if two variables are equal.

        :param first: First object.
        :param second: Second object.
        """
        return first == second

    @staticmethod
    def pad(data, pad=None):
        """Pad data

        :param data: Data to pad, must be a list!
        :param pad: Size required - default 15.
        """

        pad = pad or 15
        data = bytes(data)
        return data.ljust(pad, b'\0')

    @staticmethod
    def bytes(value, encoding='utf-8'):
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
    def udp_msg(addr, port, msg, reply=True, timeout=5,
                encoding='utf-8'):
        """Send a UDP message.

        :param addr: Host address.
        :param port: Port to send the message on.
        :param msg: Message to send (will be converted to bytes).
        :param reply: Optional, is reply needed? - default True.
        :param timeout: Optional socket timeout - default 5.
        :param encoding: Optional message encoding - default utf-8.
        """
        msg = __class__.bytes(msg, encoding)
        with __class__.new_socket(addr='', port=port, timeout=timeout,
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
    def new_socket(addr, port, timeout, bind=False, udp=False):
        """Make a new connection.

        :param addr: Address of host.
        :param port: Port of host.
        :param timeout: Socket timeout.
        :param bind: Bind rather than connect.
        :param udp: Create a UDP socket, will bind automatically.
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
    def udp_stream(port=8085):
        """Receive raw stream data from UDP.
        :param port: Port to receive the stream from.
        """
        def _sock():
            sock = __class__.new_socket(addr=None, timeout=5, bind=True,
                                        port=__class__.port(port),
                                        udp=True)
            return sock

        sock = _sock()
        while True:
            try:
                data = sock.recvfrom(65535)
                if data:
                    yield data[0]
            except (socket.error, socket.gaierror, socket.herror,
                    socket.timeout, BlockingIOError, OSError):
                continue

    @staticmethod
    def discover(**kwargs):
        """Get a list of available devices.

        :param ping: Ping message - default 'HS602'.
        :param pong: Pong message - default 'YES'.
        :param encoding: Message encoding - default 'utf-8'.
        :param broadcast: Optional address to send message - default
        '<broadcast>'.
        :param udp: Optional port on which to send message - default
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

    def __backlog_(self, key, value=None):
        """Queue up setting of properties.

        :param key: Name of the property.
        :param value: Value property value.
        """
        # Queue!
        self.__queue.put((key, value), block=False)

    def commit(self, blocking=False, timeout=5):
        """Refresh and save settings, update cache.

        :param blocking: Use a blocking queue - default False.
        :param timeout: Maximum time to block.

        If blocking make sure to thread this!
        """
        while True:
            try:
                key, value = self.__queue.get(block=blocking,
                                              timeout=timeout)
                method = getattr(self, '_{}_'.format(key))
                if value:
                    method(value)
                    self.__cache.update({key: value})
                else:
                    method()
            except queue.Empty:
                # Update the cache.
                self.__backlog_('cache')
                if not blocking:
                    break

    def _cmd(self, msg, **kwargs):
        """Send command to device.

        :param msg: Message to send.
        :param retry: Is this a retry?
        """
        msg = __class__.bytes(msg)
        data_len = self.__cmd_len

        # We need an address!
        if not self.addr:
            raise ValueError(_('an address is required'))

        # Do we require a new socket?
        if not self.__socket or kwargs.get('retry', False):
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
            self.__socket = __class__.new_socket(addr=self.addr,
                                                 port=self.tcp,
                                                 timeout=self.timeout)
        # Send!
        try:
            self.__socket.sendall(msg, 0)
            data = bytes()
            # Don't loop if data_len is zero.
            while True and int(data_len) > 0:
                # Receive reply.
                buf = self.__socket.recv(1024)
                if not buf:
                    self._close()
                    break
                data += buf
                if len(data) >= data_len:
                    break
        except (socket.error, socket.gaierror, socket.herror,
                socket.timeout, OSError) as exc:
            # Is this a retry?
            if kwargs.get('retry', False):
                raise Exception(_('failed to send command')) from exc
            self._close()
            return self._cmd(msg, retry=True)

        # Return the response.
        return data

    def _close(self):
        """Kill active TCP connection & clean-up."""
        try:
            # If this fails we can ignore it.
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
        except (socket.error, socket.gaierror, socket.herror,
                socket.timeout, OSError, AttributeError):
            pass
        # Reset!
        self.__queue = queue.Queue()

    def _rtmp_(self, param, value=None):
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
            __class__.str(value)
            for pos, char in enumerate(value):
                char_cmd = __class__.pad(cmd + [pos, ord(char)],
                                         self.__cmd_len)
                if not __class__.echo(char_cmd, self._cmd(char_cmd)):
                    raise Exception(_('setting rtmp value failed'))
            # Has the box accepted the setting?
            cmd = __class__.pad(cmd + [len(value), 0], self.__cmd_len)
            return __class__.echo(cmd, self._cmd(cmd))

        # Getting.
        cmd = [param, 1]
        buf = ''
        for pos in range(0, 255):
            dec = int(self._cmd(cmd + [pos])[0] & 255)
            if not dec:
                break
            buf += chr(dec)
        return buf

    def _url_(self, value=None):
        """Get or set the RTMP URL.

        :param value: Optional RTMP URL to set.
        """
        if value:
            return self._rtmp_('url', value)
        return self._rtmp_('url')

    @property
    def url(self):
        """RTMP URL."""
        return self.__cache['url']

    @url.setter
    def url(self, value):
        self.__backlog_('url', value)

    def _key_(self, value=None):
        """Get or set the RTMP key.

        :param value: Optional RTMP key to set.
        """
        if value:
            return self._rtmp_('key', value)
        return self._rtmp_('key')

    @property
    def key(self):
        """RTMP key."""
        return self.__cache['key']

    @key.setter
    def key(self, value):
        self.__backlog_('key', value)

    def _username_(self, value=None):
        """Get or set the RTMP username.

        :param value: Optional RTMP username to set.
        """
        if value:
            return self._rtmp_('username', value)
        return self._rtmp_('username')

    @property
    def username(self):
        """RTMP username."""
        return self.__cache['username']

    @username.setter
    def username(self, value):
        self.__backlog_('username', value)

    def _password_(self, value=None):
        """Get or set the RTMP password.

        :param value: Optional RTMP password to set.
        """
        if value:
            return self._rtmp_('password', value)
        return self._rtmp_('password')

    @property
    def password(self):
        """RTMP password."""
        return self.__cache['password']

    @password.setter
    def password(self, value):
        self.__backlog_('password', value)

    def _colour_(self, param, value=None):
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
            __class__.int(value)
            cmd = __class__.pad([10, 0, param, value], self.__cmd_len)
            return __class__.echo(cmd, self._cmd(cmd))

        # Get colour.
        return int(self._cmd([10, 1, param])[0] & 255)

    _color_ = _colour_

    def _brightness_(self, value=None):
        """Get or set the colour brightness.

        :param value: Optional brightness level, 0 - 255 - default 128.
        """
        if value:
            return self._colour_('brightness', value)
        return self._colour_('brightness')

    @property
    def brightness(self):
        """Output brightness."""
        return self.__cache['brightness']

    @brightness.setter
    def brightness(self, value):
        self.__backlog_('brightness', value)

    def _contrast_(self, value=None):
        """Get or set the colour contrast.

        :param value: Optional contrast level, 0 - 255 - default 128.
        """
        if value:
            return self._colour_('contrast', value)
        return self._colour_('contrast')

    @property
    def contrast(self):
        """Output contrast."""
        return self.__cache['contrast']

    @contrast.setter
    def contrast(self, value):
        self.__backlog_('contrast', value)

    def _hue_(self, value=None):
        """Get or set the colour hue.

        :param value: Optional hue level, 0 - 255 - default 128.
        """
        if value:
            return self._colour_('hue', value)
        return self._colour_('hue')

    @property
    def hue(self):
        """Output hue."""
        return self.__cache['hue']

    @hue.setter
    def hue(self, value):
        self.__backlog_('hue', value)

    def _saturation_(self, value=None):
        """Get or set the colour saturation.

        :param value: Optional saturation level, 0 - 255 - default 128.
        """
        if value:
            return self._colour_('saturation', value)
        return self._colour_('saturation')

    @property
    def saturation(self):
        """Output saturation."""
        return self.__cache['saturation']

    @saturation.setter
    def saturation(self, value):
        self.__backlog_('saturation', value)

    def _hdmi_(self, value=None):
        """Get or set current input source.

        :param value: Optional, set to true to switch to HDMI or
        false to switch to analogue.

        If no value is passed this will return true if input is
        HDMI or false if analogue.
        """
        if value is not None:
            cmd = [1, 0, 2]
            if value:
                cmd = [1, 0, 3]
            cmd = __class__.pad(cmd, self.__cmd_len)
            return __class__.echo(cmd, self._cmd(cmd))

        # Get value.
        ret = self._cmd(__class__.pad([1, 1], self.__cmd_len))[0] & 255
        if ret not in [2, 3]:
            raise Exception(_('invalid source number returned'))
        return True if ret is 3 else False

    @property
    def hdmi(self):
        """HDMI or analogue input."""
        return self.__cache['hdmi']

    @hdmi.setter
    def hdmi(self, value):
        self.__backlog_('hdmi', value)

    def _resolution_(self):
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
        ret = self._cmd(__class__.pad([4, 1], self.__cmd_len))[0] & 255
        if not resolutions.get(ret):
            raise Exception(_('invalid resolution value returned'))
        return resolutions.get(ret)

    @property
    def resolution(self):
        """Input resolution."""
        return self.__cache['resolution']

    def _picture_(self, value=None):
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
            cmd = __class__.pad([3, 0] + width + height, self.__cmd_len)
            return __class__.echo(cmd, self._cmd(cmd))

        # Get the picture width/height.
        ret = self._cmd(__class__.pad([3, 1], self.__cmd_len))

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

    @property
    def picture(self):
        """Output picture size."""
        return self.__cache['picture']

    @picture.setter
    def picture(self, value):
        self.__backlog_('picture', value)

    def _bitrate_(self, value=None):
        """Get or set the average RTMP bitrate.

        :param value: Optional average bitrate to set,
        500 - 15000 - default 15000.
        """
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
            cmd = __class__.pad([2, 0] + average + low + high,
                                self.__cmd_len)
            return __class__.echo(cmd, self._cmd(cmd))

        # Get value.
        ret = self._cmd(__class__.pad([2, 1]))
        onezero = (ret[1] & 255) << 8 | (ret[0] & 255)
        twothree = (ret[2] & 255) << 16 | (ret[3] & 255) << 24
        return onezero | twothree

    @property
    def bitrate(self):
        """Output bitrate."""
        return self.__cache['bitrate']

    @bitrate.setter
    def bitrate(self, value):
        self.__backlog_('bitrate', value)

    def _toggle_(self, value=None):
        """Get or set RTMP stream state.

        :param value: Set to toggle RTMP streaming state.
        """
        if value:
            cmd = __class__.pad([15, 0], self.__cmd_len)
            return __class__.echo(cmd, self._cmd(cmd))
        # Get current value.
        cmd = __class__.pad([15, 1], self.__cmd_len)
        return bool(self._cmd(cmd)[0] & 255)

    @property
    def toggle(self):
        """RTMP stream toggle."""
        return self.__cache['toggle']

    @toggle.setter
    def toggle(self, value):
        self.__backlog_('toggle', value)

    def _fps_(self, value=None):
        """Get or set RTMP frames-per-second.

        :param value: Frames-per-second, 1 - 60.
        """
        if value:
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
                                  self.__cmd_len)
        # Get!
        return self._cmd(__class__.pad([19, 1],
                                       self.__cmd_len))[0] & 255

    @property
    def fps(self):
        """Frames-per-second."""
        return self.__cache['fps']

    @fps.setter
    def fps(self, value):
        self.__backlog_('fps', value)

    def _led_(self, value=None):
        """Flash the LED."""
        cmd = [55, 0, 1]
        cmd = __class__.pad(cmd, self.__cmd_len)
        return __class__.echo(cmd, self._cmd(cmd))

    @property
    def led(self):
        """Flash the LED."""
        pass

    @led.setter
    def led(self, value):
        self.__backlog_('led', None)

    def _hdcp_(self):
        """Get HDCP status."""
        cmd = [5, 1]
        cmd = __class__.pad(cmd, self.__cmd_len)
        return bool(self._cmd(cmd)[0] & 255)

    @property
    def hdcp(self):
        """HDMI copy protection active."""
        return self.__cache['hdcp']

    def _mode_(self, value=None):
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
            __class__.str(value)

            mode = None
            for key, val in modes.items():
                if value.lower() == val:
                    mode = key
            if mode is None:
                err = _('unknown stream mode, must be one '
                        'of: {}'.format(list(modes.values())))
                raise Exception(err)
            cmd = __class__.pad([8, 0, mode], self.__cmd_len)
            return __class__.echo(cmd, self._cmd(cmd))

        # Get.
        mode = self._cmd(__class__.pad([8, 1], self.__cmd_len))[0] & 255
        return modes.get(mode)

    @property
    def mode(self):
        """Stream mode."""
        return self.__cache['mode']

    @mode.setter
    def mode(self, value):
        self.__backlog_('mode', value)

    def _firmware_(self):
        """Get firmware version."""
        ret = self._cmd(__class__.pad([56, 1], self.__cmd_len))
        major, minor, revision = [
            ret[0] & 255,
            ret[1] & 255,
            ret[2] & 255
        ]
        return '{}.{}.{}'.format(major, minor, revision)

    @property
    def firmware(self):
        """Firmware version."""
        return self.__cache['firmware']

    def _clients_(self):
        """Client ID and total connected clients. """
        ret = self._cmd(__class__.pad([50, 1], self.__cmd_len))
        return ret[0] & 255, ret[1] & 255

    @property
    def clients(self):
        """Current client number and total connected clients."""
        return self.__cache['clients']

    def _cache_(self):
        """Initialise/Update cache."""
        properties = {
            'url': self._url_(),
            'key': self._key_(),
            'username': self._username_(),
            'password': self._password_(),
            'brightness': self._brightness_(),
            'contrast': self._contrast_(),
            'hue': self._hue_(),
            'saturation': self._saturation_(),
            'hdmi': self._hdmi_(),
            'resolution': self._resolution_(),
            'picture': self._picture_(),
            'bitrate': self._bitrate_(),
            'toggle': self._toggle_(),
            'fps': self._fps_(),
            'hdcp': self._hdcp_(),
            'mode': self._mode_(),
            'firmware': self._firmware_(),
            'clients': self._clients_(),
        }
        for key, value in properties.items():
            self.__cache.update({
                key: value,
            })
        return self.__cache

    @property
    def settings(self):
        """Settings cache."""
        return self.__cache
