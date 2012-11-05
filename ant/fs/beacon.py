# Ant
#
# Copyright (c) 2012, Gustav Tiger <gustav@tiger.name>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import struct

class Beacon:
    
    class ClientDeviceState:
        LINK           = 0x00 # 0b0000
        AUTHENTICATION = 0x01 # 0b0001
        TRANSPORT      = 0x02 # 0b0010
        BUSY           = 0x03 # 0b0011

    BEACON_ID = 0x43

    def is_data_available(self):
        return bool(self._status_byte_1 & 0x20) # 0b00100000

    def is_upload_enabled(self):
        return bool(self._status_byte_1 & 0x10) # 0b00010000

    def is_pairing_enabled(self):
        return bool(self._status_byte_1 & 0x08) # 0b00001000

    def get_channel_period(self):
        return self._status_byte_1 & 0x07 # 0b00000111, TODO

    def get_client_device_state(self):
        return self._status_byte_2 & 0x0f # 0b00001111, TODO

    def get_serial(self):
        return struct.unpack("<I", self._descriptor)[0]

    def get_descriptor(self):
        return struct.unpack("<HH", self._descriptor)

    @staticmethod
    def parse(data):
        values = struct.unpack("<BBBB4x", data)
        
        assert values[0] == 0x43
        
        beacon = Beacon()
        beacon._status_byte_1 = values[1]
        beacon._status_byte_2 = values[2]
        beacon._authentication_type = values[3]
        beacon._descriptor = data[4:]
        return beacon

