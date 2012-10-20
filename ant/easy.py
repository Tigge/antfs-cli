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

from base import Ant, Message

_logger = logging.getLogger("garmin.ant.easy")

class AntException(Exception):
    pass

class TransferFailedException(AntException):
    pass

class ReceiveFailedException(AntException):
    pass

class ReceiveFailException(AntException):
    pass


def wait_for_message(match, process, queue, condition):
    """
    Wait for a specific message in the *queue* guarded by the *condition*
    matching the function *match* (which is a function that takes a
    message as a parameter and returns a boolean). The messages is
    processed by the *process* function before returning it.
    """
    _logger.debug("wait for message matching %r", match)
    condition.acquire()
    for _ in range(10):
        _logger.debug("looking for matching message in %r", queue)
        #_logger.debug("wait for response to %#02x, checking", mId)
        for message in queue:
            if match(message):
                _logger.debug(" - response found %r", message)
                queue.remove(message)
                condition.release()
                return process(message)
            elif (message[1] == 1 and 
                 message[2][0] == Message.Code.EVENT_TRANSFER_TX_FAILED):
                _logger.warning("Transfer send failed:")
                _logger.warning(message)
                queue.remove(message)
                condition.release()
                raise TransferFailedException()
        _logger.debug(" - could not find response matching %r", match)
        condition.wait(1.0)
    raise AntException("Timed out while waiting for message");
    
def wait_for_event(ok_codes, queue, condition):
    def match((channel, event, data)):
        return data[0] in ok_codes
    def process((channel, event, data)):
        return (channel, event, data)
    return wait_for_message(match, process, queue, condition)

def wait_for_response(event_id, queue, condition):
    """
    Waits for a response to a specific message sent by the channel response
    message, 0x40. It's expected to return RESPONSE_NO_ERROR, 0x00.
    """
    def match((channel, event, data)):
        return event == event_id
    def process((channel, event, data)):
        if data[0] == Message.Code.RESPONSE_NO_ERROR:
            return (channel, event, data)
        else:
            raise Exception("Responded with error " + str(data[0])
                    + ":" + Message.Code.lookup(data[0]))
    return wait_for_message(match, process, queue, condition)

def wait_for_special(event_id, queue, condition):
    """
    Waits for special responses to messages such as Channel ID, ANT
    Version, etc. This does not throw any exceptions, besides timeouts.
    """
    def match((channel, event, data)):
        return event == event_id
    def process(event):
        return event
    return wait_for_message(match, process, queue, condition)



