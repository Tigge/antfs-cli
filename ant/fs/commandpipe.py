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
import logging
import struct

_logger = logging.getLogger("garmin.ant.fs.commandpipe")

class CommandPipe:
    
    class Type:
        
        REQUEST                    = 0x01
        RESPONSE                   = 0x02
        TIME                       = 0x03
        CREATE_FILE                = 0x04
        DIRECTORY_FILTER           = 0x05
        SET_AUTHENTICATION_PASSKEY = 0x06
        SET_CLIENT_FRIENDLY_NAME   = 0x07
        FACTORY_RESET_COMMAND      = 0x08

    _format = "<BxxB"
    _id     = None

    def __init__(self):
        self._arguments = collections.OrderedDict()
        self._add_argument('command',  self._id)
        self._add_argument('sequence', 0)

    def _add_argument(self, name, value):
        self._arguments[name] = value
    
    def _get_argument(self, name):
        return self._arguments[name]
    
    def _get_arguments(self):
        return self._arguments.values()

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
        assert args[0] == cls._id
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

class Request(CommandPipe):
    
    _id     = CommandPipe.Type.REQUEST
    _format = CommandPipe._format + "Bxxx"

    def __init__(self, request_id):
        CommandPipe.__init__(self)

class Response(CommandPipe):
    
    class Response:
        OK            = 0
        FAILED        = 1
        REJECTED      = 2
        NOT_SUPPORTED = 3
    
    _id     = CommandPipe.Type.RESPONSE
    _format = CommandPipe._format + "BxBx"

    def get_request_id(self):
        return self._get_argument("request_id")

    def get_response(self):
        return self._get_argument("response")

    def __init__(self, request_id, response):
        CommandPipe.__init__(self)
        self._add_argument('request_id', request_id)
        self._add_argument('response', response)

class Time(CommandPipe):
    
    class Format:
        DIRECTORY = 0
        SYSTEM    = 1
        COUNTER   = 2
    
    _id     = CommandPipe.Type.TIME
    _format = CommandPipe._format + "IIBxxx"
    
    def __init__(self, current_time, system_time, time_format):
        CommandPipe.__init__(self)


class CreateFile(CommandPipe):
    
    _id     = CommandPipe.Type.CREATE_FILE
    _format = None

    def __init__(self, size, data_type, identifier, identifier_mask):
        CommandPipe.__init__(self)
        self._add_argument('size', size)
        self._add_argument('data_type', data_type)
        self._add_argument('identifier', identifier)
        self._add_argument('identifier_mask', identifier_mask)

    def get(self):
        data = array.array('B', struct.pack(CommandPipe._format + "IB",
                           *self._get_arguments()[:4]))
        data.extend(self._get_argument("identifier"))
        data.extend([0])
        data.extend(self._get_argument("identifier_mask"))
        return data

    @classmethod
    def _parse_args(cls, data):
        return struct.unpack(Command._format + "IB", data[0:9])\
                + (data[9:12],) + (data[13:16],)


class CreateFileResponse(Response):

    _format = Response._format + "BBBBHxx"

    def __init__(self, request_id, response, data_type, identifier, index):
        Response.__init__(self, request_id, response)
        self._add_argument('data_type', data_type)
        self._add_argument('identifier', identifier)
        self._add_argument('index', index)

    def get_data_type(self):
        return self._get_argument("data_type")

    def get_identifier(self):
        return self._get_argument("identifier")
    
    def get_index(self):
        return self._get_argument("index")

    @classmethod
    def _parse_args(cls, data):
        return Response._parse_args(data[:8]) + \
                (data[8], data[9:12], struct.unpack("<H", data[12:14])[0])

_classes = {
    CommandPipe.Type.REQUEST:                     Request,
    CommandPipe.Type.RESPONSE:                   Response,
    CommandPipe.Type.TIME:                       Time,
    CommandPipe.Type.CREATE_FILE:                CreateFile,
    CommandPipe.Type.DIRECTORY_FILTER:           None,
    CommandPipe.Type.SET_AUTHENTICATION_PASSKEY: None,
    CommandPipe.Type.SET_CLIENT_FRIENDLY_NAME:   None,
    CommandPipe.Type.FACTORY_RESET_COMMAND:      None}

_responses = {
    CommandPipe.Type.CREATE_FILE:                CreateFileResponse}

def parse(data):
    commandpipe_type = _classes[data[0]]
    if commandpipe_type == Response:
        if data[4] in _responses:
            commandpipe_type = _responses[data[4]]
    return commandpipe_type._parse(data)

