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

import array
import collections
import copy
import logging
import struct

_logger = logging.getLogger("garmin.ant.fs.command")

class Command:
    
    class Type:
        
        # Commands
        LINK                  = 0x02
        DISCONNECT            = 0x03
        AUTHENTICATE          = 0x04
        PING                  = 0x05
        
        DOWNLOAD_REQUEST      = 0x09
        UPLOAD_REQUEST        = 0x0A
        ERASE_REQUEST         = 0x0B
        UPLOAD_DATA           = 0x0C
        
        # Responses
        AUTHENTICATE_RESPONSE = 0x84
        DOWNLOAD_RESPONSE     = 0x89
        UPLOAD_RESPONSE       = 0x8A
        ERASE_RESPONSE        = 0x8B
        UPLOAD_DATA_RESPONSE  = 0x8C
    
    _format = "<BB"
    _id     = None
    
    def __init__(self):
        self._arguments = collections.OrderedDict()
        self._add_argument('x',  0x44)
        self._add_argument('id', self._id)
    
    def _add_argument(self, name, value):
        self._arguments[name] = value
    
    def _get_argument(self, name):
        return self._arguments[name]
    
    def _get_arguments(self):
        return self._arguments.values()
    
    def get_id(self):
        return self._id

    def get(self):
        data = struct.pack(self._format, *self._get_arguments())
        lst  = array.array('B', data)
        _logger.debug("packing %r in %r,%s", data, lst, type(lst))
        return lst

    @classmethod
    def _parse_args(cls, data):
        return struct.unpack(cls._format, data)

    @classmethod
    def _parse(cls, data):
        args = cls._parse_args(data)
        assert args[0] == 0x44
        assert args[1] == cls._id
        return cls(*args[2:])

    def _debug(self):
        max_key_length, max_value_length = 0, 0
        for key, value in self._arguments.items():
            max_key_length = max(len(str(key)), max_key_length)
            max_value_length = max(len(str(value)), max_value_length)
        max_length = max_key_length + max_value_length + 3
        print "=" * max_length
        print self.__class__.__name__
        print "-" * max_length
        for key, value in self._arguments.items():
            print str(key) + ":", " " * (max_length - len(key)), str(value)
        print "=" * max_length

class LinkCommand(Command):
    
    _id     = Command.Type.LINK
    _format = Command._format + "BBI"
    
    def __init__(self, channel_frequency, channel_period, host_serial_number):
        Command.__init__(self)
        self._add_argument("channel_frequency", channel_frequency)
        self._add_argument("channel_period", channel_period)
        self._add_argument("host_serial_number", host_serial_number)

class DisconnectCommand(Command):
    
    class Type:
        RETURN_LINK             = 0
        RETURN_BROADCAST        = 1

    _id     = Command.Type.DISCONNECT
    _format = Command._format + "BBBxxx"

    def __init__(self, command_type, time_duration, application_specific_duration):
        Command.__init__(self)
        self._add_argument("command_type", command_type)
        self._add_argument("time_duration", time_duration)
        self._add_argument("application_specific_duration", application_specific_duration)

class AuthenticateBase(Command):
    
    _format = None

    def __init__(self, x_type, serial_number, data = []):
        Command.__init__(self)
        self._add_argument("type", x_type)
        self._add_argument("serial_number", serial_number)
        self._add_argument("data", data)

    def _pad(self, data):
        padded_data = copy.copy(data)
        missing = 8 - len(padded_data) % 8
        if missing < 8:
            padded_data.extend([0x00] * missing)
        return padded_data

    def get_serial(self):
        return self._get_argument("serial_number")

    def get_data_string(self):
        if self._get_argument("data") == []:
            return None
        else:
            return "".join(map(chr, self._get_argument("data")))

    def get_data_array(self):
        return self._get_argument("data")

    def get(self):
        lst = array.array('B', struct.pack("<BBBBI", self._get_arguments()[0],
                self._get_arguments()[1], self._get_arguments()[2],
                len(self._get_argument("data")), self._get_arguments()[3]))
        padded = self._pad(self._get_argument("data"))
        lst.extend(array.array('B', padded))
        return lst

    @classmethod
    def _parse_args(cls, data):
        header = struct.unpack("<BBBxI", data[0:8])
        data_length = data[3]
        return header + (data[8:8 + data_length],)

class AuthenticateCommand(AuthenticateBase):
    
    class Request:
        PASS_THROUGH     = 0
        SERIAL           = 1
        PAIRING          = 2
        PASSKEY_EXCHANGE = 3
    
    _id     = Command.Type.AUTHENTICATE

    def __init__(self, command_type, host_serial_number, data = []):
        AuthenticateBase.__init__(self, command_type, host_serial_number, data)

class AuthenticateResponse(AuthenticateBase):
    
    class Response:
        NOT_AVAILABLE = 0
        ACCEPT        = 1
        REJECT        = 2
    
    _id     = Command.Type.AUTHENTICATE_RESPONSE

    def __init__(self, response_type, client_serial_number, data = []):
        AuthenticateBase.__init__(self, response_type, client_serial_number, data)

class PingCommand(Command):
    
    _id     = Command.Type.PING


