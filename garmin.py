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
from ant.fs.manager import Application, AntFSAuthenticationException

import utilities
import scripting

import array
import logging
import datetime
import time
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
                d = array.array('B', f.read())
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
            _logger.debug("wrote authfile: %r, %r", serial, passkey)

    def setup_channel(self, channel):
        channel.set_period(4096)
        channel.set_search_timeout(255)
        channel.set_rf_freq(50)
        channel.set_search_waveform([0x53, 0x00])
        channel.set_id(0, 0x01, 0)
        
        channel.open()
        #channel.request_message(Message.ID.RESPONSE_CHANNEL_STATUS)
        print "Searching..."

    def on_link(self, beacon):
        _logger.debug("on link, %r, %r", beacon.get_serial(),
                      beacon.get_descriptor())
        self.link()
        return True

    def on_authentication(self, beacon):
        _logger.debug("on authentication")
        self.serial, self.name = self.authentication_serial()
        self.passkey = self.read_passkey(self.serial)
        print "Authenticating with", self.name, "(" + str(self.serial) + ")"
        _logger.debug("serial %s, %r, %r", self.name, self.serial, self.passkey)
        
        if self.passkey != None:
            try:
                print " - Passkey:",
                self.authentication_passkey(self.passkey)
                print "OK"
                return True
            except AntFSAuthenticationException as e:
                print "FAILED"
                return False
        else:
            try:
                print " - Pairing:",
                self.passkey = self.authentication_pair(self.PRODUCT_NAME)
                self.write_passkey(self.serial, self.passkey)
                print "OK"
                return True
            except AntFSAuthenticationException as e:
                print "FAILED"
                return False

    def on_transport(self, beacon):

        directory = self.download_directory()
        
        local_files  = os.listdir(os.path.join(self.config_dir,
                str(self.serial), "activities"))
        remote_files = directory.get_files()[2:]

        downloading = filter(lambda fil: self.get_filename(fil)
                             not in local_files, remote_files)
        uploading   = filter(lambda name: name not in map(self.get_filename,
                             remote_files), local_files)

        print "Downloading", len(downloading), "file(s)"
        # TODO "and uploading", len(uploading), "file(s)"

        # Download missing files:
        for fil in downloading:
            self.download_file(fil)
        
        # Upload missing files:
        for fil in uploading:
            # TODO
            pass


    def get_filename(self, fil):
        return str.format("{0}-{1:02x}-{2}.fit",
                fil.get_date().strftime("%Y-%m-%d_%H-%M-%S"),
                fil.get_type(), fil.get_size())

    def get_filepath(self, fil):
        return os.path.join(self.config_dir, str(self.serial),
                "activities", self.get_filename(fil))


    def download_file(self, fil):

        sys.stdout.write("Downloading {0}: ".format(self.get_filename(fil)))
        sys.stdout.flush()
        def callback(new_progress):
            delta = time.time() - callback.start_time
            eta = datetime.timedelta(seconds=int(delta / new_progress - delta))
            s = "[{0:<30}] ETA: {1}".format("." * int(new_progress * 30), eta)
            sys.stdout.write(s)
            sys.stdout.flush()
            sys.stdout.write("\b" * len(s))
        callback.start_time = time.time()
        data = self.download(fil.get_index(), callback)
        with open(self.get_filepath(fil), "w") as fd:
            data.tofile(fd)
        sys.stdout.write("\n")
        sys.stdout.flush()
        
        self.scriptr.run_download(self.get_filepath(fil))


def main():
    
    # Find out what time it is
    # used for logging filename.
    currentTime = time.strftime("%Y%m%d-%H%M%S")

    # Set up logging
    logger = logging.getLogger("garmin")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(currentTime + "-garmin.log", "w")
    #handler = logging.StreamHandler()

    # If you add new module/logger name longer than the 15 characters just increase the value after %(name).
    # The longest module/logger name now is "garmin.ant.base" and "garmin.ant.easy".
    handler.setFormatter(logging.Formatter(fmt='%(threadName)-10s %(asctime)s  %(name)-15s  %(levelname)-8s  %(message)s (%(filename)s:%(lineno)d)'))

    logger.addHandler(handler)

    try:
        g = Garmin()
        try:
            g.start()
        except:
            g.stop()
            raise
    except (Exception, KeyboardInterrupt):
        traceback.print_exc()
        print "Interrupted"
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())