class Channel():
    
    class Type:
        BIDIRECTIONAL_RECEIVE         = 0x00
        BIDIRECTIONAL_TRANSMIT        = 0x10
        
        SHARED_BIDIRECTIONAL_RECEIVE  = 0x20
        SHARED_BIDIRECTIONAL_TRANSMIT = 0x30
        
        UNIDIRECTIONAL_RECEIVE_ONLY   = 0x40
        UNIDIRECTIONAL_TRANSMIT_ONLY  = 0x50
    
    def __init__(self, id, ant):
        self.id  = id
        self._ant = ant
        
        self._responses_cond = threading.Condition()
        self._responses      = collections.deque()
        self._event_cond     = threading.Condition()
        self._events         = collections.deque()

    def _response(self, event, data):
        _logger.warning("Response, Channel %x, %x: %s", self.id, event, str(data))
        self._responses_cond.acquire()
        self._responses.append((self.id, event, data))
        self._responses_cond.notify()
        self._responses_cond.release()
    
    def _event(self, event, data):
        _logger.warning("Event, Channel %x, %x: %s", self.id, event, str(data))
        self._event_cond.acquire()
        self._events.append((self.id, event, data))
        self._event_cond.notify()
        self._event_cond.release()

    def wait_for_event(self, ok_codes):
        return wait_for_event(ok_codes, self._events, self._event_cond)

    def wait_for_response(self, event_id):
        return wait_for_response(event_id, self._responses, self._responses_cond)

    def wait_for_special(self, event_id):
        return wait_for_special(event_id, self._responses, self._responses_cond)

    def _assign(self, channelType, networkNumber):
        self._ant.assign_channel(self.id, channelType, networkNumber)
        return self.wait_for_response(Message.ID.ASSIGN_CHANNEL)

    def _unassign():
        pass

    def open(self):
        self._ant.open_channel(self.id)
        return self.wait_for_response(Message.ID.OPEN_CHANNEL)

    def set_id(self, deviceNum, deviceType, transmissionType):
        self._ant.set_channel_id(self.id, deviceNum, deviceType, transmissionType)
        return self.wait_for_response(Message.ID.SET_CHANNEL_ID)
    
    def set_period(self, messagePeriod):
        self._ant.set_channel_period(self.id, messagePeriod)
        return self.wait_for_response(Message.ID.SET_CHANNEL_PERIOD)
    
    def set_search_timeout(self, timeout):
        self._ant.set_channel_search_timeout(self.id, timeout)
        return self.wait_for_response(Message.ID.SET_CHANNEL_SEARCH_TIMEOUT)
    
    def set_rf_freq(self, rfFreq):
        self._ant.set_channel_rf_freq(self.id, rfFreq)
        return self.wait_for_response(Message.ID.SET_CHANNEL_RF_FREQ)

    def set_search_waveform(self, waveform):
        self._ant.set_search_waveform(self.id, waveform)
        return self.wait_for_response(Message.ID.SET_SEARCH_WAVEFORM)

    def request_message(self, messageId):
        _logger.debug("requesting message %#02x", messageId)
        self._ant.request_message(self.id, messageId)
        _logger.debug("done requesting message %#02x", messageId)
        return self.wait_for_special(messageId)

    def send_acknowledged_data(self, data):
        try:
            _logger.debug("send acknowledged data %s", self.id)
            self._ant.send_acknowledged_data(self.id, data)
            self.wait_for_event([Message.Code.EVENT_TRANSFER_TX_COMPLETED])
            _logger.debug("done sending acknowledged data %s", self.id)
        except TransferFailedException:
            _logger.warning("failed to send acknowledged data %s, retrying", self.id)
            self.send_acknowledged_data(self.id, data)

    def send_burst_transfer_packet(self, channelSeq, data, first):
        _logger.debug("send burst transfer packet %s", data)
        self._ant.send_burst_transfer_packet(channelSeq, data, first)

    def send_burst_transfer(self, data):
        try:
            self._last_call = (self.send_burst_transfer, [self.id, data])
            _logger.debug("send burst transfer %s", self.id)
            Ant.send_burst_transfer(self, self.id, data)
            self.wait_for_event([Message.Code.EVENT_TRANSFER_TX_START])
            self.wait_for_event([Message.Code.EVENT_TRANSFER_TX_COMPLETED])
            _logger.debug("done sending burst transfer %s", self.id)
        except TransferFailedException:
            _logger.warning("failed to send burst transfer %s, retrying", self.id)
            self.send_burst_transfer(self.id, data)


class Node(Ant):
    
    def __init__(self, idVendor, idProduct):
        #Ant.__init__(self, idVendor, idProduct)
        
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

    def new_channel(self, type):
        channel = Channel(0, self.ant)
        self.channels[0] = channel
        print self.channels
        channel._assign(type, 0x00)
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
        #print "getevent"
        if self._event_cond.acquire(False):
            #print "ge - acquired"
            if len(self._events) == 0:
                self._event_cond.wait()
            message = self._events.popleft()
            self._event_cond.release()
            return message
        else:
            #print "ge - not acquired"
            return None

    def gofix(self):
        while True:
        
            try:
                (channel, event, data) = self.get_event()
            except TypeError:
                _logger.debug("npk")
                continue

            if event == Message.Code.EVENT_RX_BURST_PACKET:
                self.on_burst_data(data)
            elif event == Message.Code.EVENT_RX_BROADCAST:
                self.on_broadcast_data(data)
            else:
                # TODO: we should not really ignore this...
                if data[0] == Message.Code.EVENT_RX_FAIL:
                    _logger.warning("Got EVENT_RX_FAIL, continuing...")
                    continue
                _logger.warning("UNHANDLED EVENT %s, %d:%s", channel, event,
                        Message.Code.lookup(data[0]))
                _logger.warning("           DATA %s", data)
                raise Exception("Unhandled event " + str(data[0])
                        + ":" + Message.Code.lookup(data[0]))

    def on_burst_data(self, data):
        pass
    
    def on_broadcast_data(self, data):
        pass

