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

    def print_list(self):
        print "Index\tType\tFIT Type\tFIT Number\tSize\tDate\tFIT Flags\tFlags"
        for f in self.get_files():
            print f.get_index(), "\t", f.get_type(), "\t",\
                  f.get_fit_sub_type(), "\t", f.get_fit_file_number(), "\t",\
                  f.get_size(), "\t", f.get_date(), "\t", f._typ_flags, "\t",\
                  f.get_flags_string()

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
        DEVICE           = 1
        SETTING          = 2
        SPORT_SETTING    = 3
        ACTIVITY         = 4
        WORKOUT          = 5
        COURSE           = 6
        WEIGHT           = 9
        TOTALS           = 10
        GOALS            = 11
        BLOOD_PRESSURE   = 14
        ACTIVITY_SUMMARY = 20

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

    def get_fit_sub_type(self):
        return self._ident[0]

    def get_fit_file_number(self):
        return struct.unpack("<xH", self._ident)[0]

    def get_size(self):
        return self._size

    def get_date(self):
        return self._date

    def get_flags_string(self):
        s  = "r" if self._flags & 0b00001000 == 0 else "-"
        s += "w" if self._flags & 0b00010000 == 0 else "-"
        s += "e" if self._flags & 0b00100000 == 0 else "-"
        s += "a" if self._flags & 0b01000000 == 0 else "-"
        s += "A" if self._flags & 0b10000000 == 0 else "-"
        return s

    @staticmethod
    def parse(data):
        _logger.debug("Parse '%s' (%d) as file %s", data, len(data), type(data))

        # i1, i2, i3 -> three byte integer, not supported by struct
        (index, data_type, data_flags, flags, file_size, file_date) \
                 = struct.unpack("<HB3xBBII", data)
        file_date  = datetime.datetime.fromtimestamp(file_date + 631065600)
        identifier = data[3:6]

        return File(index, data_type, identifier, data_flags, flags, file_size, file_date)