class DownloadRequest(Command):
    
    _id     = Command.Type.DOWNLOAD_REQUEST
    _format = Command._format + "HIx?HI"
    
    def __init__(self, data_index, data_offset, initial_request, crc_seed,
                 maximum_block_size = 0):
        Command.__init__(self)
        self._add_argument("data_index", data_index)
        self._add_argument("data_offset", data_offset)
        self._add_argument("initial_request", initial_request)
        self._add_argument("crc_seed", crc_seed)
        self._add_argument("maximum_block_size", maximum_block_size)

class DownloadResponse(Command):
    
    class Response:
        OK              = 0
        NOT_EXIST       = 1
        NOT_READABLE    = 2
        NOT_READY       = 3
        INVALID_REQUEST = 4
        INCORRECT_CRC   = 5
    
    _id     = Command.Type.DOWNLOAD_RESPONSE
    _format = None
    
    def __init__(self, response, remaining, offset, size, data, crc):
        Command.__init__(self)
        self._add_argument("response", response)
        self._add_argument("remaining", remaining)
        self._add_argument("offset", offset)
        self._add_argument("size", size)
        self._add_argument("data", data)
        self._add_argument("crc", crc)
    
    @classmethod
    def _parse_args(cls, data):
        return struct.unpack("<BBBxIII", data[0:16]) + \
            (data[16:-8],) + struct.unpack("<6xH", data[-8:])

class UploadRequest(Command):
    
    _id     = Command.Type.UPLOAD_REQUEST
    _format = Command._format + "HI4xI"
    
    def __init__(self, data_index, max_size, data_offset):
        Command.__init__(self)
        self._add_argument("data_index", data_index)
        self._add_argument("max_size", max_size)
        self._add_argument("data_offset", data_offset)


class UploadResponse(Command):
    
    class Response:
        OK               = 0
        NOT_EXIST        = 1
        NOT_WRITEABLE    = 2
        NOT_ENOUGH_SPACE = 3
        INVALID_REQUEST  = 4
        NOT_READY        = 5
    
    _id     = Command.Type.UPLOAD_RESPONSE
    _format = Command._format + "BxIII6xH"
    
    def __init__(self, response, last_data_offset, maximum_file_size,
                 maximum_block_size, crc):
        Command.__init__(self)
        self._add_argument("response", response)
        self._add_argument("last_data_offset", last_data_offset)
        self._add_argument("maximum_file_size", maximum_file_size)
        self._add_argument("maximum_block_size", maximum_block_size)
        self._add_argument("crc", crc)


class UploadDataCommand(Command):
    
    _id     = Command.Type.UPLOAD_DATA
    _format = None

    def __init__(self, crc_seed, data_offset, data, crc):
        Command.__init__(self)
        self._add_argument("crc_seed", crc_seed)
        self._add_argument("data_offset", data_offset)
        self._add_argument("data", data)
        self._add_argument("crc", crc)

    def get(self):
        header = struct.pack("<BBHI", *self._get_arguments()[:4])
        footer = struct.pack("<6xH", self._get_argument("crc"))
        data = array.array('B', header)
        data.extend(self._get_argument("data"))
        data.extend(array.array('B', footer))
        return data

    @classmethod
    def _parse_args(cls, data):
        return struct.unpack("<BBHI", data[0:8]) + \
            (data[8:-8],) + struct.unpack("<6xH", data[-8:])

class UploadDataResponse(Command):
    
    class Response:
        OK     = 0
        FAILED = 1
    
    _id     = Command.Type.UPLOAD_DATA_RESPONSE
    _format = Command._format + "B5x"
    
    def __init__(self, response):
        Command.__init__(self)
        self._add_argument("response", response)


class EraseRequestCommand(Command):
    
    _id     = Command.Type.ERASE_REQUEST
    _format = Command._format + "I"
    
    def __init__(self, data_file_index):
        Command.__init__(self)
        self._add_argument("data_file_index", data_file_index)

class EraseResponse(Command):
    
    class Response:
        ERASE_SUCCESSFUL = 0
        ERASE_FAILED     = 1
        NOT_READY        = 2
    
    _id     = Command.Type.ERASE_RESPONSE
    _format = Command._format + "B"
    
    def __init__(self, response):
        Command.__init__(self)
        self._add_argument("response", response)


_classes = {
    # Commands
    Command.Type.LINK:                  LinkCommand,
    Command.Type.DISCONNECT:            DisconnectCommand,
    Command.Type.AUTHENTICATE:          AuthenticateCommand,
    Command.Type.PING:                  PingCommand,
    
    Command.Type.DOWNLOAD_REQUEST:      DownloadRequest,
    Command.Type.UPLOAD_REQUEST:        UploadRequest,
    Command.Type.ERASE_REQUEST:         EraseRequestCommand,
    Command.Type.UPLOAD_DATA:           UploadDataCommand,
    
    # Responses
    Command.Type.AUTHENTICATE_RESPONSE: AuthenticateResponse,
    Command.Type.DOWNLOAD_RESPONSE:     DownloadResponse,
    Command.Type.UPLOAD_RESPONSE:       UploadResponse,
    Command.Type.ERASE_RESPONSE:        EraseResponse,
    Command.Type.UPLOAD_DATA_RESPONSE:  UploadDataResponse}

def parse(data):
    _logger.debug("parsing data %r", data)
    mark, command_type  = struct.unpack("<BB", data[0:2])
    assert mark == 0x44
    command_class = _classes[command_type]
    
    return command_class._parse(data)

