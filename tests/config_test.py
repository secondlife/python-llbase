# file: config_test.py
#
# $LicenseInfo:firstyear=2009&license=mit$
#
# Copyright (c) 2009, Linden Research, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# $/LicenseInfo$

"""
Test the config module
"""

import mock
import os
import tempfile
from StringIO import StringIO
import time
import unittest
import uuid

from llbase import config
from llbase import llsd

class ConfigInstanceTester(unittest.TestCase):
    """
    This class aggregates all the tests for module config.
    """
    def setUp(self):
        """
        Loads a config file for testing.
        """
        self._config = config.Config(r"./test_files/config_test.xml")

    def tearDown(self):
        """
        Tear down method.
        """
        pass

    def testConfigConstructor(self):
        """
        Test constructor of Config, and verify whether the key/value in the
        passed in file has been loaded.

        Maps to test scenario module:config:row#6
        """
        con = config.Config(r"./test_files/config_test.xml")

        self.assertEquals(uuid.UUID("67153d5b-3659-afb4-8510-adda2c034649"), con.get('region_id'))
        self.assertEquals('one minute', con.get('scale'))

    def testNonExistentConfigFile(self):
        """
        Test constructor of Config with a non-existent file. IOError should be
        raised.

        Maps to test scenario module:config:row#8
        """
        try:
            config.Config(r"/non/existent/file.x")
            self.fail("IOError should be raised for non-existent file")
        except IOError:
            pass

    def testEmptyConstructor(self):
        """
        Test empty constructor, no exception should raised.
        """
        c = config.Config(None)

        self.assertEquals(0, c._get_last_modified_time())

    def testGet1(self):
        """
        Test get(key) of config.

        Maps to test scenario module:config:row#11
        """
        self.assertEquals(uuid.UUID("67153d5b-3659-afb4-8510-adda2c034649"),
                          self._config.get('region_id'))

    def testGet2(self):
        """
        Test get(key) of config.

        Maps to test scenario module:config:row#12
        """
        self.assertEquals('one minute', self._config.get('scale'))

    def testGet3(self):
        """
        Test get(key) of config

        Maps to test scenario module:config:row#13
        """
        expected_result = {'total task count': 4.0, 'active task count': 0.0,
        'time dilation': 0.9878624, 'lsl instructions per second': 0.0,
        'frame ms': 0.7757886, 'agent ms': 0.01599029,
        'sim other ms': 0.1826937, 'pysics fps': 44.38906,
        'outbound packets per second': 1.277508, 'pending downloads': 0.0,
        'pending uploads': 0.0001096525, 'net ms': 0.3152919,
        'agent updates per second': 1.34, 'inbound packets per second': 1.228283,
        'script ms': 0.1338836, 'main agent count': 0.0, 'active script count': 4.0,
        'image ms': 0.01865955, 'sim physics ms': 0.04323055,
        'child agent count': 0.0, 'sim fps': 44.38898}

        self.assertEquals(expected_result, self._config.get('simulator statistics'))

    def testNonExistentKey(self):
        """
        Test get(key) with non-existent key.
        None should be returned.

        Maps to test scenario module:config:row#14
        """
        self.assertEquals(None, self._config.get("nonexistentkey"))

    def testNonStringKey(self):
        """
        Test get(key) with non string key.
        None should be returned.

        Maps to test scenario module:config:row#15
        """
        self.assertEquals(None, self._config.get(123))

    def testSet1(self):
        """
        Test set(key, value) with exitent key but a new value.
        new value should be updated.

        Maps to test scenario module:config:row#17
        """
        new_value = 'new_scale_value'
        self._config.set('scale', new_value)

        # check whether the value is updated
        self.assertEquals(new_value, self._config.get('scale'));

    def testSet2(self):
        """
        Test set(key, value) with new key and new value.
        new key/value should be added.

        Maps to test scenario module:config:row#18
        """
        new_key = "key123"
        new_value = "value123"

        self._config.set(new_key, new_value)

        # check
        self.assertEquals(new_value, self._config.get(new_key))

    def testSet3(self):
        """
        Test set(key, value) with non string key.

        Exception should be raised.

        Maps to test scenario module:config:row#19
        """
        try:
            self._config.set(123, 123)
            self.fail("Exception is expected for non-string key")
        except Exception, e:
            pass

    def testUpdateDict(self):
        """
        Test update function with a dict, the existent key should
        have value updated, the non-existent key/value should be added.

        Maps to test scenarios module:config:row#21
        """
        dict = {'scale': 'updateValue', 'id': 888}

        # update config with dict
        self._config.update(dict);

        # chech the update
        self.assertEquals('updateValue', self._config.get('scale'))
        self.assertEquals(888, self._config.get('id'))

    def testUpdateFile(self):
        """
        Test update with another file.

        Maps to test scenario module:config:row#23
        """
        self._config.update(r"./test_files/config_update.xml")

        # check the value
        self.assertEquals('updateValue', self._config.get('scale'))
        self.assertEquals(888, self._config.get('id'))

        self._config.as_dict()

    def testUpdateWithNonExistentFile(self):
        """
        Test update with non existent file.
        IOError should be raised.

        Maps to test scenario module:config:row#25
        """
        self.assertRaises(IOError, self._config.update, r"/lala/lala.x")


    def testGolobalLoad(self):
        """
        Test the module fucntion load.

        Maps to test scenario module:config:row#30
        """
        config.load(r"./test_files/config_test.xml")

        self.assertEquals('one minute', config.get('scale'))

        self.assertEquals(uuid.UUID("67153d5b-3659-afb4-8510-adda2c034649"),
                          config.get('region_id'))

        expected_result = {'total task count': 4.0, 'active task count': 0.0,
        'time dilation': 0.9878624, 'lsl instructions per second': 0.0,
        'frame ms': 0.7757886, 'agent ms': 0.01599029,
        'sim other ms': 0.1826937, 'pysics fps': 44.38906,
        'outbound packets per second': 1.277508, 'pending downloads': 0.0,
        'pending uploads': 0.0001096525, 'net ms': 0.3152919,
        'agent updates per second': 1.34, 'inbound packets per second': 1.228283,
        'script ms': 0.1338836, 'main agent count': 0.0, 'active script count': 4.0,
        'image ms': 0.01865955, 'sim physics ms': 0.04323055,
        'child agent count': 0.0, 'sim fps': 44.38898}

        self.assertEquals(expected_result, config.get('simulator statistics'))

    def testLoadWithNonExistentFile(self):
        """
        Test the module function load with non-existent file.
        IOError should be raised.

        Maps to test scenario module:config:row#32
        """
        self.assertRaises(IOError, config.load, r"/lala/lala.x")

    def testGlobalGet1(self):
        """
        Test module function get(key).

        Maps to test scenario module:config:row#35
        """

        config.load(r"./test_files/config_test.xml")

        self.assertEquals(uuid.UUID("67153d5b-3659-afb4-8510-adda2c034649"),
                          config.get('region_id'))

    def testGlobalGet2(self):
        """
        Test get(key) of config.

        Maps to test scenario module:config:row#35
        """

        config.load(r"./test_files/config_test.xml")

        self.assertEquals('one minute', config.get('scale'))

    def testGlobalGet3(self):
        """
        Test get(key) of config

        Maps to test scenario module:config:row#35
        """

        config.load(r"./test_files/config_test.xml")

        expected_result = {'total task count': 4.0, 'active task count': 0.0,
        'time dilation': 0.9878624, 'lsl instructions per second': 0.0,
        'frame ms': 0.7757886, 'agent ms': 0.01599029,
        'sim other ms': 0.1826937, 'pysics fps': 44.38906,
        'outbound packets per second': 1.277508, 'pending downloads': 0.0,
        'pending uploads': 0.0001096525, 'net ms': 0.3152919,
        'agent updates per second': 1.34, 'inbound packets per second': 1.228283,
        'script ms': 0.1338836, 'main agent count': 0.0, 'active script count': 4.0,
        'image ms': 0.01865955, 'sim physics ms': 0.04323055,
        'child agent count': 0.0, 'sim fps': 44.38898}

        self.assertEquals(expected_result, self._config.get('simulator statistics'))

    def testGlobalGetNonExistentKey(self):
        """
        Test get(key) with non-existent key.
        None should be returned.

        Maps to test scenario module:config:row#35
        """
        config.load(r"./test_files/config_test.xml")

        self.assertEquals(None, config.get("nonexistentkey"))

    def testGlobalGetNonStringKey(self):
        """
        Test get(key) with non string key.
        None should be returned.

        Maps to test scenario module:config:row#35
        """
        config.load(r"./test_files/config_test.xml")

        self.assertEquals(None, config.get(123))

    def testGlobalSet1(self):
        """
        Test module set(key, value) with exitent key but a new value.
        new value should be updated.

        Maps to test scenario module:config:row#37
        """

        config.load(r"./test_files/config_test.xml")

        new_value = 'new_scale_value'
        config.set('scale', new_value)

        # check whether the value is updated
        self.assertEquals(new_value, config.get('scale'));

    def testGlobalSet2(self):
        """
        Test module set(key, value) with new key and new value.
        new key/value should be added.

        Maps to test scenario module:config:row#37
        """
        config.load(r"./test_files/config_test.xml")

        new_key = "key123"
        new_value = "value123"

        config.set(new_key, new_value)

        # check
        self.assertEquals(new_value, config.get(new_key))

    def testGlobalSet3(self):
        """
        Test module set(key, value) with non string key.

        Exception should be raised.

        Maps to test scenario module:config:row#19
        """
        config.load(r"./test_files/config_test.xml")

        try:
            config.set(123, 123)
            self.fail("Exception is expected for non-string key")
        except Exception, e:
            pass

    def testGlobalUpdateDict(self):
        """
        Test update function with a dict, the existent key should
        have value updated, the non-existent key/value should be added.

        Maps to test scenarios module:config:row#36
        """
        config.load(r"./test_files/config_test.xml")

        dict = {'scale': 'updateValue', 'id': 888}

        # update config with dict
        config.update(dict);

        # chech the update
        self.assertEquals('updateValue', config.get('scale'))
        self.assertEquals(888, config.get('id'))

    def testGlobalUpdateFile(self):
        """
        Test update with another file.

        Maps to test scenario module:config:row#36
        """
        config.load(r"./test_files/config_test.xml")

        config.update(r"./test_files/config_update.xml")

        # check the value
        self.assertEquals('updateValue', config.get('scale'))
        self.assertEquals(888, config.get('id'))

    def testGlobalUpdateWithNonExistentFile(self):
        """
        Test update with non existent file.
        IOError should be raised.

        Maps to test scenario module:config:row#36
        """
        config.load(r"./test_files/config_test.xml")

        self.assertRaises(IOError, config.update, r"/lala/lala.x")

    def testGlobalNoneFile(self):
        """
        No exception should be raised when global config is null.
        All the get, set, update should function properly.
        """
        config._g_config = None

        self.assert_(config.get("123") == None);

        config._g_config = None

        config.update({"123": "123"})

        self.assertEquals("123", config.get("123"))

        config._g_config = None

        config.set("k1", "v1")

        self.assertEquals("v1", config.get("k1"))


    def testUpdateFilelike(self):
        """
        Test with a file like string
        """
        self._config['k1'] = 'v1'
        self._config['k2'] = 'v2'
        new = {'k1': 'new_value', 'k3':'v3'}
        filelike = StringIO(llsd.format_xml(new))
        self._config.update(filelike)

        self.assertEquals('new_value', self._config.get('k1'))
        self.assertEquals('v3', self._config.get('k3'))

