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

import collections
import threading
import logging

from ..base import Ant, Message
from ant.easy.channel import Channel
from ant.easy.filter import wait_for_event, wait_for_response, wait_for_special

_logger = logging.getLogger("garmin.ant.easy.node")

class Node(threading.Thread):
    
    def __init__(self, idVendor, idProduct):
        
        threading.Thread.__init__(self)
        
        self._responses_cond = threading.Condition()
        self._responses      = collections.deque()
        self._event_cond     = threading.Condition()
        self._events         = collections.deque()
        
        self.channels = {}
        
        self.ant = Ant(idVendor, idProduct)
        
        def response_function(channel, event, data):
            _logger.debug("response function %r", (channel, event, data))
            if channel != None and event != Message.ID.RESET_SYSTEM and event != Message.ID.SET_NETWORK_KEY:
                print self.channels
                self.channels[channel]._response(event, data)
            else:
                self._responses_cond.acquire()
                self._responses.append((channel, event, data))
                self._responses_cond.notify()
                self._responses_cond.release()
        self.ant.response_function = response_function
        
        def channel_event_function(channel, event, data):
            _logger.debug("channel event function %r", (channel, event, data))
            if channel != None:
                print self.channels
                self.channels[channel]._response(event, data)
            else:
                self._event_cond.acquire()
                self._events.append((channel, event, data))
                self._event_cond.notify()
                self._event_cond.release()

        self.ant.channel_event_function = channel_event_function
        
        self.ant.start()
        
        # TODO: check capabilities

    def new_channel(self, ctype):
        channel = Channel(0, self.ant)
        print "New channel: " + str(channel)
        self.channels[0] = channel
        print "Channel list: " + str(self.channels)
        channel._assign(ctype, 0x00)
        return channel

    def request_message(self, messageId):
        _logger.debug("requesting message %#02x", messageId)
        self.ant.request_message(0, messageId)
        _logger.debug("done requesting message %#02x", messageId)
        return self.wait_for_special(messageId)

    def reset_system(self):
        self.ant.reset_system()
        return self.wait_for_special(Message.ID.STARTUP_MESSAGE)

    def set_network_key(self, network, key):
        self.ant.set_network_key(network, key)
        return self.wait_for_response(Message.ID.SET_NETWORK_KEY)

    def wait_for_event(self, ok_codes):
        return wait_for_event(ok_codes, self._events, self._event_cond)

    def wait_for_response(self, event_id):
        return wait_for_response(event_id, self._responses, self._responses_cond)

    def wait_for_special(self, event_id):
        return wait_for_special(event_id, self._responses, self._responses_cond)

    def get_event(self):
        print "getevent"
        if self._event_cond.acquire(False):
            print "ge - acquired"
            if len(self._events) == 0:
                print "ge - waiting"
                self._event_cond.wait()
            print "ge - popping"
            message = self._events.popleft()
            print "ge - releasing"
            self._event_cond.release()
            return message
        else:
            print "ge - not acquired"
            return None

    def run(self):
        pass
#        while True:
#        
#            try:
#                (channel, event, data) = self.get_event()
#            except TypeError:
#                _logger.debug("npk")
#                continue
#            print "gofix", channel, event, data
#            if event == Message.Code.EVENT_RX_BURST_PACKET:
#                self.on_burst_data(data)
#            elif event == Message.Code.EVENT_RX_BROADCAST:
#                self.on_broadcast_data(data)
#            else:
#                # TODO: we should not really ignore this...
#                if data[0] == Message.Code.EVENT_RX_FAIL:
#                    _logger.warning("Got EVENT_RX_FAIL, continuing...")
#                    continue
#                _logger.warning("UNHANDLED EVENT %s, %d:%s", channel, event,
#                        Message.Code.lookup(data[0]))
#                _logger.warning("           DATA %s", data)
#                raise Exception("Unhandled event " + str(data[0])
#                        + ":" + Message.Code.lookup(data[0]))

    def on_burst_data(self, data):
        pass
    
    def on_broadcast_data(self, data):
        pass

