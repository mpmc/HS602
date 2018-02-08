#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hs602.py
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

gettext.install('Hs602')


class Controller(object):
    """HS602 controller."""
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
        """
        # Defaults.
        self.__addr_broadcast = '<broadcast>'
        self._addr = self.__addr_broadcast
        self._udp = 8086
        self._tcp = 8087
        self._timeout = 10
        self._ping = 'HS602'
        self._pong = 'YES'
        self._encoding = 'utf-8'
        self._cmd_len = 15
        self.__socket = None

        # Allow kwargs override.
        for key, value in kwargs.items():
            if hasattr(self, "_{}".format(key)):
                func = getattr(self, "_{}_set".format(key))
                func(value)

    def _socket_get(self):
        """Return the socket handle."""
        return self.__socket

    def _close(self, value=None):
        """Kill the connection."""
        try:
            # If this fails we can ignore it.
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
        except (OSError, AttributeError):
            pass
        self.__socket = None

    socket = property(_socket_get, _close)

    @staticmethod
    def _properties_get():
        """Dictionary containing command properties (nested dictionary).
        """
        values = {
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
        # Color/Colour workaround.
        values['color'] = values['colour']
        return values

    properties = property(_properties_get)

    @staticmethod
    def _valid_str(value):
        """Return true if string value is 1-255 in length."""
        value = str(value)
        if len(value) in range(1, 256):
            return True
        raise ValueError(_('invalid value, requires a string of 1-255 '
                           'in length'))

    @staticmethod
    def _valid_int(value):
        """Return true if int value is 1-255."""
        value = int(value)
        if value in range(1, 256):
            return True
        raise ValueError(_('invalid value, requires a number between '
                           '1 and 255'))

    @staticmethod
    def _valid_port(value):
        """Return true if port int value is 1-65535."""
        value = int(value)
        if value in range(1, 65536):
            return True
        raise ValueError(_('invalid value, requires a port number '
                           'between 1 and 65535'))

    @staticmethod
    def _echo(first, second):
        """Check if two variables are equal.

        :param first: first object.
        :param second: second object.
        """
        return first == second

    def _addr_get(self):
        """Device address (string).

        Setting a value will kill existing sockets.
        """
        return str(self._addr)

    def _addr_set(self, value):
        """Set device address - will kill existing sockets.

        :param value: device (or broadcast) address to set.
        """
        self._addr = str(value)
        # Close any existing sockets if addr is set.
        self._close()

    addr = property(_addr_get, _addr_set)

    def _udp_get(self):
        """UDP broadcast port, 1-65535 (integer).

        Setting a value will kill existing sockets.
        """
        return int(self._udp)

    def _udp_set(self, value):
        """Set UDP broadcast port - will kill existing sockets.

        :param value: UDP to broadcast on, uses default if not 1-65535.
        """
        if not self._valid_port(value):
            return
        self._udp = int(value)
        # Close any existing sockets if udp is set.
        self._close()

    udp = property(_udp_get, _udp_set)

    def _tcp_get(self):
        """TCP command port, 1-65535 (integer).

        Setting a value will kill existing sockets.
        """
        return int(self._tcp)

    def _tcp_set(self, value):
        """Set TCP command port - will kill existing sockets.

        :param value: TCP command port, uses default if not 1-65535.
        """
        if not self._valid_port(value):
            return
        self._udp = int(value)
        # Close any existing sockets if tcp is set.
        self._close()

    tcp = property(_tcp_get, _tcp_set)

    def _timeout_get(self):
        """Socket timeout, 1-255 (integer)."""
        return int(self._timeout)

    def _timeout_set(self, value):
        """Set socket timeout.

        :param value: timeout value 1-255.
        """
        if not self._valid_int(value):
            return
        self._udp = int(value)

    timeout = property(_timeout_get, _timeout_set)

    def _cmd_len_get(self):
        """Command length (integer)."""
        return int(self._cmd_len)

    def _cmd_len_set(self, value):
        """Set expected command length.

        :param value: command length.
        """
        self._cmd_len = int(value)

    cmd_len = property(_cmd_len_get, _cmd_len_set)

    def _encoding_get(self):
        """Message encoding (string)."""
        return str(self._encoding)

    def _encoding_set(self, value):
        """Set message encoding.

        :param value: encoding value.
        """
        self._encoding = str(value)

    encoding = property(_encoding_get, _encoding_set)

    def _ping_get(self):
        """Ping trigger message (string)."""
        return str(self._ping).encode(self.encoding)

    def _ping_set(self, value):
        """Set ping trigger message.

        :param value: ping value.
        """
        self._ping = str(value)

    ping = property(_ping_get, _ping_set)

    def _pong_get(self):
        """Expected pong reply (string)."""
        return str(self._pong).encode(self.encoding)

    def _pong_set(self, value):
        """Set pong reply.

        :param value: expected pong reply.
        """
        self._pong = str(value)

    pong = property(_pong_get, _pong_set)

    def _pad(self, data, pad_len=None):
        """Append data with zero bytes to the size of pad_len.

        :param data: data to pad, can be anything that can be
        converted to bytes.
        :param pad_len: size required, if not set will use self.cmd_len.
        """
        pad_len = pad_len or self.cmd_len
        data = bytes(data)
        data = data.ljust(pad_len, b'\0')
        return data

    def _udp_msg(self, msg, reply=True):
        """Send UDP message.

        Return a list of replies, an empty list is returned if
        nothing is received.

        :param msg: message (in bytes) to send.
        :param reply: do we want to wait for a reply?
        """
        msg = bytes(msg)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(self._timeout_get())
            s.bind(('', self._udp_get()))

            replies = list()
            while True:
                # Send message.
                if msg:
                    sent = s.sendto(msg, (self._addr_get(),
                                          self._udp_get()))
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

    def _cmd(self, msg, reply=True):
        """Send command to device - If no address is set
        self.devices_get() will be called & the first device to reply
        is used.

        Return the reply. true if message was sent without error
        (when no reply needed).

        :param msg: message (in bytes) to send.
        :param reply: do we want to wait for a reply?
        """
        msg = bytes(msg)
        # Do we need to discover a device first?
        addr = self._addr_get()
        if not addr or addr.lower() == self.__addr_broadcast.lower():
            self._addr_set(self._devices_get()[0])
        # If there is no connection, so tell the device to
        # get ready to accept one.
        #
        # This is just the the "C" char and the IPv4 address of the
        # box in reverse.
        if not self.__socket:
            ip = reversed(self._addr_get().split('.'))
            cmd = [67] + [int(octal) for octal in ip]
            self._udp_msg(cmd, False)
            addr = (self._addr_get(), self._tcp_get())
            addr = addr, self._timeout_get()
            self.__socket = socket.create_connection(*addr)

        # Send it & get replies (if needed).
        self.__socket.sendall(msg)
        if not reply:
            return True
        data = bytes()
        while True:
            buf = self.__socket.recv(self._cmd_len_get())
            if not buf:
                self._close()
                break
            data += buf
            if len(data) == self._cmd_len_get():
                break
        return data

    def _devices_get(self):
        """Discovered devices (list).

        Return a list of devices (even if none are found).
        This will send a ping to self.addr:self.udp) & wait for
        replies, it will block until timeout is reached.
        """
        # Reset to defaults.
        self.__init__()
        res = self._udp_msg(self._ping_get())
        if res:
            return [rep[0] for rep in res if rep[2] == self._pong_get()]

    devices = property(_devices_get)

    def _rtmp_get(self, param):
        """Get an RTMP value.

        :param param: see _properties_get()['rtmp'].
        """
        opt = self._properties_get()['rtmp']
        cmd = [opt[param.lower()], 1]
        index = 0
        buf = ''
        while index < 254:
            result = self._pad(cmd + [index])
            dec = int(self._cmd(result)[0] & 255)
            if dec == 0:
                break
            buf += chr(dec)
            index += 1
        return buf

    def _rtmp_set(self, param, value):
        """Set RTMP values.

        :param param: see _properties_get()['rtmp'].
        :param value: value to set, max length 255.
        """
        opt = self._properties_get()['rtmp']
        cmd = [opt[param.lower()], 0]
        # Too long?
        if not self._valid_str(value):
            return

        # Send each char.
        for index, char in enumerate(value):
            char_cmd = self._pad(cmd + [index, ord(char)])
            # Ack?
            if not self._echo(char_cmd, self._cmd(char_cmd)):
                return

        # Finally, send the total length.
        cmd = self._pad(cmd + [len(value), 0])
        return self._echo(cmd, self._cmd(cmd))

    def _url_get(self):
        """RTMP URL, length 1-255 (string)."""
        return self._rtmp_get('url')

    def _url_set(self, value):
        """Set RTMP URL on device.

        :param value: URL to set - length must be 1-255.
        """
        if not self._valid_str(value):
            return
        return self._rtmp_set('url', value)

    url = property(_url_get, _url_set)

    def _key_get(self):
        """RTMP key, length 1-255 (string)."""
        return self._rtmp_get('key')

    def _key_set(self, value):
        """Set RTMP key on device.

        :param value: key to set - length must be 1-255.
        """
        if not self._valid_str(value):
            return
        return self._rtmp_set('key', value)

    key = property(_key_get, _key_set)

    def _username_get(self):
        """RTMP username, length 1-255 (string)."""
        return self._rtmp_get('username')

    def _username_set(self, value):
        """Set RTMP username on device.

        :param value: Username to set - length must be 1-255.
        """
        if not self._valid_str(value):
            return
        return self._rtmp_set('username', value)

    username = property(_username_get, _username_set)

    def _password_get(self):
        """RTMP password, length 1-255 (string)."""
        return self._rtmp_get('password')

    def _password_set(self, value):
        """Set RTMP password on device.

        :param value: password to set - length must be 1-255.
        """
        if not self._valid_str(value):
            return
        return self._rtmp_set('password', value)

    password = property(_password_get, _password_set)

    def _colour_get(self, param):
        """Get colour parameter value.

        :param param: see _properties_get()['colour'].
        """
        opt = self._properties_get()['colour']
        # What colour param?
        cmd = self._pad([10, 1, opt[param.lower()]])
        result = int(self._cmd(cmd)[0] & 255)
        return result

    def _colour_set(self, param, value):
        """Set colour parameter value.

        :param param: see properties_get()['colour']
        :param value: value to set, 0 - 255.
        """
        opt = self._properties_get()['colour']
        # What colour param?
        cmd = self._pad([10, 0, opt[param.lower()], value & 255])
        return self._echo(cmd, self._cmd(cmd))

    def _brightness_get(self):
        """Colour brightness, 1-255 (integer)."""
        return self._colour_get('brightness')

    def _brightness_set(self, value):
        """Set colour brightness.

        :param value: brightness to set - int 1-255.
        """
        if not self._valid_int(value):
            return
        return self._colour_set('brightness', value)

    brightness = property(_brightness_get, _brightness_set)

    def _contrast_get(self):
        """Colour contrast, 1-255 (integer)."""
        return self._colour_get('contrast')

    def _contrast_set(self, value):
        """Set colour contrast.

        :param value: contrast to set - int 1-255.
        """
        if not self._valid_int(value):
            return
        return self._colour_set('contrast', value)

    contrast = property(_contrast_get, _contrast_set)

    def _hue_get(self):
        """Colour hue, 1-255 (integer)."""
        return self._colour_get('hue')

    def _hue_set(self, value):
        """Set colour hue.

        :param value: hue to set - int 1-255.
        """
        if not self._valid_int(value):
            return
        return self._colour_set('hue', value)

    hue = property(_hue_get, _hue_set)

    def _saturation_get(self):
        """Colour saturation, 1-255 (integer)."""
        return self._colour_get('saturation')

    def _saturation_set(self, value):
        """Set colour saturation.

        :param value: saturation to set - int 1-255.
        """
        if not self._valid_int(value):
            return
        return self._colour_set('saturation', value)

    saturation = property(_saturation_get, _saturation_set)

    def _source_get(self):
        """Input source (integer/string).

        Return an integer, getting the value:
            0 = hdmi
            1 = ypbpr

        Return a bool, setting the value (case insensitive):
            0, "hdmi" or anything else will set input to hdmi.
            1 or "ypbpr" will set input to analogue.
        """
        cmd = self._pad([1, 1])
        ret = self._cmd(cmd)[0] & 255
        if ret is 3:
            return 0
        elif ret is 2:
            return 1
        raise ValueError(_('valid source number returned'))

    def _source_set(self, source=None):
        """Set source.

        :param source: set to ypbpr or 1 to switch to analogue input,
        will default to hdmi otherwise.
        """
        if isinstance(source, str):
            source = source.lower()
        if source in [_('ypbpr'), 1]:
            source = 2
        else:
            source = 3
        cmd = self._pad([1, 0, source & 255])
        return bool(self._cmd(cmd)[0] & 255)

    source = property(_source_get, _source_set)

    def _source_str(self):
        """Source input, hdmi or ypbpr (string)."""
        ret = self._source_get()
        if ret is 0:
            return _('hdmi')
        elif ret is 1:
            return _('ypbpr')

    source_str = property(_source_str)

    def _resolution_get(self):
        """Currently-reported input resolution (integer).

        See properties['resolution'] or use resolution_str.
        """
        cmd = self._pad([4, 1])
        return self._cmd(cmd)[0] & 255

    resolution = property(_resolution_get)

    def _resolution_str_get(self):
        """Currently-reported resolution (string).

        See properties['resolution'].
        """
        modes = self._properties_get()['resolution']
        res = self._resolution_get()
        if res not in modes:
            return _('unknown')
        return str(modes[res])

    resolution_str = property(_resolution_str_get)

    def _picture_size_get(self):
        """Current (output) picture size - width, height (tuple).

        Set using tuple, e.g, "size = 1920, 1080"
        """
        cmd = self._pad([3, 1])
        result = self._cmd(cmd)
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
        if width not in range(0, 1921) or height not in range(0, 1081):
            raise ValueError(_('invalid width and/or height returned'))
        return width, height

    def _picture_size_set(self, width, height):
        """Set (output) picture size.

        :param width: picture width.
        :param height: picture height.
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
        cmd = self._pad([3, 0] + width + height)
        return self._echo(cmd, self._cmd(cmd))

    def _size_set(self, value=None):
        """Sets picture size.

        :param value: tuple, e.g, "size = 1920, 1080".
        """
        try:
            wid = value[0]
            hei = value[1]
            if wid not in range(1, 1921) or hei not in range(1, 1081):
                raise ValueError
        except (TypeError, KeyError):
            raise ValueError(_('invalid width and/or height, or not a '
                               'tuple, e.g, "size = 1920, 1080".'))
        x = self._picture_size_set(wid, hei)
        print(x)
        return x

    size = property(_picture_size_get, _size_set)

    def _picture_size_str_get(self):
        """Current (output) picture size (string).
        "width x height" (no spaces), e.g, 720x576.
        """
        return "{}x{}".format(*self._picture_size_get())

    size_str = property(_picture_size_str_get)

    def _bitrate_get(self):
        """Average (stream) bitrate, 500-8000 (integer)."""
        cmd = self._pad([2, 1])
        result = self._cmd(cmd)
        # This is split like this to make it less ugly (still is).
        onezero = (result[1] & 255) << 8 | (result[0] & 255)
        twothree = (result[2] & 255) << 16 | (result[3] & 255) << 24
        return onezero | twothree

    def _bitrate_set(self, average):
        """Set the bitrate.

        :param average: the average bitrate to use.
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
        cmd = self._pad([2, 0] + average + low + high)
        return self._echo(cmd, self._cmd(cmd))

    bitrate = property(_bitrate_get, _bitrate_set)

    def _toggle_get(self):
        """Streaming toggle (bool).

        Set to anything to toggle, check toggle again afterwards.

        Return true (streaming) or false (not streaming).
        """
        cmd = self._pad([15, 1])
        return bool(self._cmd(cmd)[0] & 255)

    def _toggle_set(self, value=None):
        """Toggle start/stop streaming."""
        cmd = self._pad([15, 0])
        return self._echo(cmd, self._cmd(cmd))

    toggle = property(_toggle_get, _toggle_set)

    def _fps_get(self):
        """Frames-per-second - 1-60 (int)."""
        ret = self._cmd(self._pad([19, 1]))[0] & 255
        return ret

    def _fps_set(self, value=None):
        """Frames-per-second.

        :param value: frames-per-second to set - 1-60.
        """
        value = int(value)
        if value not in range(1, 61):
            value = 60
        fps = [
            value & 255,
            (value >> 8) & 255,
            (value >> 16) & 255,
            (value >> 24) & 255,
        ]
        cmd = self._pad([19, 0] + fps)
        ret = self._cmd(cmd)[2]
        if ret == value:
            return True

    fps = property(_fps_get, _fps_set)

    def _led_set(self, value=None):
        """Flash LED.

        You can't set this, just call it, e.g, foo.led.
        """
        cmd = self._pad([55, 0, 0 & 255])
        return self._echo(cmd, self._cmd(cmd))

    led = property(_led_set, _led_set)

    def _keepalive_set(self, value=None):
        """Send an (empty) keep-alive message to the device..

        You can't set this, just call it, e.g, foo.keepalive, Calling
        led works just as well :).
        """
        cmd = self._pad([0])
        return self._echo(cmd, self._cmd(cmd))

    keepalive = property(_keepalive_set, _keepalive_set)

    def _hdcp_get(self):
        """HDMI copy protection status."""
        cmd = self._pad([5, 1])
        ret = self._cmd(cmd)[0] & 255
        return bool(ret)

    hdcp = property(_hdcp_get)

    def _multicast_set(self, value=None):
        """Multicast (network wide broadcast on port 8085).

        You can't set this, just call it, e.g, foo.multicast.
        """
        cmd = self._pad([8, 0, 1])
        return self._echo(cmd, self._cmd(cmd))

    multicast = property(_multicast_set, _multicast_set)

    def _unicast_get(self):
        """Unicast (network wide broadcast on port 8085) (object).

        Set to anything to trigger, check again afterwards.
        """
        cmd = self._pad([8, 1])
        return self._echo(cmd, self._cmd(cmd))

    def _unicast_set(self, value=None):
        """Unicast.
        Return true or false.
        """
        cmd = self._pad([8, 0, 0])
        return self._echo(cmd, self._cmd(cmd))

    unicast = property(_unicast_get, _unicast_set)

    def _version_get(self):
        """Return the device version as tuple."""
        cmd = self._pad([56, 1])
        ret = self._cmd(cmd)
        major, minor, revision = [
            ret[0] & 255,
            ret[1] & 255,
            ret[2] & 255
        ]
        return major, minor, revision

    firmware_version = property(_version_get)

    def _version_str_get(self):
        """Return version as string"""
        major, minor, revision = self.firmware_version
        return "{}.{}.{}".format(major, minor, revision)

    firmware_version_str = property(_version_str_get)

    def _clients_get(self):
        """Return client id number & total connected clients."""
        cmd = self._pad([50, 1])
        current, total = cmd[0] & 255, cmd[1] & 255
        return current, total

    clients = property(_clients_get)

    def _settings_get(self):
        """Return all device settings (dictionary).

        Pass a dictionary to save settings.
        """
        return {
            _('url'): self.url,
            _('key'): self.key,
            _('username'): self.username,
            _('password'): self.password,
            _('brightness'): self.brightness,
            _('contrast'): self.contrast,
            _('hue'): self.hue,
            _('saturation'): self.saturation,
            _('source'): self.source,
            _('source_str'): self.source_str,
            _('resolution'): self.resolution,
            _('resolution_str'): self.resolution_str,
            _('picture_size'): self.size,
            _('picture_size_str'): self.size_str,
            _('bitrate'): self.bitrate,
            _('toggle'): self.toggle,
            _('fps'): self.fps,
            _('hdcp'): self.hdcp,
            _('unicast'): self.unicast,
            _('clients'): self.clients,
            _('firmware'): self.firmware_version,
            _('firmware_str'): self.firmware_version_str,
        }

    def _settings_set(self, settings):
        """Save passed settings.

           :param settings: A dictionary containing key, value pairs.
        """
        for name, value in settings.items():
            if hasattr(self, name):
                setattr(self, name, value)

    settings = property(_settings_get, _settings_set)