class ConfigInstanceFileTester(unittest.TestCase):
    """
    This class aggregate tests for realoading config files.
    """
    def setUp(self):
        """
        Set up config file and write in initial configuration.
        """
        # not worried about race conditions, this is just some unit tests.
        self.filename = tempfile.mktemp()
        initial_config = {'k1':'v1', 'k2':'v2'}
        self.writeConf(initial_config)
        self.conf = config.Config(self.filename)

    def tearDown(self):
        """
        Tear down method.
        """
        os.remove(self.filename)

    def writeConf(self, payload):
        """
        Utility method to write conf
        """
        conffile = open(self.filename, 'wb')
        conffile.write(llsd.format_xml(payload))
        conffile.close()

    def testFile(self):
        """
        Check the initial config of file.
        """
        self.assertEquals('v1', self.conf.get('k1'))
        self.assertEquals('v2', self.conf.get('k2'))

    def testReload(self):
        """
        Test reoload function.
        """
        self.assertEquals('v1', self.conf.get('k1'))
        self.assertEquals('v2', self.conf.get('k2'))

        now = time.time()

        new_conf = {'k1':'new value', 'k2':'v2'}
        self.writeConf(new_conf)
        self.conf._last_mod_time
        os.utime(self.filename, (now + 10, now + 10))

        mock_time = mock.Mock(return_value=now + 60) # 60 seconds into future
        @mock.patch('time.time', mock_time)
        def _check_reload(self):
            self.assertEquals('new value', self.conf.get('k1'))
            self.assertEquals('v2', self.conf.get('k2'))
        _check_reload(self)


class ConfigStressTest(unittest.TestCase):
    """
    This class aggregates stress test of load config file.
    """
    def testLoadStress(self):
        """
        Run loading config file for 500 times, print out benchmark

        Maps to test scenario module:config:row#41
        """
        t = time.clock()
        for i in range(0, 500):
            x = config.load(r"test_files/config_test.xml")
        delta = time.clock() - t
        print "config.load", 500, " times takes total :", delta, "secs"
        print "average time:", delta / 500, "secs"

if __name__ == '__main__':
    unittest.main()
