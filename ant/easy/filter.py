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

import logging

from ant.base.message import Message
from ant.easy.exception import AntException, TransferFailedException

_logger = logging.getLogger("garmin.ant.easy.filter")

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
    condition.release()
    raise AntException("Timed out while waiting for message")
    
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
