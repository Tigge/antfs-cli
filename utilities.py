# Utilities
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

import errno
import os

def makedirs_if_not_exists(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else: 
            raise


class XDGError(Exception):
    
    def __init__(self, message):
        self.message = message

class XDG:

    def __init__(self, application):
        self._application = application

    def get_data_dir(self):
        if "XDG_DATA_HOME" in os.environ:
            return os.path.join(os.environ["XDG_DATA_HOME"], self._application)
        elif "HOME" in os.environ:
            return os.path.join(os.environ["HOME"], ".local/share", self._application)
        else:
            raise XDGError("Neither XDG_DATA_HOME nor HOME found in the environment")
        
    def get_config_dir(self):
        if "XDG_CONFIG_HOME" in os.environ:
            return os.path.join(os.environ["XDG_CONFIG_HOME"], self._application)
        elif "HOME" in os.environ:
            return os.path.join(os.environ["HOME"], ".config", self._application)
        else:
            raise XDGError("Neither XDG_CONFIG_HOME nor HOME found in the environment")

