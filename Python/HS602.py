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
            addr: Address of device or None. If None a broadcast
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
            if not s.sendto(msg, (self.addr, self.udp_port)) == len(msg):
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

    def get_version(self):
        """Return version number.

           I'm not even sure this is correct as the box just echos
           it back.
        """
        cmd = [56, 1]
        r = self.send(bytes(cmd))
        version = str(r[0]) + str(r[1]) + str(r[2])
        return version

    def set_param(self, param = None, value = None):
        """Set string parameter.

           Args:
               param: Parameter to set, possible values are..
               "username": Username for the streaming service.
               "password": Password for the streaming service.
               "rtmpkey": RTMP key used to auth.
               "rtmpurl": RTMP push url.
               value: The value of the to-be-set param.

            Notes:
                Only rtmpkey & rtmpurl actually work. You can set the
                the username & password but they have no effect at the
                moment.
        """
        """Bail if value exceeds 254 chars, so we don't crash the box"""
        if len(value) > 254:
            raise ValueError("Value cannot exceed 254 characters")
        """Which parameter are we setting?"""
        if param is "password":
            start = [21, 0]
        elif param is "username":
            start = [20, 0]
        elif param is "rtmpkey":
            start = [17, 0]
        elif param is "rtmpurl":
            start = [16, 0]
        else:
            raise ValueError("Unknown param")
        """The device expects one character at a time with an index."""
        for index, char in enumerate(value):
            cmd = bytes(start + [index & 255, ord(char)])
            reply = self.send(cmd)
            """Make sure the box echos our command back."""
            if not reply[:len(cmd)] == cmd:
                raise Exception("Command echo mismatch")
        """The last packet is the total length of the value."""
        end = start + [len(value), 0]
        self.send(bytes(end))
        return True

    def get_param(self, param = None):
        """Get string parameter.

           Args:
               param: Parameter to get, possible values are..
               "username": Username for the streaming service.
               "password": Password for the streaming service.
               "rtmpkey": RTMP key used to auth.
               "rtmpurl": RTMP push url.
        """
        """Which parameter are we getting?"""
        if param is "password":
            start = [21, 1]
        elif param is "username":
            start = [20, 1]
        elif param is "rtmpkey":
            start = [17, 1]
        elif param is "rtmpurl":
            start = [16, 1]
        else:
            raise ValueError("Unknown param")
        """Character index and value buffer."""
        index = 0
        value = ""
        """We need to loop until we've received all characters."""
        while True:
            cmd = start + [index & 255]
            reply = self.send(bytes(cmd))
            dec = int(reply[0])
            """Break if decimal is 0, over 255 or the index hits 254."""
            if dec == 0 or dec > 255 or index > 254:
                break
            """Add the char to the buffer."""
            value += chr(dec)
            """Increment the index."""
            index += 1
        """Return the value."""
        return value

    def is_streaming(self):
        """Get the current streaming status."""
        cmd = [15, 1];
        reply = self.send(bytes(cmd))
        return bool(reply[0] & 255)

    def toggle_streaming(self):
        """Tell the box to begin/end streaming."""
        cmd = [15, 0]
        self.send(bytes(cmd))
        return True
