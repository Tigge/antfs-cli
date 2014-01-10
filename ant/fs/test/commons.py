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

# Most significant bit first (big-endian)
# x^16+x^12+x^5+1 = (1) 0001 0000 0010 0001 = 0x1021
def crc(data):
    rem = 0
    # A popular variant complements rem here
    for byte in data:
        rem ^= (byte << 8)  # n = 16 in this example
        for _ in range(0, 8):     # Assuming 8 bits per byte
            if rem & 0x8000:    # if leftmost (most significant) bit is set
                rem = (rem << 1)
                rem ^= 0x1021
            else:
                rem = rem << 1
            rem = rem & 0xffff # Trim remainder to 16 bits
    return "done", bin(rem)


print crc(array.array("B", "Wikipedia"))
    
