# Ant-FS
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

from base import Ant, Message

import array
import datetime
import struct

import logging

_logger = logging.getLogger("garmin.ant.fs")

class File:

    class State:
        INIT    = 0
        STARTED = 1
        DONE    = 2

    def  __init__(self, index, typ, sub, flags, size, date):
        self._state = File.State.INIT
        self._index = index
        self._type  = typ
        self._subtype = sub
        self._flags = flags
        self._size = size
        self._date = date

    def get_index(self):
        return self._index

    def get_type(self):
        return self._type

    def get_size(self):
        return self._size

    def get_date(self):
        return self._date

    def get_data(self):
        return self._data

    @staticmethod
    def parse(data):
        _logger.debug("Parse '%s' (%d) as file %s", data, len(data), type(data))

        (file_index, file_type, file_sub, flags, file_size, file_date) = \
            struct.unpack("<HBBxxxBII", data)
        file_date = datetime.datetime.fromtimestamp(file_date + 631065600)

        return File(file_index, file_type, file_sub, flags, file_size, file_date)


class Directory:
    def __init__(self, files):
        self._files = files;
        pass

    @staticmethod
    def parse(data):
        _logger.debug("Parse '%s' as directory", data)

        files = []
        for offset in range(16 , len(data), 16):
            item_data = data[offset:offset + 16]
            _logger.debug(" - (%d - %d) %d, %s", offset, offset + 16, len(item_data), item_data)
            files.append(File.parse(item_data))
        return Directory(files)


class Packet:

    class Type:
        DOWNLOAD = 0x89

    @staticmethod
    def is_packet(data):
        return len(data) > 40 and data[8] == 0x44 and data[9] == 0x89

    @staticmethod
    def parse(data):
        _logger.debug("Parse '%s' as packet", data)
        
        packet = Packet()
        packet._type, = struct.unpack("<xB", data[0:2])
        
        if packet._type == Packet.Type.DOWNLOAD:
            header = data[0:16]
            footer = data[-8:]
            packet._data = data[16:-8]
            packet._checksum = footer[-2:]

            # Is this packet data length, index, and total size?
            packet._left, packet._got, packet._total_size = struct.unpack("<4xIII", header)
        else:
            raise Exception("Unknown packet type " + str(packet._type))
        return packet

class Manager:

    class State:
        NONE = 0
        DOWNLOADING = 1

    class DownloadInfo:
        def __init__(self, index):
            self._index = index
            self._data = array.array('B')
            self._object = None

    def __init__(self, ant):
        self._state  = Manager.State.NONE
        self._object = None
        self._ant    = ant

    def download_index(self):
        self._state = Manager.State.DOWNLOADING
        self._download(0)

    def download(self, f):
        self._state = Manager.State.DOWNLOADING
        f.state = File.State.STARTED
        self._download(f.get_index())
        self._object._object = f


    def _download(self, index):
        self._object = Manager.DownloadInfo(index)

        _logger.debug("Request download of file with index %d", self._object._index)
        self._ant.send_burst_transfer(0x00, [\
            [0x44, 0x09,  self._object._index, 0x00, 0x00, 0x00, 0x00, 0x00], \
            [0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]])

    def on_data(self, data):
        _logger.debug("Got '%s' as data", data)
        
        # Remove ant header
        packet = Packet.parse(data[8:])
        
        _logger.debug("Got packet %s, type %d, pd %s, sd %s", packet, packet._type, packet._type == Packet.Type.DOWNLOAD, self._state == Manager.State.DOWNLOADING)
        _logger.debug("left %d, got %d, total %d, this %d", packet._left, packet._got, packet._total_size, len(packet._data))

        if self._state == Manager.State.DOWNLOADING and packet._type == Packet.Type.DOWNLOAD:
            #assert len(packet._data) == packet._left #don't always hold
            self._object._data += packet._data[0:packet._left]

            # File downloaded completely
            if(packet._left + packet._got == packet._total_size):
                _logger.debug("File %r done", self._object)

                self._object.state = File.State.DONE
                
                if self._object._index == 0:
                    return Directory.parse(self._object._data)
                else:
                    self._object._object._data = self._object._data
                    self._object._object._state = File.State.DONE
                    return self._object._object

            # Request next part
            else:
            
                _logger.debug("File %r continue from %d", self._object, packet._got + packet._left)
                # Start next request at index
                next = list(map(ord, struct.pack("<I", packet._got + packet._left)))
                self._ant.send_burst_transfer(0x00, [\
                    [0x44, 0x09, self._object._index, 0x00] + next, \
                    [0x00, 0x00] + packet._checksum.tolist() + [0x00, 0x00, 0x00, 0x00]])

        return None

