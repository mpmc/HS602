#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  HS602.py
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

class HS602(object):

    """Controller for HS602-T."""
    def __init__(self, addr = None, udp_port = None, cmd_port = None,
                 udp_to = None, tcp_to = None, cmd_len = None):
        """Args:
            addr: Address of device or None. A broadcast
            message will be sent asking the device to reveal itself.
            udp_port: UDP port to send messages. If None default
            8086 used.
            cmd_port: TCP command port. If none default 8087 used.
            udp_to: UDP socket timeout, if none default 10 seconds used.
            tcp_to: TCP socket timeout If none default 30 seconds used.
            cmd_len: Length of data to receive from socket, default 15.
        """
        self.addr = addr or "<broadcast>"
        self.udp_port = udp_port or 8086
        self.cmd_port = cmd_port or 8087
        self.udp_to = udp_to or 10
        self.tcp_to = tcp_to or 30
        self.cmd_len = cmd_len or 15
        self.socket = None
        """Resolution modes."""
        self.modes = {0: "1920x1080 60Hz",
                      1: "1280x720 60Hz",
                      2: "720x480 60Hz",
                      3: "720x480 60Hz",
                      4: "720x480 60Hz",
                      5: "1920x1080 50Hz",
                      6: "1280x720 50Hz",
                      7: "720x576 50Hz",
                      8: "720x576 50Hz",
                      9: "720x576 50Hz",
                      10: "1920x1080 60Hz",
                      11: "1280x720 60Hz",
                      12: "720x480 60Hz",
                      13: "720x480 60Hz",
                      14: "1920x1080 50Hz",
                      15: "1280x720 50Hz",
                      16: "720x576 50Hz",
                      17: "720x576 50Hz",
                      18: "720x480 60Hz",
                      19: "720x576 50Hz",
                      20: "1920x1080 25Hz",
                      21: "1920x1080 30Hz",
                      22: "0x0 60Hz",
                      23: "640x480 60Hz",
                      24: "1920x1080 30Hz",
                      25: "1920x1080 25Hz",
                      26: "1920x1080 50Hz",
                      27: "1920x1080 60Hz",
                      28: "1920x1080 24Hz",
                      29: "1920x1080 60Hz",
                      30: "1920x1080 50Hz",
                      31: "1920x1080 24Hz",
                      32: "800x600 60Hz",
                      33: "1024x768 60Hz",
                      34: "1152x864 60Hz",
                      35: "1280x768 60Hz",
                      36: "1280x800 60Hz",
                      37: "1280x960 60Hz",
                      38: "1280x1024 60Hz",
                      39: "1360x768 60Hz",
                      40: "1440x900 60Hz",
                      41: "1600x900 60Hz",
                      42: "1680x1050 60Hz"}

    def udp(self, msg, reply = True):
        """Args:
            msg: The message (in bytes) to send.
            reply: Return the response?
        """
        """Create a socket & use it to send the message."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            """Set the options."""
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(self.udp_to)
            """Check the message was actually sent."""
            addr = (self.addr, self.udp_port)
            if not s.sendto(msg, addr) == len(msg):
                raise BrokenPipeError("Failed to send message")
            if reply:
                """Get the reply and return it."""
                data, source = s.recvfrom(2048)
                return data, source[0]
            else:
                return True

    def connect(self):
        """Discover and connect to device."""
        """Send discover message."""
        data, source = self.udp(bytes("HS602", 'utf-8'))
        """Make sure response is what we expect."""
        if not data.decode('utf-8') == "YES":
            raise Exception("Invalid reply")
        """We've discovered the device."""
        self.addr = source
        """Now ask the device to open the tcp port.
           This is just another UDP message sent direct to the box
           with the byte 67 / "C" (for connect maybe?) and device's
           IP address in reverse.
        """
        ip = reversed(self.addr.split("."))
        ip = [int(octet) for octet in ip]
        msg = bytes([67, ip[0], ip[1], ip[2], ip[3]])
        """Send it, we don't need a response! We'll then have about
           10 seconds to open a TCP connection.
        """
        self.udp(msg, False)
        """Create TCP socket & connect to the device."""
        self.socket = socket.create_connection((self.addr,
                                                self.cmd_port),
                                               self.tcp_to)
        return self.socket

    def send(self, msg, reply = True):
        """Send a command to the device & return the response.

           Args:
               msg: Message (in bytes) to send.
               reply: Return any responses.
        """
        """Open command connection if not already."""
        if not self.socket:
            self.connect()
        sent = self.socket.send(msg)
        if sent == 0:
            raise BrokenPipeError("Failed to send command")
        """Get the response."""
        data = bytes()
        data = self.socket.recv(self.cmd_len)
        return data

    def stream(self, param, value = None):
        """Get/Set stream parameters.

           Args:
               param: Parameter to get/set, possible values are..
               "username": Username for the streaming service.
               "password": Password for the streaming service.
               "rtmpkey": RTMP key used to auth.
               "rtmpurl": RTMP push url.
               value: The value of the to-be-set param, leave this
               as None to return the value.

            Notes:
                 Only rtmpkey & rtmpurl actually work. You can set the
                 the username & password but they have no effect at the
                 moment.
        """
        setting = {"password": 21,
                   "username": 20,
                   "rtmpkey": 17,
                   "rtmpurl": 16}
        if not param in setting:
            raise ValueError("Unknown param")
        start = [setting[param]]
        """If value is present we're setting it on the box."""
        if value:
            """Add zero byte to indicate that we're setting a value."""
            start += [0]
            """Don't set a value if it exceeds 255 chars."""
            if len(value) > 255:
                raise ValueError("Value cannot exceed 254 characters")
            """The device expects one char at a time with index."""
            for index, char in enumerate(value):
                cmd = bytes(start + [index & 255, ord(char)])
                r = self.send(cmd)
                """Make sure the box echos our command back."""
                if not r[:len(cmd)] == cmd:
                    raise Exception("Command echo mismatch")
            """The last packet is the total length of the value."""
            cmd = bytes(start + [len(value), 0])
            r = self.send(bytes(cmd))
            if not r[:len(cmd)] == cmd:
                raise Exception("Command echo mismatch (end)")
            return True
        """No value set, so we're getting a param."""
        start += [1]
        """Character index and value buffer."""
        index = 0
        value = ""
        """We need to loop until we've received all chars (max 255)."""
        while index < 254:
            cmd = start + [index & 255]
            r = self.send(bytes(cmd))
            dec = int(r[0])
            """Break if decimal is 0 or over 255."""
            if dec == 0 or dec > 255:
                break
            """Add the char to the buffer."""
            value += chr(dec)
            """Increment the index."""
            index += 1
        """Return the value."""
        return value

    def colour(self, param, value = None):
        """Get/Set colour values.

        Args:
            param: Parameter to get/set, possible values are..
            "brightness": Picture brightness.
            "contrast": Picture contrast.
            "hue": Picture hue.
            "saturation": Picture saturation.
            value: Int 0-255. Leave as None to return the current
            value from the box.

            Notes:
                 Changing colour value doesn't seem to work on HDMI
                 input. I assume it's just for YPbPr input only.
        """
        setting = {"brightness": 0,
                    "contrast": 1,
                    "hue": 2,
                    "saturation": 3}
        start = [10]
        """What colour param?"""
        if not param in setting:
            raise ValueError("Unknown colour param")
        """We're setting the value."""
        if value:
            """Make sure value is in the range accepted.."""
            if not int(value) >= 0 or int(value) > 255:
                raise ValueError("Value must be between 0-255.")
            """Send it!"""
            cmd = bytes(start + [0, setting[param], value & 255])
            r = self.send(cmd)
            """Make sure the box echos our command back."""
            if not r[:len(cmd)] == cmd:
                raise Exception("Box didn't acknowledge colour change")
            return True
        """We're getting the value."""
        cmd = start + [1, setting[param]]
        r = self.send(bytes(cmd))
        v = r[0] & 255
        """Is it in range?"""
        if not v >= 0 or v > 255:
            raise Exception("Box returned invalid colour value")
        return v

    def color(self, param, value = None):
        """Duplicate of colour function, for those who spell it
           differently!

           See colour above for arg details.

        """
        return self.colour(param, value)

    def resolution(self, text = False):
        """Get the input resolution value.

           Args:
               text: If true, return value will be string
               representation of the resolution mode reported by the
               box.
        """
        """Get the mode."""
        cmd = [4, 1]
        r = self.send(bytes(cmd))
        mode = r[0] & 255
        """Make sure the box returns a known mode."""
        if not mode in self.modes:
            raise Exception("Box returned invalid mode number")
        """Do we return the text repr or just the raw value?"""
        return self.modes[mode] if text else mode

    def source(self, source = None, text = False):
        """Get/Set the current input source.

           Args:
               source: Set this to 3 or 2 to tell the box to switch
               input source. Leave this as None to get current value.
               text: Return text representation of the value returned
               by the box (get only).

           Notes:
                3 = HDMI
                2 = YPbPr

                If setting the source and the return value is None
                it means nothing has been received from that input.
        """
        """Available inputs."""
        inputs = {2: "ypbpr",
                  3: "hdmi"}
        start = [1]
        """We're setting the input."""
        if source:
            if not source in inputs:
                raise Exception("Invalid input source number")
            cmd = start + [0, source & 255]
            r = self.send(bytes(cmd))
            ack = r[0] & 255
            mode = r[3] & 255
            """The box acknowledges the request and returns the mode.
               If the mode returned is 22 it means no video/audio
               is on that input at the current time.
            """
            if not mode in self.modes:
                raise Exception("Box returned invalid mode number")
            if ack == 1:
                return True if not mode == 22 else None
            """We should not reach here."""
            raise Exception("Box did not acknowledge source switch")
        """We're getting the current source input."""
        cmd = start + [1]
        r = self.send(bytes(cmd))
        source = r[0] & 255
        """Make sure the box returns a valid source number."""
        if not source in inputs:
            raise Exception("Box returned invalid source number")
        """Return it!"""
        return inputs[source] if text else source

    def is_streaming(self):
        """Get the current streaming status."""
        cmd = [15, 1];
        r = self.send(bytes(cmd))
        return bool(r[0] & 255)

    def toggle_streaming(self):
        """Tell the box to begin/end streaming."""
        cmd = bytes([15, 0])
        r = self.send(bytes(cmd))
        """Check for ack."""
        if not r[:len(cmd)] == cmd:
            raise Exception("Command echo mismatch (toggle streaming)")
        return True

    def size(self, height = None, width = None):
        """Get/Set size.

           Args:
               height: Picture height in pixels, e.g 1080.
               width: Picture width in pixels, e.g. 1920.

           Notes:
                Minimum/Max height: 640/1080
                Minimum/Max width: 480/1920
        """
        cmd = [3]
        """Make sure both height and width are set."""
        if height and not width or width and not height:
            raise ValueError("Both height and width must be defined")
        """ If both height and width are set, we're setting the size."""
        if height and width:
            """No floats!"""
            height = int(height)
            width = int(width)
            """Make sure the values are sane."""
            if height < 640 or height > 1080:
                height = 1080
            if width < 480 or width > 1920:
                width = 1920
            """Build the command."""
            cmd = bytes(cmd + [0, width & 255, (width >> 8) & 255,
                           (width >> 16) & 255, (width >> 24) & 255,
                            height & 255, (height >> 8) & 255,
                            (height >> 16) & 255, (height >> 24) & 255])
            """Send and get the response."""
            r = self.send(cmd)
            """Make sure the box echos our command back."""
            if not r[:len(cmd)] == cmd:
                raise Exception("Command echo mismatch (size)")
            return True
        """Get the current size."""
        cmd += [1]
        r = self.send(bytes(cmd))
        height = int((((r[0] & 255) + ((r[1] & 255) << 8)) +
                 ((r[2] & 255) << 16)) + ((r[3] & 255) << 24))
        width = int((((r[4] & 255) + ((r[5] & 255) << 8)) +
                ((r[6] & 255) << 16)) + ((r[7] & 255) << 24))
        """Make sure they're sane."""
        if height < 0 or height > 1080 or width < 0 or width > 1920:
            raise Exception("Box returned invalid size values")
        """Return a tuple of values."""
        return height, width

    def bitrate(self, value = None):
        """Get/Set bitrate.

           Args:
               value: the max allowed bitrate in kbps. Leave as
               None to return current value.
        """
        cmd = [2]
        """Set the value."""
        if value:
            cmd += [0]
            """Make sure value is int & in range."""
            value = int(value)
            if not value > 0 or value > 8000:
                """The default values on a reboot
                   are avg = 15000, min = 18000 highest = 13000.

                   These kinda feel backwards but anything higher and
                   the box screws up royally. Just use safe values.

                   Setting zero tells the box to use defaults.
                """
                value = 0
            """The Android app uses the following to generate
               the min/max values.
            """
            lowest = int(value * 7 / 10)
            highest = int(value * 14 / 10)
            """Use 0 if values exceed 8000."""
            if lowest > 8000 or highest > 8000:
                lowest = 0
                highest = 0
            """Build the command."""
            cmd += [value & 255, (value >> 8) & 255,
                    (value >> 16) & 255, (value >> 24) & 255,
                    lowest & 255, (lowest >> 8) & 255,
                    (lowest >> 16) & 255, (lowest >> 24) & 255,
                    highest & 255, (highest >> 8) & 255,
                    (highest >> 16) & 255, (highest & 24) & 255]
            """Send values!"""
            cmd = bytes(cmd)
            r = self.send(cmd)
            """Make sure box accepts command."""
            if not r[:len(cmd)] == cmd:
                raise Exception("Command echo mismatch (bitrate)")
            return True
        """Get the value."""
        cmd += [1]
        r = self.send(bytes(cmd))
        rate = int(((((r[1] & 255) << 8) | (r[0] & 255)) |
                ((r[2] & 255) << 16)) | ((r[3] & 255) << 24))
        """Done!"""
        return rate
