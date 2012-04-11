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

class Garmin(EasyAnt):

    class State:
        INITIALIZING   = 0
        SEARCHING      = 1
        PAIRING        = 2
        NEWFREQUENCY   = 3
        REQUESTID      = 4
        AUTHENTICATING = 5
        FETCH          = 6

    def __init__(self):
        # Create Ant
        EasyAnt.__init__(self, ID_VENDOR, ID_PRODUCT)
        #self.start()
        
        self._logger = logging.getLogger("garmin")
        
        self.state = Garmin.State.INITIALIZING
        
        self.myid     = [0xff, 0xff, 0xff, 0xff]
        self.auth     = [0xee, 0xee, 0xee, 0xee, 0xee, 0xee, 0xee, 0xee]
        self.pair     = True
        self.myfreq   = 0x19
        
        self.last     = array.array("B")
        
        self.fetch    = []
        self.fetchdat = array.array("B")
        
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
            self._logger.debug("loaded authfile:")
            self._logger.debug("%s, %s, %s, %s", d, self.myid, self.auth, self.pair)

    def write_authfile(self, unitid):
    
        path = os.path.join(self.config_dir, str(unitid))
        if not os.path.exists(path):
            os.mkdir(path)
        
        with open(os.path.join(path, "authfile"), 'wb') as f:
            f.write("".join(map(chr, self.myid)))
            f.write("".join(map(chr, self.auth)))
            self._logger.debug("wrote authfile:")
            self._logger.debug("%s, %s, %s", self.myid, self.auth, self.pair)

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

    def ant_fs_next(self, filedat):
        self._logger.debug("ant fs next")
        if len(self.fetch) == 0:
            return
        
        (fno, ftype, flags, size, date_mod) = filedat

        self.send_burst_transfer(0x00, [\
            [0x44, 0x09,  fno, 0x00, 0x00, 0x00, 0x00, 0x00], \
            [0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]])
        self._logger.debug("ant fs next request sent")

    def ant_fs_continute(self, filedat, cont_from, extra):

        (fno, ftype, flags, size, date_mod) = filedat
        cfrom = list(map(ord, struct.pack("<I", cont_from)))
        self._logger.debug("ant fs continue %s, %s, %s", filedat, cont_from, cfrom)
        
        self.send_burst_transfer(0x00, [\
            [0x44, 0x09,  fno, 0x00] + cfrom, \
            [0x00, 0x00] + list(extra) +  [0x00, 0x00, 0x00, 0x00]])
        self._logger.debug("ant fs continue request sent")

    def ant_fs_done(self, filedat, filecontent, totsize):
        self._logger.debug("ant fs file is done")
        (fno, ftype, flags, size, date_mod) = filedat
        self._logger.debug("got %s, want %s", totsize, size)
        
        file_date_time = date_mod.strftime("%Y-%m-%d_%H-%M-%S")
        
        filename = str.format("{}-{:02x}-{}-{}-{}.fit", fno, ftype, file_date_time, size, totsize)
        with open(filename, "w") as f:
            filecontent.tofile(f)
        print "Done downloading", filename

    def got_ant_fs(self, data):
        self._logger.debug("ant fs data")
        if len(self.fetch) == 0:
            self._logger.debug("Got ANT-FS packet")
            (version, length, date1, date2) = \
                struct.unpack("<BBxxxxxxII", data[24:40])
            self._logger.debug("ver %s, length %s, date1 %s, date2 %s", version, length, date1, date2)
            for i in range(40+16+16 , len(data) - 8, 16):
                (fno, ftype, fsub, flags, size, mod) = \
                    struct.unpack("<HBBxxxBII", data[i:i+16])
                date_mod = datetime.datetime.fromtimestamp(mod + 631065600)
                print fno, "\t", ftype, "\t", flags, "\t", size, "\t", date_mod
                self.fetch.append((fno, ftype, flags, size, date_mod))
            
            self.ant_fs_next(self.fetch[0])
            
        else:
            header = data[0:24]
            rdata  = data[24:-8]
            end    = data[-8:]
            self.fetchdat.extend(rdata)
            
            self._logger.debug("actual length %d, given length %d", len(self.fetchdat), self.fetch[0][3])
            (pack_length, sent_length, tot_length) = struct.unpack("<12xIII", header)
            self._logger.debug("header %d, %d, %d ,%d", len(header), pack_length, sent_length, tot_length)
            #print header
            #print rdata
            #print end
            #print "tot:"
            #print self.fetchdat
            
            
            if(sent_length + pack_length == tot_length):
                # File done
                
                self._logger.debug("File done")
                self._logger.debug("%s, %d", self.fetch[0], len(self.fetchdat))
                self._logger.debug("%s",  self.fetchdat)
                
                self.ant_fs_done(self.fetch[0], self.fetchdat, tot_length)
                
                # reset
                self.fetch.pop(0)
                self.fetchdat = array.array("B")
                
                self.ant_fs_next(self.fetch[0])
                
            else:
                 self.ant_fs_continute(self.fetch[0], pack_length + sent_length, end[-2:])

    def on_burst_data(self, data):
        #print "burst data", self.state, data
        
        if self.state == Garmin.State.REQUESTID:
            self._logger.debug("%d, %d, %s", len(data), len(data[11:]), data[11:])
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
            self._logger.debug("pairing is done")
            self.auth = data[16:24]
            self.write_authfile(self.unitid)
            self.state = Garmin.State.FETCH
        
        elif self.state == Garmin.State.AUTHENTICATING:
            self._logger.debug("auth is done")
            self.state = Garmin.State.FETCH
        
        elif self.state == Garmin.State.FETCH:
            
            if len(data) > 40 and data[8] == 0x44 and data[9] == 0x89:
            
                self.got_ant_fs(data)
    

    def on_broadcast_data(self, data):
        #print "broadcast data", self.state, data
        
        if self.last != data:
            self._logger.debug("new state")
            self._logger.debug(data)
        #else:
        #    return
        
        if self.state == Garmin.State.SEARCHING:
            self._logger.debug("found device")
            can_pair = bool(data[1] & 0b00001000)
            new_data = bool(data[1] & 0b00100000)
            self._logger.debug("pair %s, data %s", can_pair, new_data)

            self.request_message(0x00, Message.ID.RESPONSE_CHANNEL_ID)
            self.send_acknowledged_data(0x00, [0x44, 0x02, self.myfreq, 0x04] + self.myid)
            
            self._logger.debug("\tNew period, search, rf req")
            # New period, search timeout
            self.set_channel_period(0x00, [0x00, 0x10])
            self.set_channel_search_timeout(0x00, 0x03)
            self.set_channel_rf_freq(0x00, self.myfreq)
            
            self.state = Garmin.State.NEWFREQUENCY
        
        elif self.state == Garmin.State.NEWFREQUENCY:
            self._logger.debug("talking on new frequency")
            self.send_acknowledged_data(0x00, [0x44, 0x04, 0x01, 0x00] + self.myid)
            
            self.state = Garmin.State.REQUESTID
        
        elif self.state == Garmin.State.FETCH and len(self.fetch) == 0:
            self.send_burst_transfer(0x00, [\
                [0x44, 0x0a, 0xfe, 0xff, 0x10, 0x00, 0x00, 0x00], \
                [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]])
        
            self.send_burst_transfer(0x00, [\
                [0x44, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], \
                [0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]])

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
                
            print "was killed"
            self._running = False
            self.join()
            
            sys.exit()
        


def main():

    # Set up logging
    logger = logging.getLogger("garmin")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler("garmin.log", "w")
    #handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(name)-12s: %(levelname)-8s - %(message)s'))
    logger.addHandler(handler)

    g = Garmin()
    g.gogo()



if __name__ == "__main__":
    sys.exit(main())


