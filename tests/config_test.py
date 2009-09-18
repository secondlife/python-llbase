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

import mock
import os
import tempfile
import time
import unittest

from StringIO import StringIO

from llbase import config
from llbase import llsd

class ConfigInstanceTester(unittest.TestCase):
    def setUp(self):
        # use tempfile.mktemp() since it works across platforms and
        # python versions for our needs
        self._filename = tempfile.mktemp()
        fd = open(self._filename, "w")
        fd.close()
        self._config = config.Config(self._filename)

        # this would be preferred though cannot be used until python
        # 2.6 so that we can use the delete=False parameter on
        # initialization.
        #self._file = tempfile.NamedTemporaryFile()
        #self._config = config.Config(self._file.name)

    def tearDown(self):
        pass

    def test_set_get(self):
        self._config['key'] = 'value'
        self.assertEquals('value', self._config['key'])
        self._config.set('key2', 'value2')
        self.assertEquals('value2', self._config.get('key2'))

    def setup_update(self):
        self._config['k1'] = 'v1'
        self._config['k2'] = 'v2'

    def update_assert(self):
        self.assertEquals('new_value', self._config.get('k1'))
        self.assertEquals('v2', self._config.get('k2'))
        self.assertEquals('v3', self._config.get('k3'))

    def test_update_dict(self):
        self.setup_update()
        new = {'k1': 'new_value', 'k3':'v3'}
        self._config.update(new)
        self.update_assert()

    def test_update_filename(self):
        self.setup_update()
        # not worried about race conditions, this is just some unit tests.
        filename = tempfile.mktemp()
        new = {'k1': 'new_value', 'k3':'v3'}
        open(filename, 'wb').write(llsd.format_xml(new))
        self._config.update(filename)
        self.update_assert()
        os.remove(filename)

    def test_update_filelike(self):
        self.setup_update()
        new = {'k1': 'new_value', 'k3':'v3'}
        filelike = StringIO(llsd.format_xml(new))
        self._config.update(filelike)
        self.update_assert()
        

class ConfigInstanceFileTester(unittest.TestCase):
    def setUp(self):
        # not worried about race conditions, this is just some unit tests.
        self.filename = tempfile.mktemp()
        initial_config = {'k1':'v1', 'k2':'v2'}
        self.write_conf(initial_config)
        self.conf = config.Config(self.filename)

    def tearDown(self):
        os.remove(self.filename)

    def write_conf(self, payload):
        conffile = open(self.filename, 'wb')
        conffile.write(llsd.format_xml(payload))
        conffile.close()

    def test_file(self):
        self.assertEquals('v1', self.conf.get('k1'))
        self.assertEquals('v2', self.conf.get('k2'))

    def test_reload(self):
        self.assertEquals('v1', self.conf.get('k1'))
        self.assertEquals('v2', self.conf.get('k2'))

        now = time.time()

        new_conf = {'k1':'new value', 'k2':'v2'}
        self.write_conf(new_conf)
        self.conf._last_mod_time
        os.utime(self.filename, (now + 10, now + 10))

        mock_time = mock.Mock(return_value=now+60) # 60 seconds into future
        @mock.patch('time.time', mock_time)
        def _check_reload(self):
            self.assertEquals('new value', self.conf.get('k1'))
            self.assertEquals('v2', self.conf.get('k2'))
        _check_reload(self)


if __name__ == '__main__':
    unittest.main()
