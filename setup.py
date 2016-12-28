#!/usr/bin/env python
#
# antfs-cli distutils setup script
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

from __future__ import absolute_import, print_function

from setuptools import setup

try:
    with open('README.md') as file:
        long_description = file.read()
except IOError:
    long_description = ''

setup(name='antfs-cli',
      version='0.3',

      description='ANT-FS Command Line Interface',
      long_description=long_description,

      author='Gustav Tiger',
      author_email='gustav@tiger.name',

      packages=['antfs_cli'],
      entry_points={
          'console_scripts': ['antfs-cli=antfs_cli.program:main']
      },

      url='https://github.com/Tigge/antfs-cli',

      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Intended Audience :: End Users/Desktop',
                   'Intended Audience :: Healthcare Industry',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5'],

      dependency_links=['git+https://github.com/Tigge/openant.git#egg=openant-0.3'],
      install_requires=['openant>=0.3'],
      extras_require={
          'upload': ['garmin-uploader'],
      },

      test_suite='tests')
