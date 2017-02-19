#!/usr/bin/env python
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
    def __init__(self, broadcast_addr = None,
                 broadcast_port = None, cmd_port = None,
                 udp_timeout = None, tcp_timeout = None):
        """Args:
               broadcast_addr: UDP broadcast address to send messages.
               broadcast_port: Port to broadcast UDP messages on.
               cmd_port: TCP command port the device is listening on.
               udp_timeout: UDP socket timeout.
               tcp_timeout: TCP socket timeout.
        """
        self.broadcast_addr = broadcast_addr or "<broadcast>"
        self.broadcast_port = broadcast_port or 8086
        self.cmd_port = cmd_port or 8087
        self.cmd_len = 15
        self.udp_timeout = udp_timeout or 10
        self.tcp_timeout = tcp_timeout or 10
        self.device_addr = None
        self.socket = None
        
    def udp(self, msg, addr = None, reply = True):
        """Send UDP message.
            
           Args:
               msg: Message to send (in bytes).
               addr: Optional address to send message, will use 
               self.broadcast_addr as default.
               reply: Return response?
        """
        addr = addr or self.broadcast_addr
        port = self.broadcast_port
        """Create a socket & use it to send the message."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            """Set the socket options."""
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(self.udp_timeout)
            """Send the message & make sure it was sent correctly."""
            if not s.sendto(msg, (addr, port)) == len(msg):
                raise BrokenPipeError("Failed to send message")
            if reply:
                """Return the reply."""
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
        self.device_addr = source
        """Now ask the device to open the tcp port. 
           This is just another UDP message sent direct to the box 
           with the byte 67 / "C" (for connect maybe?) and device's 
           IP address in reverse. 
        """
        ip = reversed(self.device_addr.split("."))
        ip = [int(octet) for octet in ip]
        msg = bytes([67, ip[0], ip[1], ip[2], ip[3]])
        """Send it, we don't need a response! We'll then have about 
           10 seconds to open a TCP connection.
        """
        self.udp(msg, self.device_addr, False)
        """Create TCP socket & connect to the device."""
        self.socket = socket.create_connection((self.device_addr, 
                                               self.cmd_port),
                                               self.tcp_timeout)
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
        """Send message."""
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
        
    def set_string_param(self, param = None, value = None):
        """Set string parameter on the box.
        
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
            raise Exception("Unknown param")
        """The device expects one character at a time with an index."""
        for index, char in enumerate(value):
            cmd = start + [index & 255, ord(char)]
            self.send(bytes(cmd))
        """The last packet is the total length of the value."""
        end = start + [len(value), 0]
        self.send(bytes(end))
        return True
        
    def is_streaming(self):
        """Get the current streaming status."""
        cmd = [15, 1];
        reply = self.send(bytes(cmd))
        return bool(reply[0])

    def toggle_streaming(self):
        """Tell the box to begin/end streaming."""
        cmd = [15, 0]
        self.send(bytes(cmd))
        return True
