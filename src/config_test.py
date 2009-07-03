#!/usr/bin/env python
"""\
@file config_test.py
@brief Test the config module

$LicenseInfo:firstyear=2009&license=mit$

Copyright (c) 2009, Linden Research, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
$/LicenseInfo$
"""

import os
import tempfile
import unittest

import config

class ConfigInstanceTester(unittest.TestCase):
    def setUp(self):
        self._file = tempfile.NamedTemporaryFile()
        self._config = config.Config(self._file.name)

    def tearDown(self):
        pass

    def testSetAndGet(self):
        self._config['key'] = 'value'
        self.assertEquals('value', self._config['key'])
        self._config.set('key2', 'value2')
        self.assertEquals('value2', self._config.get('key2'))


if __name__ == '__main__':
    unittest.main()
