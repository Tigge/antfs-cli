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

class EasyAnt(Ant):
    
    def __init__(self, idVendor, idProduct):
        Ant.__init__(self, idVendor, idProduct)
        
        self._responses_cond = threading.Condition()
        self._responses      = collections.deque()
        self._event_cond     = threading.Condition()
        self._events         = collections.deque()
        
        self.start()

    def response_function(self, channel, event, data):
        self._responses_cond.acquire()
        self._responses.append((channel, event, data))
        self._responses_cond.notify()
        self._responses_cond.release()
    
    def channel_event_function(self, channel, event, data):
        #_logger.debug("channel event function %r", message)
        self._event_cond.acquire()
        self._events.append((channel, event, data))
        self._event_cond.notify()
        self._event_cond.release()

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

    def _wait_for_message(self, match, process, queue, condition):
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
        
    def wait_for_event(self, ok_codes):
        def match((channel, event, data)):
            return data[0] in ok_codes
        def process((channel, event, data)):
            return (channel, event, data)
        return self._wait_for_message(match, process, self._events,
               self._event_cond)

    def wait_for_response(self, event_id):
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
        return self._wait_for_message(match, process, self._responses,
               self._responses_cond)

    def wait_for_special(self, event_id):
        """
        Waits for special responses to messages such as Channel ID, ANT
        Version, etc. This does not throw any exceptions, besides timeouts.
        """
        def match((channel, event, data)):
            return event == event_id
        def process(event):
            return event
        return self._wait_for_message(match, process, self._responses,
               self._responses_cond)

    def request_message(self, channel, messageId):
        _logger.debug("requesting message %#02x", messageId)
        Ant.request_message(self, channel, messageId)
        _logger.debug("done requesting message %#02x", messageId)
        return self.wait_for_special(messageId)

    def reset_system(self):
        Ant.reset_system(self)
        return self.wait_for_special(Message.ID.STARTUP_MESSAGE)

    def assign_channel(self, channel, channelType, networkNumber):
        Ant.assign_channel(self, channel, channelType, networkNumber)
        return self.wait_for_response(Message.ID.ASSIGN_CHANNEL)
    
    def open_channel(self, channel):
        Ant.open_channel(self, channel)
        return self.wait_for_response(Message.ID.OPEN_CHANNEL)
    
    def set_channel_id(self, channel, deviceNum, deviceType, transmissionType):
        Ant.set_channel_id(self, channel, deviceNum, deviceType, transmissionType)
        return self.wait_for_response(Message.ID.SET_CHANNEL_ID)
    
    def set_channel_period(self, channel, messagePeriod):
        Ant.set_channel_period(self, channel, messagePeriod)
        return self.wait_for_response(Message.ID.SET_CHANNEL_PERIOD)
    
    def set_channel_search_timeout(self, channel, timeout):
        Ant.set_channel_search_timeout(self, channel, timeout)
        return self.wait_for_response(Message.ID.SET_CHANNEL_SEARCH_TIMEOUT)
    
    def set_channel_rf_freq(self, channel, rfFreq):
        Ant.set_channel_rf_freq(self, channel, rfFreq)
        return self.wait_for_response(Message.ID.SET_CHANNEL_RF_FREQ)
    
    def set_network_key(self, network, key):
        Ant.set_network_key(self, network, key)
        return self.wait_for_response(Message.ID.SET_NETWORK_KEY)

    def set_search_waveform(self, channel, waveform):
        Ant.set_search_waveform(self, channel, waveform)
        return self.wait_for_response(Message.ID.SET_SEARCH_WAVEFORM)

    def send_acknowledged_data(self, channel, data):
        try:
            _logger.debug("send acknowledged data %s", channel)
            Ant.send_acknowledged_data(self, channel, data)
            self.wait_for_event([Message.Code.EVENT_TRANSFER_TX_COMPLETED])
            _logger.debug("done sending acknowledged data %s", channel)
        except TransferFailedException:
            _logger.warning("failed to send acknowledged data %s, retrying", channel)
            self.send_acknowledged_data(channel, data)

    def send_burst_transfer_packet(self, channelSeq, data, first):
        _logger.debug("send burst transfer packet %s", data)
        Ant.send_burst_transfer_packet(self, channelSeq, data, first)


    def send_burst_transfer(self, channel, data):
        try:
            self._last_call = (self.send_burst_transfer, [channel, data])
            _logger.debug("send burst transfer %s", channel)
            Ant.send_burst_transfer(self, channel, data)
            self.wait_for_event([Message.Code.EVENT_TRANSFER_TX_START])
            self.wait_for_event([Message.Code.EVENT_TRANSFER_TX_COMPLETED])
            _logger.debug("done sending burst transfer %s", channel)
        except TransferFailedException:
            _logger.warning("failed to send burst transfer %s, retrying", channel)
            self.send_burst_transfer(channel, data)

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
