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

from ant.fs.commandpipe import parse, CreateFile

def main():

    # Test create file
    data    = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09]
    request = CreateFile(len(data), 0x80, [0x04, 0x00, 0x00], [0x00, 0xff, 0xff])
    print request
    print request.get()
    
    # Test create file response
    response_data = array.array('B', [2, 0, 0, 0, 4, 0, 0, 0, 128, 4, 123, 0, 103, 0, 0, 0])
    response = parse(response_data)
    assert response.get_request_id() == 0x04
    assert response.get_response()   == 0x00
    assert response.get_data_type()  == 0x80 #FIT
    assert response.get_identifier() == array.array('B', [4, 123, 0])
    assert response.get_index()      == 103

