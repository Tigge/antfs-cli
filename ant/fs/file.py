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

import datetime
import logging
import struct

_logger = logging.getLogger("garmin.ant.fs.file")

class Directory:
    def __init__(self, version, time_format, current_system_time,
            last_modified, files):
        self._version = version
        self._time_format = time_format
        self._current_system_time = current_system_time
        self._last_modified = last_modified
        self._files = files

    def get_version(self):
        return self._version

    def get_files(self):
        return self._files

    @staticmethod
    def parse(data):
        _logger.debug("Parse '%s' as directory", data)

        # Header
        version, structure_length, time_format, current_system_time, \
            last_modified = struct.unpack("<BBB5xII", data[:16])

        version_major = (version & 0xf0) >> 4
        version_minor = (version & 0x0f)
    
        files = []
        for offset in range(16 , len(data), 16):
            item_data = data[offset:offset + 16]
            _logger.debug(" - (%d - %d) %d, %s", offset, offset + 16, len(item_data), item_data)
            files.append(File.parse(item_data))
        return Directory((version_major, version_minor), time_format,
                current_system_time, last_modified, files)


class File:

    class Type:
        FIT     = 0x80

    class Identifier:
        pass

    def  __init__(self, index, typ, ident, typ_flags, flags, size, date):
        self._index = index
        self._type = typ
        self._ident = ident
        self._typ_flags = typ_flags
        self._flags = flags
        self._size = size
        self._date = date

    def get_index(self):
        return self._index

    def get_type(self):
        return self._type

    def get_identifier(self):
        return self._ident

    def get_size(self):
        return self._size

    def get_date(self):
        return self._date

    @staticmethod
    def parse(data):
        _logger.debug("Parse '%s' (%d) as file %s", data, len(data), type(data))

        # i1, i2, i3 -> three byte integer, not supported by struct
        (index, data_type, data_i1, data_i2, data_i3, data_flags, flags, \
            file_size, file_date) = struct.unpack("<HB3BBBII", data)
        file_date  = datetime.datetime.fromtimestamp(file_date + 631065600)
        identifier = data_i1 + data_i2 << 8 + data_i3 << 16

        return File(index, data_type, identifier, data_flags, flags, file_size, file_date)


