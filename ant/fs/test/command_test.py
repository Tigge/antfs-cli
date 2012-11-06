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

from ant.fs.command import parse, DownloadRequest, DownloadResponse,\
        AuthenticateCommand

def authenticate_command():

    command = AuthenticateCommand(
            AuthenticateCommand.Type.REQUEST_SERIAL, 123456789)
    assert command.get() == array.array('B',
            [0x44, 0x04, 0x01, 0x00, 0x15, 0xcd, 0x5b, 0x7])

    command = AuthenticateCommand(
            AuthenticateCommand.Type.REQUEST_PAIRING, 987654321,
            map(ord, 'hello'))
    assert command.get() == array.array('B',
            [0x44, 0x04, 0x02, 0x05, 0xb1, 0x68, 0xde, 0x3a,
             0x68, 0x65, 0x6c, 0x6c, 0x6f, 0x00, 0x00, 0x00])

def download_request():

    # Download request
    request = array.array('B', [0x44, 0x09, 0x5f, 0x00, 0x00, 0xba, 0x00,
        0x00, 0x00, 0x00, 0x9e, 0xc2, 0x00, 0x00, 0x00, 0x00])

    a = parse(request)
    assert isinstance(a, DownloadRequest)

def download_response():

    # Download response
    download_response = array.array('B', [68, 137, 0, 0, 241, 1, 0, 0, 0, 186, 0,
        0, 241, 187, 0, 0, 56, 4, 83, 78, 255, 255, 1, 12, 255, 255, 255,3, 72,
        129, 233, 42, 96, 64, 0, 0, 255, 255, 255, 255, 255, 255, 255, 255, 10,
        42, 0, 0, 73, 0, 0, 0, 255, 255, 255, 255, 255, 255, 255, 255, 2, 120,
        255, 99, 255, 2, 192, 129, 233, 42, 121, 0, 0, 0, 21, 3, 255, 71, 0, 0,
        19, 0, 33, 253, 4, 134, 2, 4, 134, 3, 4, 133, 4, 4, 133, 5, 4, 133, 6, 4,
        133, 7, 4, 134, 8, 4, 134, 9, 4, 134, 10, 4, 134, 27, 4, 133, 28, 4, 133,
        29, 4, 133, 30, 4, 133, 254, 2, 132, 11, 2, 132, 12, 2, 132, 13,2, 132,
        14, 2, 132, 19, 2, 132, 20, 2, 132, 21, 2, 132, 22, 2, 132, 0, 1, 0, 1,
        1, 0, 15, 1, 2, 16, 1, 2, 17, 1, 2, 18, 1, 2, 23, 1, 0, 24, 1, 0, 25, 1,
        0, 26, 1, 2, 7, 150, 130, 233, 42, 234, 120, 233, 42, 19, 218, 10, 41,
        131, 80, 137, 8, 208, 206, 10, 41, 220, 95, 137, 8, 22, 176, 32, 0,22,
        176, 32, 0, 88, 34, 9, 0, 255, 255, 255, 255, 172, 1, 11, 41, 164, 238,
        139, 8, 58, 63, 10, 41, 131, 80, 137, 8, 0, 0, 137, 2, 0, 0, 234, 10, 57,
        14, 255, 255, 255, 255, 184, 0, 227, 0, 9, 1, 164, 172, 255, 255, 255, 7,
        1, 255, 2, 150, 130, 233, 42, 1, 0, 0, 0, 8, 9, 1, 72, 0, 0, 18, 0, 34,
        253, 4, 134, 2, 4, 134, 3, 4, 133, 4, 4, 133, 7, 4, 134, 8, 4, 134, 9, 4,
        134, 10, 4, 134, 29, 4, 133, 30, 4, 133, 31, 4, 133, 32, 4, 133, 254, 2,
        132, 11, 2, 132, 13, 2, 132, 14, 2, 132, 15, 2, 132, 20, 2, 132, 21, 2,
        132, 22, 2, 132, 23, 2, 132, 25, 2, 132, 26, 2, 132, 0, 1, 0, 1, 1, 0, 5,
        1, 0, 6, 1, 0, 16, 1, 2, 17, 1, 2, 18, 1, 2, 19, 1, 2, 24, 1, 2, 27, 1, 2,
        28, 1, 0, 8, 150, 130, 233, 42, 234, 120, 233, 42, 19, 218, 10, 41, 131,
        80, 137, 8, 22, 176, 32, 0, 22, 176, 32, 0, 88, 34, 9, 0, 255, 255, 255,
        255, 172, 1, 11, 41, 164, 238, 139, 8, 58, 63, 10, 41, 131, 80, 137, 8, 0,
        0, 137, 2, 0, 0, 234, 10, 57, 14, 255, 255, 255, 255, 184, 0, 227, 0, 0,
        0, 1, 0, 9, 1, 1, 0, 164, 172, 255, 255, 46, 255, 0, 73, 0, 0, 34, 0, 7,
        253, 4, 134, 0, 4, 134, 1, 2, 132, 2, 1, 0, 3, 1, 0, 4, 1, 0, 6, 1, 2, 9,
        150, 130, 233, 42, 22, 176, 32, 0, 1, 0, 0, 26, 1, 255, 233, 66, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    a = parse(download_response)
    assert isinstance(a, DownloadResponse)

