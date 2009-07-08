#!/usr/bin/env python
"""\
@file rub_test.py
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

from llbase import rub

class RubTester(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testNoMatch(self):
        expected = 'http://example.com/'
        actual = rub.format(expected)
        self.assertEquals(actual, expected)

        expected = 'http://example.com/{$foo}/'
        actual = rub.format(expected)
        self.assertEquals(actual, expected)

    def testSub(self):
        context = {'foo':'bar'}
        actual = rub.format('http://example.com/{$foo}/', **context)
        self.assertEquals(actual, 'http://example.com/bar/')

    def testKWArgs(self):
        actual = rub.format('http://example.com/{$foo}/', foo='bar')
        self.assertEquals(actual, 'http://example.com/bar/')
        actual = rub.format('http://example.com/{$foo}/', foo='baz')
        self.assertEquals(actual, 'http://example.com/baz/')

if __name__ == '__main__':
    unittest.main()
