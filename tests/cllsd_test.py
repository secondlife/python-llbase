# file: cllsd_test.py
#
# $LicenseInfo:firstyear=2008&license=mit$
#
# Copyright (c) 2008-2009, Linden Research, Inc.
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
Types as well as parsing and formatting functions for handling LLSD.
"""

from datetime import datetime, date
import os.path
import sys
import time
import unittest
import uuid

from llbase import llsd

values = (
    '&<>',
    u'\u81acj',
    llsd.uri('http://foo<'),
    uuid.UUID(int=0),
    ['thing', 123, 1.34],
    sys.maxint + 10,
    llsd.binary('foo'),
    {u'f&\u1212': 3},
    3.1,
    True,
    None,
    datetime.fromtimestamp(time.time()),
    date(1066,1,1),
    )

class CLLSDTest(unittest.TestCase):
    """
    This class aggreates all the test cases for the C extension cllsd.
    The performance comparision between c extension and pure python of
    each value type is done in separate method.
    """
    def runValueTest(self, v, times, debug=False):
        """
        Uility method to run performance comparision on passed in value.
        It will use passed-in value to construct a large llsd object.
        """
        # check whether it's windows platform first
        if sys.platform.lower().startswith('win'):
            print "C extension is not supported on Windows. Test abort."
            return
        
        import _cllsd as cllsd
        
        if debug:
            print '%r => %r' % (v, cllsd.llsd_to_xml(v))

        a = [[{'a': v}]] * times

        s = time.time()
        cresult = cllsd.llsd_to_xml(a)
        chash = hash(cresult)
        e = time.time()
        t1 = e - s
        if debug:
            print "C running time:", t1

        s = time.time()
        presult = llsd.LLSDXMLFormatter()._format(a)
        phash = hash(presult)
        e = time.time()
        t2 = e - s
        if debug:
            print "Pure python running time:", t2
            print "\ncpresult:",cresult
            print "presult:",presult

        self.assertEquals(a, llsd.parse(cresult))
        self.assertEquals(a, llsd.parse(presult))
        #self.assertEquals(chash, phash)

        if debug:
            print 'Speedup:', t2 / t1


    def testCLLSDPerformanceString(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a string value.
        """
        self.runValueTest(values[0], 1000)
    
    def testCLLSDPerformanceUnicodeString(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a Unicode string value.
        """
        self.runValueTest(values[1], 1000)
    
    def testCLLSDPerformanceURI(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a URI value.
        """
        self.runValueTest(values[2], 1000)

    def testCLLSDPerformceUUID(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a UUID value.
        """
        self.runValueTest(values[3], 1000)
        
    def testCLLSDPerformanceArray(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a Array value.
        """
        self.runValueTest(values[4], 1000)
    
    def testCLLSDPerformanceInteger(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a Integer value.
        """
        self.runValueTest(values[5], 1000)

    def testCLLSDPerformanceBinary(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a Binary value.
        """
        self.runValueTest(values[6], 1000)

    def testCLLSDPerformanceMap(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a Map value.
        """
        self.runValueTest(values[7], 1000)

    def testCLLSDPerformanceReal(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a Real value.
        """
        self.runValueTest(values[8], 1000)

    def testCLLSDPerformanceBoolean(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a Boolean value.
        """
        self.runValueTest(values[9], 1000)

    def testCLLSDPerformanceUndef(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a undefined value.
        """
        self.runValueTest(values[10], 1000)

    def testCLLSDPerformanceDate(self):
        """
        Test performance for serialization of a large mixed array which
        is consistent of map which has a datetime value.
        """
        self.runValueTest(values[11], 1000)

    def testCLLSDFormatDate(self):
        """
        Test serialization of a date before the year 1900
        """
        # check whether it's windows platform first
        if sys.platform.lower().startswith('win'):
            print "C extension is not supported on Windows. Test abort."
            return
        
        import _cllsd as cllsd
       
        a = [[{'a': values[12]}]]
        b = [[{'a': datetime(1066, 1, 1, 0, 0)}]]

        cresult = cllsd.llsd_to_xml(a)
        self.assertEquals(b, llsd.parse(cresult))

    def testCLLSDPerformanceComposited(self):
        """
        Test performance for serialization of a composited llsd object.
        """
        composited_object = [{'destination': 'http://secondlife.com'},
        {'version': 1},
        {'modification_date': datetime(2006, 2, 1, 14, 29, 53, 460000)},
        {'first_name': 'Pat', 'last_name': 'Lin', 'granters': [uuid.UUID('a2e76fcd-9360-4f6d-a924-000000000003')],
        'look_at': [-0.043753, -0.99904199999999999, 0.0],
        'attachment_data': [{'attachment_point': 2, 'item_id': uuid.UUID('d6852c11-a74e-309a-0462-50533f1ef9b3'),
        'asset_id': uuid.UUID('c69b29b1-8944-58ae-a7c5-2ca7b23e22fb')},
        {'attachment_point': 10, 'item_id': uuid.UUID('ff852c22-a74e-309a-0462-50533f1ef900'),
        'asset_id': uuid.UUID('5868dd20-c25a-47bd-8b4c-dedc99ef9479')}],
        'session_id': uuid.UUID('2c585cec-038c-40b0-b42e-a25ebab4d132'),
        'agent_id': uuid.UUID('3c115e51-04f4-523c-9fa6-98aff1034730'),
        'circuit_code': 1075, 'position': [70.924700000000001, 254.37799999999999, 38.730400000000003]}]

        self.runValueTest(composited_object, 1)
