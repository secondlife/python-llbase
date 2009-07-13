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

from llbase import config
from llbase import llsd

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

    def testUpdate(self):
        self._config['k1'] = 'v1'
        self._config['k2'] = 'v2'
        new = {'k1': 'new_value', 'k3':'v3'}
        self._config.update(new)
        self.assertEquals('new_value', self._config.get('k1'))
        self.assertEquals('v2', self._config.get('k2'))
        self.assertEquals('v3', self._config.get('k3'))

class ConfigInstanceFileTester(unittest.TestCase):
    def setUp(self):
        # not worried about race conditions, this is just some unit tests.
        self.filename = tempfile.mktemp()
        self.conf = {'k1':'v1', 'k2':'v2'}

    def tearDown(self):
        os.remove(self.filename)

    def assertConfig(self):
        self.assertEquals('v1', config.get('k1'))
        self.assertEquals('v2', config.get('k2'))

    def testXML(self):
        conffile = open(self.filename, 'wb')
        conffile.write(llsd.format_xml(self.conf))
        conffile.close()
        config.load(self.filename)
        self.assertConfig()

if __name__ == '__main__':
    unittest.main()
