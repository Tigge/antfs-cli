# Ant
#
# Copyright (c) 2016, Rhys Kidd <rhyskidd@gmail.com>
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

from __future__ import absolute_import, print_function

import unittest

from antfs_cli import utilities


class BasicUtilityTest(unittest.TestCase):
    """Test basic utility features"""

    def setUp(self):
        """Test setup of XDG"""
        self.dummy_device = "Garmin00XT"
        self.xdg_object = utilities.XDG(self.dummy_device)

    def test_data_dir(self):
        """Test if operating system-appropriate data directory is located"""
        self.assertIn(self.dummy_device, self.xdg_object.get_data_dir())

    def test_config_dir(self):
        """Test if operating system-appropriate config directory is located"""
        self.assertIn(self.dummy_device, self.xdg_object.get_config_dir())
