#!/usr/bin/python
#
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

#from ant.base import Message
#from ant.easy.node import Node, Message
#from ant.easy.channel import Channel
from ant.fs.manager import Application

import utilities
import scripting

import array
import logging
import os
import struct
import sys
import traceback

ID_VENDOR  = 0x0fcf
ID_PRODUCT = 0x1008

PRODUCT_NAME = "garmin-extractor"

_logger = logging.getLogger("garmin")

class Garmin(Application):

    ID_VENDOR  = 0x0fcf
    ID_PRODUCT = 0x1008

    PRODUCT_NAME = "garmin-extractor"

    def __init__(self):
        Application.__init__(self)
        
        _logger.debug("Creating directories")
        self.config_dir = utilities.XDG(self.PRODUCT_NAME).get_config_dir()
        self.script_dir = os.path.join(self.config_dir, "scripts")
        utilities.makedirs_if_not_exists(self.config_dir)
        utilities.makedirs_if_not_exists(self.script_dir)
        
        self.scriptr  = scripting.Runner(self.script_dir)

    def read_passkey(self, serial):

        try:
            path = os.path.join(self.config_dir, str(serial))
            with open(os.path.join(path, "authfile"), 'rb') as f:
                d = list(struct.unpack("<8B", f.read()))
                _logger.debug("loaded authfile: %r", d)
                return d
        except:
            return None
            
    def write_passkey(self, serial, passkey):
    
        path = os.path.join(self.config_dir, str(serial))
        utilities.makedirs_if_not_exists(path)
        utilities.makedirs_if_not_exists(os.path.join(path, "activities"))
        
        with open(os.path.join(path, "authfile"), 'wb') as f:
            passkey.tofile(f)
            _logger.debug("wrote authfile:", serial, passkey)

    def setup_channel(self, channel):
        channel.set_period(4096)
        channel.set_search_timeout(255)
        channel.set_rf_freq(50)
        channel.set_search_waveform([0x53, 0x00])
        channel.set_id(0, 0x01, 0)
        
        print "Open channel..."
        channel.open()
        #channel.request_message(Message.ID.RESPONSE_CHANNEL_STATUS)

    def on_link(self, beacon):
        print "on link"
        self.link()

    def on_authentication(self, beacon):
        print "on authentication"
        self.serial, self.name = self.authentication_serial()
        self.passkey = self.read_passkey(self.serial)
        print self.name, self.serial, self.passkey
        
        if self.passkey != None:
            self.authentication_passkey(self.passkey)
        else:
            self.passkey = self.authentication_pair(self.PRODUCT_NAME)
            self.write_passkey(self.serial, self.passkey)

    def on_transport(self, beacon):
        print "on transport"
        directory = self.download_directory()
        
        for fil in directory.get_files()[2:]:
            print " - {0}:\t{1}\t{2}\t{3}".format(fil.get_index(),
                    fil.get_type(), fil.get_size(), fil.get_date())
        
        for fil in directory.get_files()[2:]:
            self.download_file(fil)

    def download_file(self, fil):

        name = str.format("{0}-{1:02x}-{2}.fit",
                fil.get_date().strftime("%Y-%m-%d_%H-%M-%S"),
                fil.get_type(), fil.get_size())
        path = os.path.join(self.config_dir, str(self.serial),
                "activities", name)

        if os.path.exists(path):
            print "Skipping", name
        else:
            sys.stdout.write("Downloading " + name + " [")
            sys.stdout.flush()
            def callback(new_progress):
                diff = int(new_progress * 10.0) - int(callback.progress * 10.0)
                sys.stdout.write("." * diff)
                sys.stdout.flush()
                callback.progress = new_progress
            callback.progress = 0.0
            data = self.download(fil.get_index(), callback)
            with open(path, "w") as fd:
                data.tofile(fd)
            sys.stdout.write("]\n")
            sys.stdout.flush()
            
            self.scriptr.run_download(path)

def main():

    # Set up logging
    logger = logging.getLogger("garmin")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler("garmin.log", "w")
    #handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt='%(threadName)-10s %(asctime)s  %(name)-15s  %(levelname)-8s  %(message)s'))
    logger.addHandler(handler)

    try:
        g = Garmin()
        g.start()
    except (Exception, KeyboardInterrupt):
        traceback.print_exc()
        print "Interrupted"
        g.stop()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())

