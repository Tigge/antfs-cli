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

from ant.base import Ant, Message
from ant.easy import EasyAnt
import ant.fs

import utilities

import logging
import threading
import time
import signal
import collections

import array
import datetime
import os
import struct
import sys
import traceback

ID_VENDOR  = 0x0fcf
ID_PRODUCT = 0x1008

PRODUCT_NAME = "garmin-extractor"

_logger = logging.getLogger("garmin")

class Garmin(EasyAnt):

    class State:
        INITIALIZING   = 0
        SEARCHING      = 1
        PAIRING        = 2
        NEWFREQUENCY   = 3
        REQUESTID      = 4
        AUTHENTICATING = 5
        FETCH          = 6
        FS             = 7

    def __init__(self):
        # Create Ant
        EasyAnt.__init__(self, ID_VENDOR, ID_PRODUCT)
        #self.start()
        
        self.state = Garmin.State.INITIALIZING
        
        self.myid     = [0xff, 0xff, 0xff, 0xff]
        self.auth     = [0xee, 0xee, 0xee, 0xee, 0xee, 0xee, 0xee, 0xee]
        self.pair     = True
        self.myfreq   = 0x19
        
        self.last     = array.array("B")
        
        self.fetch    = []
        self.fetchdat = array.array("B")
        
        _logger.debug("Creating directories")
        self.create_directories()
        self.fs       = ant.fs.Manager(self)

    def create_directories(self):
        xdg = utilities.XDG(PRODUCT_NAME)
        self.config_dir = xdg.get_config_dir()
        
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def read_authfile(self, unitid):

        path = os.path.join(self.config_dir, str(unitid))
        
        with open(os.path.join(path, "authfile"), 'rb') as f:
            d = list(struct.unpack("<4B8B", f.read()))
            self.myid = d[0:4]
            self.auth = d[4:12]
            self.pair = False
            _logger.debug("loaded authfile:")
            _logger.debug("%s, %s, %s, %s", d, self.myid, self.auth, self.pair)

    def write_authfile(self, unitid):
    
        path = os.path.join(self.config_dir, str(unitid))
        if not os.path.exists(path):
            os.mkdir(path)
        
        with open(os.path.join(path, "authfile"), 'wb') as f:
            f.write("".join(map(chr, self.myid)))
            f.write("".join(map(chr, self.auth)))
            _logger.debug("wrote authfile:")
            _logger.debug("%s, %s, %s", self.myid, self.auth, self.pair)

    def init(self):
        print "Request basic information..."
        m = self.request_message(0x00, Message.ID.RESPONSE_VERSION)
        m = self.request_message(0x00, Message.ID.RESPONSE_CAPABILITIES)
        m = self.request_message(0x00, Message.ID.RESPONSE_SERIAL_NUMBER)
        
        print "Starting system..."
        
        NETWORK_KEY= [0xa8, 0xa4, 0x23, 0xb9, 0xf5, 0x5e, 0x63, 0xc1]
        
        self.reset_system()
        self.set_network_key(0x00, NETWORK_KEY)
        self.assign_channel(0x00, 0x00, 0x00)
        self.set_channel_period(0x00, [0x00, 0x10])
        self.set_channel_search_timeout(0x00, 0xff)
        self.set_channel_rf_freq(0x00, 0x32)
        # TODO: 0x49 = Channel waveform? 
        #self.xxxxx("\xa4\x03\x49\x00\x53\x00\xbd")
        self.set_channel_id(0x00, [0x00, 0x00], 0x01, 0x00)
        
        print "Open channel..."
        self.open_channel(0x00)
        self.request_message(0x00, Message.ID.RESPONSE_CHANNEL_STATUS)

        print "Searching..."
        
        self.state = Garmin.State.SEARCHING

    def get_filename(self, f):
        file_date_time = f.get_date().strftime("%Y-%m-%d_%H-%M-%S")
        return str.format("{0}-{1:02x}-{2}.fit", file_date_time,
                          f.get_type(), f.get_size())

    def get_filepath(self, f):
        return os.path.join(self.config_dir, self.get_filename(f))

    def download_index_done(self, index):
        self._index = index
        for f in self._index._files:
            print " - {0}:\t{1}\t{2}\t{3}".format(f.get_index(), f.get_type(),
                  f.get_size(), f.get_date())
        # Skip first two files (seems special)
        self._index._files = self._index._files[2:]
        self.download_file_next()

    def download_file_next(self):
        if len(self._index._files) > 0:
            f = self._index._files.pop(0)
            if os.path.exists(self.get_filepath(f)):
                print "Skipping", self.get_filename(f)
                self.download_file_next()
            else:
                print "Downloading", self.get_filename(f),
                sys.stdout.flush()
                self.fs.download(f)
        else:
            print "Done!"
            sys.exit(0)

    def download_file_done(self, f):
        with open(self.get_filepath(f), "w") as fd:
            f.get_data().tofile(fd)
        print "- done"
        self.download_file_next()

    def on_burst_data(self, data):
        #print "burst data", self.state, data
        
        if self.state == Garmin.State.REQUESTID:
            _logger.debug("%d, %d, %s", len(data), len(data[11:]), data[11:])
            (strlen, unitid, name) = struct.unpack("<BI14s", data[11:-2])
            print "String length: ", strlen
            print "Unit ID:       ", unitid
            print "Product name:  ", name
            
            self.unitid = unitid
            
            try:
                self.read_authfile(self.unitid)
            except:
                if not self.pair:
                    raise Exception("Have no authentication data, and watch is not set for initial pairing")
            
            #TODO, pair or resume
            if self.pair:
                self.send_acknowledged_data(0x00, [0x44, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                self.request_message(0x00, Message.ID.RESPONSE_CHANNEL_STATUS)
                
                sid = map(ord, list(str(unitid)))
                
                # Identifier, sync/id?
                self.send_burst_transfer(0x00, [\
                    [0x44, 0x04, 0x02, 0x0a] + self.myid, sid[0:8], \
                    sid[8:10] + [0x00, 0x00, 0x00, 0x00, 0x00, 0x00], \
                    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]])
                
                self.state = Garmin.State.PAIRING
                
            else:
                
                self.send_burst_transfer(0x00, [\
                    [0x44, 0x04, 0x03, 0x08] + self.myid, self.auth, \
                    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]])
                    
                self.state = Garmin.State.AUTHENTICATING

        elif self.state == Garmin.State.PAIRING:
            _logger.debug("pairing is done")
            self.auth = data[16:24]
            self.write_authfile(self.unitid)
            self.state = Garmin.State.FETCH
        
        elif self.state == Garmin.State.AUTHENTICATING:
            _logger.debug("auth is done")
            self.state = Garmin.State.FETCH
        
        elif self.state == Garmin.State.FS:
            if len(data) >= 32 and data[8] == 0x44 and data[9] == 0x89:
                res = self.fs.on_data(data)
                if isinstance(res, ant.fs.Directory):
                    self.download_index_done(res)
                elif isinstance(res, ant.fs.File):
                    self.download_file_done(res)

    def on_broadcast_data(self, data):
        #print "broadcast data", self.state, data
        
        if self.last != data:
            _logger.debug("new state")
            _logger.debug(data)
        #else:
        #    return
        
        if self.state == Garmin.State.SEARCHING:
            _logger.debug("found device")
            can_pair = bool(data[1] & 0b00001000)
            new_data = bool(data[1] & 0b00100000)
            _logger.debug("pair %s, data %s", can_pair, new_data)

            self.request_message(0x00, Message.ID.RESPONSE_CHANNEL_ID)
            self.send_acknowledged_data(0x00, [0x44, 0x02, self.myfreq, 0x04] + self.myid)
            
            _logger.debug("\tNew period, search, rf req")
            # New period, search timeout
            self.set_channel_period(0x00, [0x00, 0x10])
            self.set_channel_search_timeout(0x00, 0x03)
            self.set_channel_rf_freq(0x00, self.myfreq)
            
            self.state = Garmin.State.NEWFREQUENCY
        
        elif self.state == Garmin.State.NEWFREQUENCY:
            _logger.debug("talking on new frequency")
            self.send_acknowledged_data(0x00, [0x44, 0x04, 0x01, 0x00] + self.myid)
            
            self.state = Garmin.State.REQUESTID
        
        elif self.state == Garmin.State.FETCH and len(self.fetch) == 0:
            self.send_burst_transfer(0x00, [\
                [0x44, 0x0a, 0xfe, 0xff, 0x10, 0x00, 0x00, 0x00], \
                [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]])
            print "Downloading index..."
            self.fs.download_index()
            #self.send_burst_transfer(0x00, [\
            #    [0x44, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], \
            #    [0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]])
            self.state = Garmin.State.FS
        self.last = data


    def gogo(self):
        
        try:
            self.init()
            self.gofix()
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            print e, type(e)
            traceback.print_stack()
            traceback.print_exc()
        finally:
            self.stop()
            sys.exit()


def main():

    # Set up logging
    logger = logging.getLogger("garmin")
    logger.setLevel(logging.ERROR)
    handler = logging.FileHandler("garmin.log", "w")
    #handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt='%(asctime)s  %(name)-15s  %(levelname)-8s  %(message)s'))
    logger.addHandler(handler)

    g = Garmin()
    g.gogo()



if __name__ == "__main__":
    sys.exit(main())


