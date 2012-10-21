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
import Queue

from ant.base.ant import Ant
from ant.base.message import Message
from ant.easy.channel import Channel
from ant.easy.filter import wait_for_event, wait_for_response, wait_for_special

_logger = logging.getLogger("garmin.ant.easy.node")

class Node():
    
    def __init__(self, idVendor, idProduct):
        
        self._responses_cond = threading.Condition()
        self._responses      = collections.deque()
        self._event_cond     = threading.Condition()
        self._events         = collections.deque()
        
        self._datas = Queue.Queue()
        
        self.channels = {}
        
        self.ant = Ant(idVendor, idProduct)
        
        self._running = True
        
        self._worker_thread = threading.Thread(target=self._worker, name="ant.easy")
        self._worker_thread.start()

    def new_channel(self, ctype):
        channel = Channel(0, self, self.ant)
        self.channels[0] = channel
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

    def _worker_response(self, channel, event, data):
        self._responses_cond.acquire()
        self._responses.append((channel, event, data))
        self._responses_cond.notify()
        self._responses_cond.release()

    def _worker_event(self, channel, event, data):
        if event == Message.Code.EVENT_RX_BURST_PACKET:
            self._datas.put(('burst', channel, data))
        elif event == Message.Code.EVENT_RX_BROADCAST:
            self._datas.put(('broadcast', channel, data))
        else:
            self._event_cond.acquire()
            self._events.append((channel, event, data))
            self._event_cond.notify()
            self._event_cond.release()

    def _worker(self):
        self.ant.response_function = self._worker_response
        self.ant.channel_event_function = self._worker_event
        
        # TODO: check capabilities
        self.ant.start()
        
    def _main(self):
        while self._running:
            try:
                (data_type, channel, data) = self._datas.get(True, 1.0)
                self._datas.task_done()
                
                if data_type == 'broadcast':
                    self.channels[channel].on_broadcast_data(data)
                elif data_type == 'burst':
                    self.channels[channel].on_burst_data(data)
                else:
                    _logger.warning("Unknown data type '%s': %r", data_type, data)
            except Queue.Empty as e:
                pass

    def start(self):
        self._main()

    def stop(self):
        if self._running:
            _logger.debug("Stoping ant.easy")
            self._running = False
            self.ant.stop()
            self._worker_thread.join()


