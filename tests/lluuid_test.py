#!/usr/bin/env python
"""
@file lluuid_test.py
@brief Test the uuid module
"""

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

import unittest
import uuid

from llbase import lluuid

class LLUUIDTester(unittest.TestCase):
    """
    Aggreate all tests for lluuid
    """
    def testUUIDType(self):
        """
        Test whether the generated value is of type uuid.UUID

        Maps to test scenario module:lluuid:row#4
        """
        self.assert_(isinstance(lluuid.generate(), uuid.UUID))

    def testNotEqual(self):
        """
        Test whether two generated UUID is different.

        Maps to test scenario module:lluuid:row#5
        """
        one = lluuid.generate()
        two = lluuid.generate()
        self.assertNotEqual(one, two)

if __name__ == '__main__':
    unittest.main()
