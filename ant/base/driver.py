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

_logger = logging.getLogger("garmin.ant.base.driver")

class DriverException(Exception):
    pass

class DriverNotFound(DriverException):
    pass

class DriverTimeoutException(DriverException):
    pass

class Driver:
    
    @classmethod
    def find(cls):
        pass
    
    def open(self):
        pass
    
    def close(self):
        pass

    def read(self):
        pass
    
    def write(self, data):
        pass

drivers = []

try:
    import array
    import os
    import os.path

    import serial

    class SerialDriver(Driver):

        ID_VENDOR  = 0x0fcf
        ID_PRODUCT = 0x1004

        @classmethod
        def find(cls):
            return cls.get_url() != None
        
        @classmethod
        def get_url(cls):
            try:
                path = '/sys/bus/usb-serial/devices'
                for device in os.listdir(path):
                    try:
                        device_path = os.path.realpath(os.path.join(path, device))
                        device_path = os.path.join(device_path, "../../")
                        ven = int(open(os.path.join(device_path, 'idVendor')).read().strip(), 16)
                        pro = int(open(os.path.join(device_path, 'idProduct')).read().strip(), 16)
                        if ven == cls.ID_VENDOR or cls.ID_PRODUCT == pro:
                            return os.path.join("/dev", device)
                    except:
                        continue
                return None
            except OSError:
                return None
        
        def open(self):
            
            # TODO find correct port on our own, could be done with
            #      serial.tools.list_ports, but that seems to have some
            #      problems at the moment.
            
            try:
                self._serial = serial.serial_for_url(self.get_url(), 115200)
            except serial.SerialException as e:
                raise DriverException(e)
            
            print "Serial information:"
            print "name:            ", self._serial.name
            print "port:            ", self._serial.port
            print "baudrate:        ", self._serial.baudrate
            print "bytesize:        ", self._serial.bytesize
            print "parity:          ", self._serial.parity
            print "stopbits:        ", self._serial.stopbits
            print "timeout:         ", self._serial.timeout
            print "writeTimeout:    ", self._serial.writeTimeout
            print "xonxoff:         ", self._serial.xonxoff
            print "rtscts:          ", self._serial.rtscts
            print "dsrdtr:          ", self._serial.dsrdtr
            print "interCharTimeout:", self._serial.interCharTimeout

            self._serial.timeout = 0
        
        def read(self):
            data = self._serial.read(4096)
            #print "serial read", len(data), type(data), data
            return array.array('B', data)

        def write(self, data):
            try:
                #print "serial write", type(data), data
                self._serial.write(data)
            except serial.SerialTimeoutException as e:
                raise DriverTimeoutException(e)

        def close(self):
            self._serial.close()

    drivers.append(SerialDriver)
    
except ImportError:
    pass


try:
    import usb.core
    import usb.util

    class USBDriver(Driver):

        def __init__(self):
            pass

        @classmethod
        def find(cls):
            return usb.core.find(idVendor=cls.ID_VENDOR, idProduct=cls.ID_PRODUCT) != None

        def open(self):
            # Find USB device
            _logger.debug("USB Find device, vendor %#04x, product %#04x", self.ID_VENDOR, self.ID_PRODUCT)
            dev = usb.core.find(idVendor=self.ID_VENDOR, idProduct=self.ID_PRODUCT)

            # was it found?
            if dev is None:
                raise ValueError('Device not found')

            _logger.debug("USB Config values:")
            for cfg in dev:
                _logger.debug(" Config %s", cfg.bConfigurationValue)
                for intf in cfg:
                    _logger.debug("  Interface %s, Alt %s", str(intf.bInterfaceNumber), str(intf.bAlternateSetting))
                    for ep in intf:
                        _logger.debug("   Endpoint %s", str(ep.bEndpointAddress))

            # unmount a kernel driver (TODO: should probably reattach later)
            if dev.is_kernel_driver_active(0):
                _logger.debug("A kernel driver active, detatching")
                dev.detach_kernel_driver(0)
            else:
                _logger.debug("No kernel driver active")

            # set the active configuration. With no arguments, the first
            # configuration will be the active one
            dev.set_configuration()
            dev.reset()
            #dev.set_configuration()

            # get an endpoint instance
            cfg = dev.get_active_configuration()
            interface_number = cfg[(0,0)].bInterfaceNumber
            alternate_setting = usb.control.get_interface(dev, interface_number)
            intf = usb.util.find_descriptor(
                cfg, bInterfaceNumber = interface_number,
                bAlternateSetting = alternate_setting
            )

            self._out = usb.util.find_descriptor(
                intf,
                # match the first OUT endpoint
                custom_match = \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_OUT
            )

            _logger.debug("UBS Endpoint out: %s, %s", self._out, self._out.bEndpointAddress)

            self._in = usb.util.find_descriptor(
                intf,
                # match the first OUT endpoint
                custom_match = \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_IN
            )

            _logger.debug("UBS Endpoint in: %s, %s", self._in, self._in.bEndpointAddress)

            assert self._out is not None and self._in is not None
        
        def close(self):
            pass
        
        def read(self):
            return self._in.read(4096)
        
        def write(self, data):
            self._out.write(data)

    class USB2Driver(USBDriver):
        ID_VENDOR  = 0x0fcf
        ID_PRODUCT = 0x1008

    class USB3Driver(USBDriver):
        ID_VENDOR  = 0x0fcf
        ID_PRODUCT = 0x1009

    drivers.append(USB2Driver)
    drivers.append(USB3Driver)

except ImportError:
    pass

def find_driver():
    
    print "Driver available:", drivers
    
    for driver in drivers:
        if driver.find():
            print " - Using:", driver
            return driver()
    raise DriverNotFound

