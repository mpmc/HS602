# Copyright (C) 2019 Mark Clarkstone <mpmc@disroot.org>
# 
# This file is part of hs602.
# 
# hs602 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# hs602 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with hs602.  If not, see <http://www.gnu.org/licenses/>.

import socket
import gettext

gettext.install('hs602_controller')


class Controller(object):
    """Controller for HS602-based devices."""
    def __init__(self, addr=None, tcp=8087, udp=8086, listen=8085,
                 timeout=10, cmd_len=15):
        """
        :param addr: Address of device.
        :param tcp: TCP command port - default 8087.
        :param udp: UDP broadcast port - default 8086.
        :param listen: Stream receive port - default 8085.
        :param timeout: Socket timeout - default 10.
        :param cmd_len: Server-defined command length - default 15.
        """
        self.addr = str(addr)
        self.tcp = int(tcp)
        self.udp = int(udp)
        self.listen = int(listen)
        self.timeout = int(timeout)
        self.cmd_len = int(cmd_len)

        self.socket = None
        self.udp_socket = None

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

        :param data: Data to pad, must be a list.
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

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(timeout)
            if bind:
                sock.bind(('', port))
            else:
                sock.connect((__class__.str(addr), port))
            return sock
        except OSError as exc:
            raise Exception(_('can\'t connect or bind')) from exc

    @staticmethod
    def socket_shutdown(sock):
        """Shutdown a given socket.

        :param sock: Socket to shutdown.
        """
        try:
            # If this fails we can ignore it.
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        except (OSError, AttributeError):
            pass
        sock = None

    def udp_msg(self, addr, port, msg, reply=True, timeout=5,
                encoding='utf-8'):
        """Send a UDP message.

        :param addr: Host address.
        :param port: Port to send the message on.
        :param msg: Message to send (will be converted to bytes).
        :param reply: Reply needed?
        :param timeout: Socket timeout.
        :param encoding: Message encoding.
        """
        msg = __class__.bytes(msg, encoding)
        port = __class__.port(port)
        timeout = __class__.int(timeout)

        self.udp_socket = __class__.sock(addr='', port=port,
                                         timeout=timeout, udp=True)

        replies = list()
        sent = 0
        while True:
            # Send message.
            if msg:
                sent = self.udp_socket.sendto(msg, (addr, port))
                if not sent > 0:
                    break
                msg = msg[sent:]
                continue

            # Receive message?
            if not reply:
                return
            try:
                data, [addr, port] = self.udp_socket.recvfrom(2048)
                replies += [[addr, port, data]]
            except (socket.error, socket.gaierror,
                    socket.herror, socket.timeout, OSError):
                break

        # Make sure the socket is completely cleaned up.
        self.socket_shutdown(self.udp_socket)
        return replies

    def cmd(self, msg, new=False):
        """Send command to device.

        :param msg: Command message.
        :param new: Force new socket.
        """
        msg = __class__.bytes(msg)
        data_len = self.cmd_len
        addr = __class__.str(self.addr)
        udp = __class__.port(self.udp)
        tcp = __class__.port(self.tcp)
        timeout = __class__.int(self.timeout)

        addr = socket.gethostbyname(addr)
        ip = reversed(addr.split('.'))
        knock = [67] + [int(octal) for octal in ip]

        # Do we require a new socket?
        if not self.socket or new:
            try:
                # Knock.
                self.udp_msg(addr=addr, port=udp, msg=knock,
                             reply=False)
            except Exception as exc:
                raise Exception(_('failed to knock')) from exc

            # Connect!
            self.socket = __class__.sock(addr=addr, port=tcp,
                                         timeout=timeout)
        try:
            # Send!
            self.socket.sendall(msg, 0)
            data = bytes()

            while True:
                # Receive reply.
                buf = self.socket.recv(1024)
                if not buf:
                    raise OSError(_('command socket dead'))
                data += buf
                # Return the response.
                if len(data) >= data_len:
                    return data
        except Exception as exc:
            # Close the socket.
            self.socket_shutdown(self.socket)
            raise Exception(_('failed to receive and/or send '
                              'command')) from exc

    def shutdown(self):
        """Shutdown thread(s) and connection(s)."""
        self.socket_shutdown(self.udp_socket)
        self.socket_shutdown(self.socket)

    __del__ = stop = close = shutdown

    def led(self):
        """Flash LED."""
        cmd = [55, 0, 1]
        cmd = __class__.pad(cmd, self.cmd_len)
        return __class__.echo(cmd, self.cmd(cmd))

    def hdcp(self):
        """HDCP (High-bandwidth Digital Content Protection) state."""
        cmd = [5, 1]
        cmd = __class__.pad(cmd, self.cmd_len)
        return bool(self.cmd(cmd)[0] & 255)

    def firmware(self):
        """Firmware version."""
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

    def resolution(self):
        """Current input resolution."""
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
            raise Exception(_('server returned unknown resolution'))
        return resolutions.get(ret)

    def keepalive(self):
        """Send keepalive message"""
        cmd = __class__.pad([0], self.cmd_len)
        return __class__.echo(cmd, self.cmd(cmd))

    def source(self, hdmi=None):
        """Get/Set source input - HDMI or Analogue.

        :param hdmi: True for HDMI, False for analogue.
        """
        # Get.
        ret = self.cmd(__class__.pad([1, 1], self.cmd_len))[0] & 255
        if ret not in [2, 3]:
            raise Exception(_('server returned invalid source id'))

        ret = 'hdmi' if ret is 3 else 'analogue'

        # Set.
        if hdmi is not None:
            cmd = [1, 0, 2]
            if hdmi:
                cmd = [1, 0, 3]

            cmd = __class__.pad(cmd, self.cmd_len)
            self.cmd(cmd)
            return self.source()

        return ret

    def rtmp(self, option, new_value=None):
        """Get/Set RTMP option.

        :param option: One of: url, key, username or password.
        :param new_value: New value.
        """
        options = {
            'url': 16,
            'key': 17,
            'username': 20,
            'password': 21,
            'name': 23,
        }
        # What's the option?
        orig_opt = str(option).lower()
        option = options.get(orig_opt, None)
        if not option:
            raise Exception(_('unknown rtmp option {}, must be one of: '
                              '{}').format(orig_opt,
                                           list(options.keys())))
        # Get.
        cmd = [option, 1]
        buf = ret = ''
        for pos in range(0, 255):
            dec = int(self.cmd(cmd + [pos])[0] & 255)
            if not dec:
                break
            buf += chr(dec)
        ret = buf

        if new_value:
            cmd = [option, 0]
            # Is what we're setting too long?
            __class__.str(new_value)
            for pos, char in enumerate(new_value):
                char_cmd = __class__.pad(cmd + [pos, ord(char)],
                                         self.cmd_len)
                if not __class__.echo(char_cmd, self.cmd(char_cmd)):
                    raise Exception(_('server rejected rtmp {} new '
                                      'value at char '
                                      '{}').format(orig_opt, char))

            # Has the server accepted the new value?
            cmd = __class__.pad(cmd + [len(new_value), 0], self.cmd_len)
            if not __class__.echo(cmd, self.cmd(cmd)):
                raise Exception(_('server rejected new rtmp {} value'
                                  '{}').format(orig_opt, new_value))
            ret = str(new_value)

        # Done!
        return ret

    def url(self, new_value=None):
        """Get/Set RTMP URL.

        :param new_value: URL to set.
        """
        if new_value is not None:
            return self.rtmp('url', new_value)
        return self.rtmp('url')

    def key(self, new_value=None):
        """Get/Set RTMP key.

        :param new_value: Key to set.
        """
        if new_value is not None:
            return self.rtmp('key', new_value)
        return self.rtmp('key')

    def username(self, new_value=None):
        """Get/Set RTMP username.

        :param new_value: Username to set.
        """
        if new_value is not None:
            return self.rtmp('username', new_value)
        return self.rtmp('username')

    def password(self, new_value=None):
        """Get/Set RTMP password.

        :param new_value: Password to set.
        """
        if new_value is not None:
            return self.rtmp('password', new_value)
        return self.rtmp('password')

    def name(self, new_value=None):
        """Get/Set RTMP channel name.

        :param new_value: RTMP name to set.
        """
        # Version 56 of the firmware doesn't support channel name.
        if self.firmware().startswith('56'):
            return ''

        if new_value is not None:
            return self.rtmp('name', new_value)
        return self.rtmp('name')

    def colour(self, option, new_value=None):
        """Get/Set a colour value.

        :param option: Desired colour option: brightness, contrast,
        hue or saturation.
        :param new_value: New colour value - 0 - 255
        """
        options = {
            'brightness': 0,
            'contrast': 1,
            'hue': 2,
            'saturation': 3,
        }
        orig_opt = str(option).lower()
        option = options.get(orig_opt, None)
        if option is None:
            raise Exception(_('unknown colour option {}, must be one '
                              'of: {}').format(orig_opt,
                                               list(options.keys())))

        # Get colour value.
        ret = int(self.cmd([10, 1, option])[0] & 255)

        # Set new colour value.
        if new_value is not None:
            __class__.int(new_value)
            cmd = __class__.pad([10, 0, option, new_value],
                                self.cmd_len)
            if not __class__.echo(cmd, self.cmd(cmd)):
                raise Exception(_('server rejected new {} value {}')
                                .format(orig_opt, new_value))
            ret = int(new_value)

        return ret

    def brightness(self, new_value=None):
        """Get/Set brightness.

        :param new_value: New brightness level, 0 - 255 - default 128.
        """
        if new_value is not None:
            return self.colour('brightness', new_value)
        return self.colour('brightness')

    def contrast(self, new_value=None):
        """Get/Set contrast.

        :param new_value: New contrast level, 0 - 255 - default 128.
        """
        if new_value is not None:
            return self.colour('contrast', new_value)
        return self.colour('contrast')

    def hue(self, new_value=None):
        """Get/Set hue.

        :param new_value: New hue level, 0 - 255 - default 128.
        """
        if new_value is not None:
            return self.colour('hue', new_value)
        return self.colour('hue')

    def saturation(self, new_value=None):
        """Get/Set saturation.

        :param new_value: New saturation level, 0 - 255 - default 128.
        """
        if new_value is not None:
            return self.colour('saturation', new_value)
        return self.colour('saturation')

    def picture(self, new_value=None):
        """Get/Set RTMP output picture size.

        :param new_value: RTMP picture size. Set as two values,
        e.g, "1920,1080".

        This is width by height.
        """
        w_range = range(0, 1921)
        h_range = range(0, 1081)
        ret_value = orig_val = ''

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
            raise Exception(_('server returned invalid values - '
                              'width {} height {}').format(width,
                                                           height))
        ret_value = '{},{}'.format(width, height)

        # Set the value.
        if new_value is not None:
            # Try a string split.
            try:
                new_value = new_value.replace(" ", "")
                orig_val = new_value
                new_value = new_value.split(',', 2)
            except AttributeError:
                pass

            try:
                width = int(new_value[0].strip())
                height = int(new_value[1].strip())
                if width not in w_range or height not in h_range:
                    raise ValueError
            except (TypeError, IndexError, ValueError) as exc:
                raise Exception(_('invalid width or height, max width '
                                  '1920, height 1080 - set as two  '
                                  'values e.g, "1920,1080"')) from exc

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
            # Server accepted?
            if not __class__.echo(cmd, self.cmd(cmd)):
                raise Exception(_('server rejected new picture size '
                                  '{}').format(orig_val))
            ret_value = orig_val

        # Done
        return ret_value

    def bitrate(self, new_value=None):
        """Get/Set the average RTMP bitrate.

        :param new_value: New average bitrate - 500 - 20000.
        """
        # Get value.
        ret = self.cmd(__class__.pad([2, 1]))
        onezero = (ret[1] & 255) << 8 | (ret[0] & 255)
        twothree = (ret[2] & 255) << 16 | (ret[3] & 255) << 24
        ret_val = onezero | twothree

        if new_value is not None:
            try:
                average = int(new_value)
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

            if not __class__.echo(cmd, self.cmd(cmd)):
                raise Exception(_('server rejected new bitrate '
                                  '{}').format(new_value))
            ret_val = new_value
        return ret_val

    def streaming(self, toggle=False):
        """Get/Set RTMP stream state.

        :param toggle: Set to toggle RTMP streaming state.

        """
        # Get current value.
        cmd = __class__.pad([15, 1], self.cmd_len)
        ret = bool(self.cmd(cmd)[0] & 255)

        if toggle:
            cmd = __class__.pad([15, 0], self.cmd_len)
            if not __class__.echo(cmd, self.cmd(cmd)):
                raise Exception(_('server rejected toggling stream '
                                  'state'))
            return self.streaming()
        return ret

    def fps(self, new_value=None):
        """Get/Set RTMP frames-per-second.

        :param new_value: New frames-per-second value, 1 - 60.
        """
        # Get!
        ret = self.cmd(__class__.pad([19, 1], self.cmd_len))[0] & 255

        # Set!
        if new_value is not None:
            __class__.int(new_value)
            if new_value not in range(1, 61):
                new_value = 60
            new_value = round(int(new_value))
            fps = [
                new_value & 255,
                (new_value >> 8) & 255,
                (new_value >> 16) & 255,
                (new_value >> 24) & 255,
            ]
            if not __class__.echo(__class__.pad([19, 0] + fps),
                                  self.cmd_len):
                raise Exception(_('server rejected new fps {}')
                                .format(new_value))
            return new_value

        return ret

    def mode(self, new_value=None):
        """Get/Set RTP/UDP stream mode.

        :param new_value: new stream mode: unicast, broadcast, tcp.
        """

        modes = ['unicast', 'broadcast', 'tcp']

        # Get.
        mode = self.cmd(__class__.pad([8, 1], self.cmd_len))[0] & 255
        ret = modes[mode]

        # Set.
        if new_value is not None:
            new_value = __class__.str(new_value).lower()
            orig_val = new_value
            try:
                new_value = modes.index(new_value)
            except ValueError as exc:
                raise ValueError(_('unknown stream mode - supported '
                                   'modes: {}'.format(modes))) from exc
            cmd = __class__.pad([8, 0, new_value], self.cmd_len)

            if not __class__.echo(cmd, self.cmd(cmd)):
                raise Exception(_('server rejected new stream mode {}')
                                .format(orig_val))
            return orig_val
        return ret

    def base_port(self, new_value):
        """Set device base port.

        :param new_value: New base port number.
        """
        port = __class__.port(new_value)
        cmd = bytes([14, 0]) + port.to_bytes(2, byteorder='little')
        cmd = __class__.pad(cmd, self.cmd_len)
        return __class__.echo(cmd, self.cmd(cmd))

    def discover(self, encoding='utf-8', ping='HS602', pong='YES',
                 broadcast='<broadcast>', udp=8086):
        """Get a list of available devices.

        :param encoding: Message encoding - default 'utf-8'.
        :param ping: Ping message - default 'HS602'.
        :param pong: Pong message - default 'YES'.
        :param broadcast: Address to send message - default
        '<broadcast>'.
        :param udp: Port on which to send message - default 8086.

        """
        encoding = str(encoding)
        ping = __class__.bytes(ping, encoding)
        pong = __class__.bytes(pong, encoding)
        broadcast = __class__.str(broadcast)
        udp = __class__.port(udp)

        try:
            ret = self.udp_msg(addr=broadcast, port=udp, msg=ping,
                               encoding=encoding)
        except Exception as exc:
            raise Exception('discovery failure') from exc
        return [rep[0] for rep in ret if rep[2] == pong]

    def settings(self, **kwargs):
        """Get all/Set settings.

        :param kwargs: (optional) keyword args [with values] to update.

        The passed keyword args should be class method names, for
        example settings(fps=60, username=demo ...)
        """
        read_only = [
            'resolution',
            'clients',
            'firmware',
            'hdcp',
        ]
        modifiable = [
            'mode',
            'fps',
            'streaming',
            'bitrate',
            'picture',
            'saturation',
            'hue',
            'contrast',
            'brightness',
            'username',
            'password',
            'key',
            'url',
            'name',
            'source',
        ]
        settings = {}

        for method_name in read_only + modifiable:
            method_name = '{}'.format(method_name).lower()
            method = getattr(self, method_name)
            value = None

            # Do we have a value to pass along?
            try:
                value = kwargs[method_name]
            except KeyError:
                pass
            # Read only methods do not accept a value!
            if method_name in read_only:
                settings[method_name] = method()
                continue

            settings[method_name] = method(value)

        # Add misc keys & values.
        settings.update({
            'addr': self.addr,
            'tcp': self.tcp,
            'udp': self.udp,
            'listen': self.listen,
            'timeout': self.timeout,
            'len': self.cmd_len,
        })
        return settings
