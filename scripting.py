# Utilities
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

import errno
import os
import subprocess
import threading

class Runner:

    def __init__(self, directory):
        self.directory = directory
        
        # TODO: loop over scripts, check if they are runnable, warn
        #       then don't warn at runtime.


    def get_scripts(self):
        scripts = []
        for _, _, filenames in os.walk(self.directory):
            for filename in filenames:
                scripts.append(filename)
        return sorted(scripts)

    def _run_action(self, action, filename, fit_type):
        for script in self.get_scripts():
            try:
                subprocess.call([os.path.join(self.directory, script),
                                 action, filename, str(fit_type)])
            except OSError as e:
                print " - Could not run", script, "-",\
                      errno.errorcode[e.errno], os.strerror(e.errno)

    def run_action(self, action, filename, fit_type):
        t = threading.Thread(target=self._run_action, args=(action, filename, fit_type))
        t.start()

    def run_download(self, filename, fit_type):
        self.run_action("DOWNLOAD", filename, fit_type)

    def run_upload(self, filename, fit_type):
        self.run_action("UPLOAD", filename, fit_type)

    def run_delete(self, filename, fit_type):
        self.run_action("DELETE", filename, fit_type)

