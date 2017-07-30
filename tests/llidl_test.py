# file: llidl_test.py
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
Test the llidl module
"""

import datetime
import io
import unittest

from llbase import llidl
from llbase import llsd
from llbase import lluuid
from llbase.llidl import MatchError
from llbase.llidl import ParseError

def _dateToday():
    """
    Return the datetime object which represents today.
    """
    return datetime.datetime.today()

def _dateEpoch():
    """
    Return the datatime object which represents Epoch time.
    """
    return datetime.datetime.fromtimestamp(0)

def _uri():
    """
    Return a llsd.uri object for teting.
    """
    return llsd.uri('http://tools.ietf.org/html/draft-hamrick-llsd-00')

def _uuid():
    """
    Generate an UUID for testing.
    """
    return lluuid.generate()

def _binary():
    """
    Return a llsd.binary object for testing.
    """
    return llsd.binary(b"\0x01\x02\x03")

class LLIDLTypeTests(unittest.TestCase):
    """
    This class aggregates all the parse and match tests for atomic types:
    undef, boolean, integer, real, string, UUID, date, URI, binary.
    """
    def testUndef(self):
        """
        Parse and match tests for type: undef.

        Maps to test scenarios module:llidl:row#6-18
        """
        v = llidl.parse_value("undef")

        self.assert_(v.match(None))
        self.assert_(v.match(True))
        self.assert_(v.match(False))
        self.assert_(v.match(0))
        self.assert_(v.match(1))
        self.assert_(v.match(3))
        self.assert_(v.match(0.0))
        self.assert_(v.match(1.0))
        self.assert_(v.match(3.14))
        self.assert_(v.match(""))
        self.assert_(v.match("True"))
        self.assert_(v.match("False"))
        self.assert_(v.match(_dateToday()))
        self.assert_(v.match(_uuid()))
        self.assert_(v.match(_uri()))
        self.assert_(v.match(_binary()))

    def testBool(self):
        """
        Parse and match tests for type: bool.

        Maps to test scenarios module:llidl:row#19-32
        """
        v = llidl.parse_value("bool")
        self.assert_(v.has_defaulted(None))
        self.assert_(v.match(True))
        self.assert_(v.match(False))
        self.assert_(v.match(0))
        self.assert_(v.match(1))
        self.assert_(v.incompatible(3))
        self.assert_(v.match(0.0))
        self.assert_(v.match(1.0))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.match(""))
        self.assert_(v.match("true"))
        self.assert_(v.incompatible("false"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def testInt(self):
        """
        Parse and match tests for type: integer.

        Maps to test scenarios module:llidl:row#34-47
        """
        v = llidl.parse_value("int")
        self.assert_(v.has_defaulted(None))
        self.assert_(v.match(True))
        self.assert_(v.match(False))
        self.assert_(v.match(0))
        self.assert_(v.match(1))
        self.assert_(v.match(0.0))
        self.assert_(v.match(10.0))
        self.assert_(v.incompatible(3.14))
        if llsd.PY2:
            # In Python 2, this would require a 'long', but it fits in a
            # Python 3 'int' and hence is not incompatible().
            self.assert_(v.incompatible(6.02e23))
        else:
            self.assert_(v.match(6.02e23))
        self.assert_(v.has_defaulted(""))
        self.assert_(v.match("0"))
        self.assert_(v.match("1"))
        self.assert_(v.match("0.0"))
        self.assert_(v.match("10.0"))
        self.assert_(v.incompatible("3.14"))
        if llsd.PY2:
            self.assert_(v.incompatible("6.02e23"))
        else:
            self.assert_(v.match("6.02e23"))
        self.assert_(v.incompatible("blob"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def testReal(self):
        """
        Parse and match tests for type: real.

        Maps to test scenarios module:llidl:row#49-62
        """
        v = llidl.parse_value("real")
        self.assert_(v.has_defaulted(None))
        self.assert_(v.match(True))
        self.assert_(v.match(False))
        self.assert_(v.match(0))
        self.assert_(v.match(1))
        self.assert_(v.match(0.0))
        self.assert_(v.match(10.0))
        self.assert_(v.match(3.14))
        self.assert_(v.match(6.02e23))
        self.assert_(v.has_defaulted(""))
        self.assert_(v.match("0"))
        self.assert_(v.match("1"))
        self.assert_(v.match("0.0"))
        self.assert_(v.match("10.0"))
        self.assert_(v.match("3.14"))
        self.assert_(v.match("6.02e23"))
        self.assert_(v.incompatible("blob"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def testString(self):
        """
        Parse and match tests for type: string.

        Maps to test scenarios module:llidl:row#64-76
        """
        v = llidl.parse_value("string")
        self.assert_(v.has_defaulted(None))
        self.assert_(v.match(True))
        self.assert_(v.match(False))
        self.assert_(v.match(3))
        self.assert_(v.match(3.14))
        self.assert_(v.match(""))
        self.assert_(v.match("bob"))
        self.assert_(v.match(_dateToday()))
        self.assert_(v.match(_uuid()))
        self.assert_(v.match(_uri()))
        self.assert_(v.incompatible(_binary()))

    def testDate(self):
        """
        Parse and match tests for type: Date.

        Maps to test scenarios module:llidl:row#78-90
        """
        v = llidl.parse_value("date")
        self.assert_(v.has_defaulted(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.has_defaulted(""))
        self.assert_(v.match("2009-02-06T22:17:38Z"))
        # self.assert_(v.match("2009-02-06T22:17:38.0025Z"))
        self.assert_(v.incompatible("bob"))
        self.assert_(v.match(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def testUUID(self):
        """
        Parse and match tests for type: UUID.

        Maps to test scenarios module:llidl:row#92-104
        """
        v = llidl.parse_value("uuid")
        self.assert_(v.has_defaulted(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.has_defaulted(""))
        self.assert_(v.match("6cb93268-5148-423f-8618-eaa0884f5b6c"))
        self.assert_(v.incompatible("bob"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.match(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def testURI(self):
        """
        Parse and match tests for type: URI.

        Maps to test scenarios module:llidl:row#106-118
        """
        v = llidl.parse_value("uri")
        self.assert_(v.has_defaulted(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.has_defaulted(""))
        self.assert_(v.match("http://example.com/"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.match(_uri()))
        self.assert_(v.incompatible(_binary()))

    def testBinary(self):
        """
        Parse and match tests for type: string.

        Maps to test scenarios module:llidl:row#120-132
        """
        v = llidl.parse_value("binary")
        self.assert_(v.has_defaulted(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.incompatible("bob"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.match(_binary()))

class LLIDLSelectorTests(unittest.TestCase):
    """
    This class aggregates all the test cases for atomic type selectors.

    The selector is used to indicate a particular fixed value.
    """
    def testTrue(self):
        """
        Tests the parse and match for a boolean selector with value 'true'

        Maps to test scenario module:llidl:row#142-154
        """
        v = llidl.parse_value("true")
        self.assert_(v.incompatible(None))
        self.assert_(v.match(True))
        self.assert_(v.incompatible(False))
        self.assert_(v.incompatible(0))
        self.assert_(v.match(1))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(0.0))
        self.assert_(v.match(1.0))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.incompatible(""))
        self.assert_(v.match("true"))
        self.assert_(v.incompatible("false"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def testFalse(self):
        """
        Tests the parse and match for a boolean selector with value 'false'

        Maps to test scenario module:llidl:row#156-168
        """
        v = llidl.parse_value("false")
        self.assert_(v.has_defaulted(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.match(False))
        self.assert_(v.match(0))
        self.assert_(v.incompatible(1))
        self.assert_(v.incompatible(3))
        self.assert_(v.match(0.0))
        self.assert_(v.incompatible(1.0))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.match(""))
        self.assert_(v.incompatible("true"))
        self.assert_(v.incompatible("false"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def testNumber1983(self):
        """
        Tests the parse and match for a integer selector with value 1983

        Maps to test scenario module:llidl:row#170-182
        """
        v = llidl.parse_value("1983")
        self.assert_(v.incompatible(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(False))
        self.assert_(v.incompatible(0))
        self.assert_(v.incompatible(3))
        self.assert_(v.match(1983))
        self.assert_(v.incompatible(0.0))
        self.assert_(v.match(1983.0))
        self.assert_(v.match(1983.2))
        self.assert_(v.incompatible(""))
        self.assert_(v.match("1983"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def testNumber0(self):
        """
        Tests the parse and match for a integer selector with value 0.
        """
        v = llidl.parse_value("0")
        self.assert_(v.has_defaulted(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.match(False))
        self.assert_(v.match(0))
        self.assert_(v.incompatible(3))
        self.assert_(v.match(0.0))
        self.assert_(v.incompatible(16.0))
        self.assert_(v.has_defaulted(""))
        self.assert_(v.match("0"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def testStringSecondLife(self):
        """
        Tests the parse and match for a string selector with value "secondLife"

        Maps to test scenario module:llidl:row#184-196
        """
        v = llidl.parse_value('"secondLife"')
        self.assert_(v.incompatible(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(False))
        self.assert_(v.incompatible(0))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(0.0))
        self.assert_(v.incompatible(16.0))
        self.assert_(v.incompatible(""))
        self.assert_(v.match("secondLife"))
        self.assert_(v.incompatible("1983"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def x_t_est_string_empty(self):
        # currently the draft doesn't support this test
        v = llidl.parse_value('""')
        self.assert_(v.match(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(False))
        self.assert_(v.incompatible(0))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(0.0))
        self.assert_(v.incompatible(16.0))
        self.assert_(v.match(""))
        self.assert_(v.incompatible("bob"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

class LLIDLArrayTests(unittest.TestCase):
    """
    This class aggregates test cases for the composite type : array. LLIDL has
    several array representations:
    - Fixed length array with same value type: [value, value]
    - Fixed length array with different value types: [value1, value2, value3]
    - Array of arbitrary length with same value type: [value, ...]
    - Array of arbitraty length with different value types: [value1, value2, ...]
    """
    def testFixedLengthSameValueSimpleTypes(self):
        """
        Test parse and match of fixed length array with same value type.

        Maps to test scenario module:llidl:row#201
        """
        v = llidl.parse_value("[real, real, real]")

        # simple types
        self.assert_(v.incompatible(123))
        self.assert_(v.incompatible(3.1415))
        self.assert_(v.incompatible(lluuid.generate()))


    def testFixedLengthSameValueEmptyArray(self):
        """
        Test parse and match of fixed length array with same value type.

        Maps to test scenario module:llidl:row#202
        """
        v = llidl.parse_value("[real, real, real]")
        # empty array
        self.assert_(not v.match([]))

    def testFixedLengthSameValueVariableLength(self):
        """
        Test parse and match of fixed length array with same value type.

        Maps to test scenario module:llidl:row#203,204,206
        """
        v = llidl.parse_value("[real, real, real]")

        #  1 element array
        self.assert_(not v.match([1.23]))

        # 2 elements array
        self.assert_(not v.match([1.23, 789.0]))

        # 4 elements array ( > 3)
        self.assert_(not v.match([1.23, 2.3, 4.56, 5.67]))

    def testFixedLengthSameValueSameLength(self):
        """
        Test parse and match of fixed length array with same value type.

        Maps to test scenario module:llidl:row#205, 207
        """
        v = llidl.parse_value("[real, real, real]")

        # 3 elements with incorrect value type
        self.assert_(v.incompatible([1.23, 3.3, 'string']))

        # 3 elements with correct value type
        self.assert_(v.match([1.23, 3.3, 2.3434]))

    def testFixedLengthDifferentValuesSimpleType(self):
        """
        Test parse and match of fixed length array with different value types.

        Maps to test scenario module:llidl:row#209
        """
        v = llidl.parse_value("[int, string]")

        # simple types
        self.assert_(v.incompatible(123))
        self.assert_(v.incompatible(3.1415))
        self.assert_(v.incompatible('string'))
        self.assert_(v.incompatible(lluuid.generate()))

    def testFixedLengthDifferentValuesEmptyArray(self):
        """
        Test parse and match of fixed length array with different value types.

        Maps to test scenario module:llidl:row#210
        """
        v = llidl.parse_value("[int, string]")

        # empty array
        self.assert_(not v.match([]))


    def testFixedLengthDifferentValuesVariableLength(self):
        """
        Test parse and match of fixed length array with different value types.

        Maps to test scenario module:llidl:row#211, 212
        """
        v = llidl.parse_value("[int, string]")

        self.assert_(not v.match([123]))
        self.assert_(v.incompatible(['str1']))
        self.assert_(not v.match([123, 'str1', 'str2']))
        self.assert_(v.incompatible(['str1', 123, 345]))

    def testFixedLengthDifferentValuesSameLength(self):
        """
        Test parse and match of fixed length array with different value types.

        Maps to test scenario module:llidl:row#213 - 216
        """
        v = llidl.parse_value("[int, string]")

        self.assert_(v.match([123, 'str1']))
        self.assert_(v.match([123, 1.2323]))
        self.assert_(v.match([123, 456]))
        self.assert_(v.incompatible([9.999, 'str1']))

    def testArbitratyLengthSameValueWithSimpleTypes(self):
        """
        Test parse and match of arbitrary length array with same value type.

        Maps to test scenario module:llidl:row#218
        """
        v = llidl.parse_value("[uri,...]")

        # simple types
        self.assert_(v.incompatible(123))
        self.assert_(v.incompatible(3.1415))
        self.assert_(v.incompatible('string'))
        self.assert_(v.incompatible(lluuid.generate()))

    def testArbitratyLengthSameValueWithEmptyArray(self):
        """
        Test parse and match of arbitrary length array with same value type.

        Maps to test scenario module:llidl:row#219
        """
        v = llidl.parse_value("[uri,...]")

        # empty array
        self.assert_(v.match([]))

    def testArbitratyLengthSameValueWithVariableLength(self):
        """
        Test parse and match of arbitrary length array with same value type.

        Maps to test scenario module:llidl:row#220,221
        """
        v = llidl.parse_value("[uri,...]")

        # 1 element array
        self.assert_(v.match([llsd.uri("www.foo.com")]))

        # 2 elements array
        self.assert_(v.match([llsd.uri("www.foo.com"), llsd.uri("www.bar.com")]))

        # 3 elements array
        self.assert_(v.match([llsd.uri("www.foo.com"), llsd.uri("www.bar.com"),
                     llsd.uri(r"www.topcoder.com/tc/review?project_id=30012")]))

    def testArbitraryLengthSameValueIncorrectType(self):
        """
        Test parse and match of arbitrary length array with same value type.

        Maps to test scenario module:llidl:row#222
        """
        v = llidl.parse_value("[uri,...]")

        # 1 element
        self.assert_(v.incompatible([123]))

        # 2 elements
        self.assert_(v.incompatible([llsd.uri("www.google.com"), 123]))

    def testArbitrayLengthDifferentValuesSimpleType(self):
        """
        Test parse and match of arbitrary length array with different value types.

        Maps to test scenario module:llidl:row#224
        """
        v = llidl.parse_value("[string, int,...]")

        # simple types
        self.assert_(v.incompatible(123))
        self.assert_(v.incompatible(3.1415))
        self.assert_(v.incompatible('string'))
        self.assert_(v.incompatible(lluuid.generate()))

    def testArbitrayLengthDifferentValuesEmptyArray(self):
        """
        Test parse and match of arbitrary length array with different value types.

        Maps to test scenario module:llidl:row#225
        """
        v = llidl.parse_value("[string, int,...]")

        # empty array
        self.assert_(v.match([]))

    def testArbitrayLengthDifferentValuesVariableLength(self):
        """
        Test parse and match of arbitrary length array with different value types.

        Maps to test scenario module:llidl:row#226- 231
        """
        v = llidl.parse_value("[string, int,...]")

        self.assert_(not v.match(['str']))
        self.assert_(not v.match([12345]))
        self.assert_(not v.match(['str', 123, 'str2']))
        self.assert_(v.incompatible(['foo', 'bar']))

        self.assert_(v.match(['foo', 123]))
        self.assert_(v.match(['foo', 123, 'bar', 345]))

    def testArrayHasAddiontional(self):
        """
        Test has_addiontal function of parsed array value matcher.

        Maps to test scenario module:llidl:row#250
        """
        v = llidl.parse_value("[int, int]")

        self.assert_(v.match([123, 123]))
        self.assert_(not v.match([123, 345, 678]))
        self.assert_(v.has_additional([123, 345, 678]))

    def testArrayValid(self):
        """
        Test valid function of parsed array value matcher.

        Maps to test scenario module:llidl:row#253
        """
        v = llidl.parse_value("[int, int]")

        self.assert_(v.valid([123, 123]))
        self.assert_(v.valid([123, 345, 678]))

class LLIDLMapTests(unittest.TestCase):
    """
    This class aggregates test cases for the composite type : Map. LLIDL has
    two map representations:
    - Map with comma separated key/value pairs: {key1 : value1, key2 : value 2}
    - Map with abitraty key names: { $ : int }
    """
    def testMapWithKeyValuePairs(self):
        """
        Test parse and match of map with comma separated key/value pairs.

        Maps to test scenario module:llidl:row#233 - 241
        """
        v = llidl.parse_value("{ name : string, phone: int }")

        # simple types
        self.assert_(v.incompatible(123))
        self.assert_(v.incompatible(3.1415))
        self.assert_(v.incompatible('string'))
        self.assert_(v.incompatible(lluuid.generate()))

        # empty array
        self.assert_(v.incompatible([]))

        # empty map
        self.assert_(v.has_defaulted({}))

        # one entry map
        self.assert_(v.has_defaulted({'name': 'ant'}))
        self.assert_(v.has_defaulted({'phone': 42312334}))
        self.assert_(v.incompatible({'phone' : 'error'}))

        # two entries map
        self.assert_(v.match({'name': 'ant', 'phone': 429873232}))

        # three entries map
        self.assert_(not v.match({'name': 'ant', 'phone': 429873232, 'address' : 'xx'}))
        self.assert_(v.has_additional({'amy': 'ant', 'bob': 42, 'cam': True}))

    def testMapWithArbitraryKeys(self):
        """
        Test parse and match of map with arbitrary keys.

        Maps to test scenario module:llidl:row#242-248
        """
        v = llidl.parse_value("{ $: int }")

        # simple types
        self.assert_(v.incompatible(123))
        self.assert_(v.incompatible(3.1415))
        self.assert_(v.incompatible('string'))
        self.assert_(v.incompatible(lluuid.generate()))

         # empty array
        self.assert_(v.incompatible([]))

        # empty map
        self.assert_(v.match({}))

        # one entry map
        self.assert_(v.incompatible({'name': 'ant'}))
        self.assert_(v.match({'id1': 1234}))
        self.assert_(v.incompatible({'phone' : 'error'}))

        # two entires map
        self.assert_(v.match({'id1': 1234, 'id2': 100}))
        self.assert_(v.incompatible({'id1': 1234, 'phone' : 'error'}))
        self.assert_(v.has_defaulted({'id1': None, 'id2': 100}))

        # many entires map
        self.assert_(v.match({'id1': 1234, 'id2': 100, 'id3' : 101, 'id4' : 102}))

    def testMapHasAddiontional(self):
        """
        Test has_addiontal function of parsed map value matcher.

        Maps to test scenario module:llidl:row#251
        """
        v = llidl.parse_value("{name : string, phone : int}")

        self.assert_(v.match({'name':'bob'}))
        self.assert_(not v.match({'name' : 'bob', 'address' : 'NYC'}))
        self.assert_(v.has_additional({'name' : 'bob', 'address' : 'NYC'}))

    def testMapHasAddiontional(self):
        """
        Test valid function of parsed map value matcher.

        Maps to test scenario module:llidl:row#254
        """
        v = llidl.parse_value("{name : string, phone : int}")

        self.assert_(v.valid({'name':'bob'}))
        self.assert_(v.valid({'name' : 'bob', 'address' : 'NYC'}))
        self.assert_(v.valid({'name' : 'bob', 'phone' : 123, 'address' : 'NYC'}))


class LLIDLParseValueTests(unittest.TestCase):
    """
    This class aggregates all the test cases for parse_value.
    """
    def testParseValueSimpleType(self):
        """
        Test parse_value for simple types. No exception should be raised.
        Value object should be returned.

        Maps to test scenario module:llidl:row#259-267
        """

        # simple types
        self.assert_(llidl.parse_value('undef') != None)
        self.assert_(llidl.parse_value('string') != None)
        self.assert_(llidl.parse_value('bool') != None)
        self.assert_(llidl.parse_value('int') != None)
        self.assert_(llidl.parse_value('real') != None)
        self.assert_(llidl.parse_value('date') != None)
        self.assert_(llidl.parse_value('uri') != None)
        self.assert_(llidl.parse_value('uuid') != None)
        self.assert_(llidl.parse_value('binary') != None)

    def testParseValueCompositeType(self):
        """
        Test parse_value for composite types. No exception should be raised.
        Value object should be returned.

        Maps to test scenario module:llidl:row#269-274
        """
        # composite types
        self.assert_(llidl.parse_value('[int, int]') != None)
        self.assert_(llidl.parse_value('[int, ...]') != None)
        self.assert_(llidl.parse_value('[string, int, bool, real...]') != None)
        self.assert_(llidl.parse_value('[int, date, uuid]') != None)
        self.assert_(llidl.parse_value('{name1 : string, name2 : real, name3 : date, name4 : uuid}') != None)
        self.assert_(llidl.parse_value('{$ : int}') != None)

    def testParseValueSimpleTypeFailure1(self):
        """
        Test parse_value with incorrect type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#277, 278
        """
        self.assertRaises(ParseError, llidl.parse_value, 'foo')
        self.assertRaises(ParseError, llidl.parse_value, 'bar')

    def testParseValueSimpleTypeFailure2(self):
        """
        Test parse_value with incorrect type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#279-281
        """
        self.assertRaises(TypeError, llidl.parse_value, 123)
        self.assertRaises(TypeError, llidl.parse_value, 1.23232)
        self.assertRaises(TypeError, llidl.parse_value, _dateToday())

    def testParseValueCompositeTypeFailure1(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#283
        """
        self.assertRaises(ParseError, llidl.parse_value, '[]')

    def testParseValueCompositeTypeFailure2(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#284
        """
        self.assertRaises(ParseError, llidl.parse_value, '{}')

    def testParseValueCompositeTypeFailure3(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#285
        """
        self.assertRaises(ParseError, llidl.parse_value, '[int, real, date')

    def testParseValueCompositeTypeFailure4(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#286
        """
        self.assertRaises(ParseError, llidl.parse_value, '{name : string, phone : int')

    def testParseValueCompositeTypeFailure5(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#287
        """
        self.assertRaises(ParseError, llidl.parse_value, '{name:string, name:int}')

    def testParseValueCompositeTypeFailure6(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#288
        """
        self.assertRaises(ParseError, llidl.parse_value, '{name:string,phone:}')

    def testParseValueCompositeTypeFailure7(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#289
        """
        self.assertRaises(ParseError, llidl.parse_value, '{name:string, :int}')

    def testParseValueCompositeTypeFailure8(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#290
        """
        self.assertRaises(ParseError, llidl.parse_value, '{name:string phone,int}')

    def testParseValueCompositeTypeFailure9(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#291
        """
        self.assertRaises(ParseError, llidl.parse_value, '[int, real, invalid]')

    def testParseValueCompositeTypeFailure10(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#292
        """
        self.assertRaises(ParseError, llidl.parse_value, '{name: string, id:invalid}')

    def testParseValueCompositeTypeFailure11(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#293
        """
        self.assertRaises(ParseError, llidl.parse_value, '')

    def testParseValueCompositeTypeFailure12(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#294
        """
        self.assertRaises(ParseError, llidl.parse_value, '   ')

    def testParseValueCompositeTypeFailure13(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#295
        """
        self.assertRaises(ParseError, llidl.parse_value, '  int')

    def testParseValueCompositeTypeFailure14(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#296
        """
        self.assertRaises(ParseError, llidl.parse_value, 'int  ')

    def testParseValueCompositeTypeFailure15(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#297
        """
        self.assertRaises(ParseError, llidl.parse_value, '[...]')

    def testParseValueCompositeTypeFailure16(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#298
        """
        self.assertRaises(ParseError, llidl.parse_value, '{alphone-omega:real}')

    def testParseValueCompositeTypeFailure17(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#299
        """
        self.assertRaises(ParseError, llidl.parse_value, '{$}')

    def testParseValueCompositeTypeFailure18(self):
        """
        Test parse_value with invalid composite type name. ParseError should be raised.

        Maps to test scenario module:llidl:row#300
        """
        self.assertRaises(ParseError, llidl.parse_value, '{$:}')

class LLIDLParseSuiteTests(unittest.TestCase):
    """
    This class aggregates all the test cases for parse_suite function.
    """
    def testParseSuiteGET(self):
        """
        Test parse_suite with interface definition which uses GET method.
        The suite should be correctly parsed.

        Maps to test scenario module:llidl:row#304
        """
        s = """
            %% secondlife/getAllActiveUser
            << { id : [int, ...] }
            """

        self.assert_(llidl.parse_suite(s) != None)

    def testParseSuitePUT(self):
        """
        Test parse_suite with interface definition which uses PUT method.
        The suite should be correctly parsed.

        Maps to test scenario module:llidl:row#305
        """
        s = """
            %% secondlife/updateAllRecords
            >> { day : binary }
            """
        self.assert_(llidl.parse_suite(s) != None)

    def testParseSuitePost(self):
        """
        Test parse_suite with interface definition which uses POST method.
        The suite should be correctly parsed.

        Maps to test scenario module:llidl:row#306
        """
        s = """
            %% secondlife/getUserRecord
            -> { id : int }
            <- { name : string, rating : real, updateTime: date}
            """
        self.assert_(llidl.parse_suite(s) != None)

    def testParseSuiteMultipleResources(self):
        """
        Test parse_suite with multiple interface definitions.
        The suite should be correctly parsed.

        Maps to test scenario module:llidl:row#307
        """
        s = """
            %% secondlife/getUserRecord
            -> { id : int }
            <- { name : string, rating : real, updateTime: date}

            %% useful/resource
            -> undef
            <- { ids : [int, ...] }

            %% foo/bar
            -> { name : string }
            <- { id : uuid, data : { recordName : string, stream : binary } }
            """
        self.assert_(llidl.parse_suite(s) != None)

    def testParseSuiteVariantValues(self):
        """
        Test parse_suite with interface definition which has several variants.
        The suite should be correctly parsed.

        Maps to test scenario module:llidl:row#308
        """
        s = """
            %% foo/bar
            -> { name : string }
            <- { id : uuid, data : { recordName : string, res : &resource } }

            &resource = { update: date, data : binary}
            &resource = { update: date, ids : [int, ...] }
            &resource = { error : int }
            """
        self.assert_(llidl.parse_suite(s) != None)

    def testParseSuiteContainComments(self):
        """
        Test parse_suite with interface definition which has comments.
        The suite should be correctly parsed.

        Maps to test scenario module:llidl:row#309
        """
        s = """
            ; suite definition started
            %% secondlife/getUserRecord
            ; request definition
            -> { id : int }
            ; response definition
            <- { name : string, rating : real, updateTime: date}
            """
        self.assert_(llidl.parse_suite(s) != None)

    def checkBadParseSuite(self, s, msg=None, line=None, char=None):
        """
        Check whether parse_suite handles invalid interface definition
        correctly. ParseError should be raised, and contains correct
        error message and details (error_line, error_char).
        """
        try:
            v = llidl.parse_suite(s)
            self.fail('Incorrectly parsed "%s" as valid' % s)
        except llidl.ParseError as e:
            if msg and msg not in str(e):
                self.fail('Missing "%s" in "%s"' % (msg, str(e)))
            if line:
                self.assertEqual(e.line, line)
            if char:
                self.assertEqual(e.char, char)
            pass

    def testParseSuiteFailureIncorrectResourceName1(self):
        """
        Test parse_suite with interface definition which has incorrect resource name.
        ParseError should be raised.

        Maps to test scenario module:llidl:row#313
        """
        s = """
%% 123foo/bar
-> { name : string }
<- { id : uuid, data : { recordName : string, stream : binary } }
"""
        self.checkBadParseSuite(s, 'expected resource name', 2, 4)

    def testParseSuiteFailureIncorrectResourceName2(self):
        """
        Test parse_suite with interface definition which has incorrect resource name.
        ParseError should be raised.

        Maps to test scenario module:llidl:row#314
        """
        s = """
%% foo/bar-goo
-> { name : string }
<- { id : uuid, data : { recordName : string, stream : binary } }
"""
        self.checkBadParseSuite(s, 'malformed name', 2, 15)

    def testParseSuiteFailureNoPrefix(self):
        """
        Test parse_suite with interface definition which has no prefix %%.
        ParseError should be raised.

        Maps to test scenario module:llidl:row#315
        """
        s = """
foo/bar
-> { name : string }
<- { id : uuid, data : { recordName : string, res : binary} }
"""
        self.checkBadParseSuite(s, '', 2, 1)

    def testParseSuiteFailureIncorrectMethodIndicator(self):
        """
        Test parse_suite with interface definition which has incorrect method
        indicators.
        ParseError should be raised.

        Maps to test scenario module:llidl:row#316
        """
        s = """
%% foo/bar
->> { name : string }
<<- { id : uuid, data : { recordName : string, res : binary } }
"""
        self.checkBadParseSuite(s, '', 3, 3)

    def testParseSuiteFailureIncorrectRequest(self):
        """
        Test parse_suite with interface definition which has incorrect
        request definition.
        ParseError should be raised.

        Maps to test scenario module:llidl:row#317
        """
        s = """
%% foo/bar
-> { name : blabla }
<- { id : uuid, data : { recordName : string, res : binary} }}
"""
        self.checkBadParseSuite(s, '', 3, 19)

    def testParseSuiteFailureIncorrectResponse(self):
        """
        Test parse_suite with interface definition which has incorrect
        response definition.
        ParseError should be raised.

        Maps to test scenario module:llidl:row#318
        """
        s = """
%% foo/bar
-> { name : string }
<- { id : uuid, data : { recordName : string, res : resource } }
"""
        self.checkBadParseSuite(s, '', 4, 61)

    def testParseSuiteFailureMissingResourceName(self):
        """
        Test parse_suite with interface definitions which miss
        resource name.
        ParseError should be raised.

        Maps to test scenario module:llidl:row#319
        """
        s = """
%% secondlife/getUserRecord
-> { id : int }
<- { name : string, rating : real, updateTime: date}

%%
-> undef
<- { ids : [int, ...] }

%% foo/bar
-> { name : string }
<- { id : uuid, data : { recordName : string, stream : binary } }
"""
        self.checkBadParseSuite(s, 'resource name', 7, 1)

    def testParseSuiteFailureDuplicateResourceName(self):
        """
        Test parse_suite with interface definitions which has
        duplicated resource names
        ParseError should be raised.

        Maps to test scenario module:llidl:row#320
        """
        s = """
%% secondlife/getUserRecord
-> { id : int }
<- { name : string, rating : real, updateTime: date}

%% foo/bar
-> undef
<- { ids : [int, ...] }

%% foo/bar
-> { name : string }
<- { id : uuid, data : { recordName : string, stream : binary } }
"""
        self.checkBadParseSuite(s, '', 10, 11)

    def testParseSuiteFailureMissVariantDefinitions(self):
        """
        Test parse_suite with interface definition which missed
        variant definitions
        ParseError should be raised.

        Maps to test scenario module:llidl:row#321
        """
        s = """
%% foo/bar
-> { name : string }
<- { id : uuid, data : { recordName : string, res : &resource } }
"""
        self.checkBadParseSuite(s, 'missing', 5, 1)


class LLIDLValidTests(unittest.TestCase):
    """
    This class aggregates all the test cases for valid_request
    and valid_response.
    """
    def setUp(self):
        """
        Set up a suite instance for testing.
        """
        self._suite = llidl.parse_suite("""
                %% foo/bar
                -> { id : int }
                <- { name : string, rating : real, updateTime: date}
                """)

    def testValidRequest1(self):
         """
         Test match_request with matched data, should return true.

         Maps to test scenario module:llidl:row#346
         """
         self.assert_(self._suite.valid_request('foo/bar', {'id' : 123}))

    def testValidRequest2(self):
        """
         Test valid_request with unmatched data, should return false.

         Maps to test scenario module:llidl:row#347
        """
        self.assert_(self._suite.valid_request('foo/bar', {'id2' : 123}))

    def testValidRequest3(self):
        """
         Test valid_request with unmatched data, should return false.

         Maps to test scenario module:llidl:row#348
        """
        self.assert_(not self._suite.valid_request('foo/bar', {'id' : 'str'}))

    def testValidRequest4(self):
        """
         Test valid_request with unmatched data, should return false.

         Maps to test scenario module:llidl:row#349
        """
        self.assert_(self._suite.valid_request('foo/bar', {'id' : 123,
            'name' : 'bob'}))

    def testValidRequest5(self):
        """
         Test valid_request with unmatched data, should return false.

         Maps to test scenario module:llidl:row#350
        """
        self.assert_(not self._suite.valid_request('foo/bar', [123 , 123]))

    def testValidRequest6(self):
        """
         Test valid_request with unmatched data, should return false.

         Maps to test scenario module:llidl:row#351
        """
        try:
            self._suite.valid_request('none/resource', {123 : 123})
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testValidResponse1(self):
        """
        Test valid_response with matched data, should return true.

        Maps to test scenario module:llidl:row#353
        """
        self.assert_(self._suite.valid_response('foo/bar',
        {'name':'Jack', 'rating':1.82, 'updateTime':datetime.datetime.today()}))

    def testValidResponse2(self):
        """
        Test valid_response with unmatched data, should return false.

        Maps to test scenario module:llidl:row#354
        """
        self.assert_(not self._suite.valid_response('foo/bar',
        {'name':'Jack', 'rating':1.82, 'updateTime':False}))

    def testValidResponse3(self):
        """
        Test valid_response with unmatched data, should return false.

        Maps to test scenario module:llidl:row#355
        """
        self.assert_(not self._suite.valid_response('foo/bar',
        {'name':'Jack', 'rating':1.82, 'updateTime': 'today'}))

    def testValidResponse4(self):
        """
        Test valid_response with unmatched data, should return false.

        Maps to test scenario module:llidl:row#356
        """
        self.assert_(self._suite.valid_response('foo/bar',
        {'name':'Jack', 'rating':1.82, 'id' : 1001,
        'updateTime' : datetime.datetime.today()}))

    def testValidResponse5(self):
        """
        Test valid_response with unmatched data, should return false.

        Maps to test scenario module:llidl:row#357
        """
        self.assert_(not self._suite.valid_response('foo/bar',
        ['str', 'bob', 2323]))

    def testValidResponse6(self):
        """
         Test valid_response with unmatched resource name.
         MatchError should be raised.

         Maps to test scenario module:llidl:row#358
        """
        try:
            self._suite.match_request('none/resource', {123 : 123})
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testValidRequestFailure1(self):
        """
        Test valid_request with unmatched request data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#360
        """
        try:
            self._suite.valid_request('foo/bar', {'id' : [123]}, raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testValidRequestFailure2(self):
        """
        Test valid_request with unmatched request data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#361
        """
        try:
            self._suite.valid_request('foo/bar', {'id' : 'strdata'}, raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testValidRequestFailure3(self):
        """
        Test valid_request with unmatched request data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#362
        """
        try:
            self._suite.valid_request('foo/bar',
            [123 , 123], raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testValidResponseFailure1(self):
        """
        Test valid_response with unmatched response data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#363
        """
        try:
            self._suite.valid_response('foo/bar', {'name': 123, 'rating':1.82,
            'updateTime':False},raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testValidResponseFailure2(self):
        """
        Test valid_response with unmatched response data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#364
        """
        try:
            self._suite.valid_response('foo/bar', {'name':'Jack', 'rating':1.82,
            'updateTime':'today'},raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testValidResponseFailure3(self):
        """
        Test valid_response with unmatched response data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#365
        """
        try:
            self._suite.valid_response('foo/bar', [12, 12], raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

class LLIDLMatchTests(unittest.TestCase):
    """
    This class aggregates all the test cases for match_request
    and match_response.
    """
    def setUp(self):
        """
        Set up a suite instance for testing.
        """
        self._suite = llidl.parse_suite("""
                %% foo/bar
                -> { id : int }
                <- { name : string, rating : real, updateTime: date}
                """)

    def testMatchRequest1(self):
         """
         Test match_request with matched data, should return true.

         Maps to test scenario module:llidl:row#323
         """
         self.assert_(self._suite.match_request('foo/bar', {'id' : 123}))

    def testMatchRequest2(self):
        """
         Test match_request with unmatched data, should return false.

         Maps to test scenario module:llidl:row#324
        """
        self.assert_(not self._suite.match_request('foo/bar', {'id2' : 123}))

    def testMatchRequest3(self):
        """
         Test match_request with unmatched data, should return false.

         Maps to test scenario module:llidl:row#325
        """
        self.assert_(not self._suite.match_request('foo/bar', {'id2' : 'str'}))

    def testMatchRequest4(self):
        """
         Test match_request with unmatched data, should return false.

         Maps to test scenario module:llidl:row#326
        """
        self.assert_(not self._suite.match_request('foo/bar', {'id2' : 123,
            'name' : 'bob'}))

    def testMatchRequest5(self):
        """
         Test match_request with unmatched data, should return false.

         Maps to test scenario module:llidl:row#327
        """
        self.assert_(not self._suite.match_request('foo/bar', {123 : 123}))

    def testMatchRequest6(self):
        """
         Test match_request with unmatched data, should return false.

         Maps to test scenario module:llidl:row#327
        """
        try:
            self._suite.match_request('none/resource', {123 : 123})
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testMatchResponse1(self):
        """
        Test match_response with matched data, should return true.

        Maps to test scenario module:llidl:row#329
        """
        self.assert_(self._suite.match_response('foo/bar',
        {'name':'Jack', 'rating':1.82, 'updateTime':datetime.datetime.today()}))

    def testMatchResponse2(self):
        """
        Test match_response with unmatched data, should return false.

        Maps to test scenario module:llidl:row#330
        """
        self.assert_(not self._suite.match_response('foo/bar',
        {'name':'Jack', 'rating':1.82, 'updateDate':datetime.datetime.today()}))

    def testMatchResponse3(self):
        """
        Test match_response with unmatched data, should return false.

        Maps to test scenario module:llidl:row#331
        """
        self.assert_(not self._suite.match_response('foo/bar',
        {'name':'Jack', 'rating':1.82, 'updateTime': 'today'}))

    def testMatchResponse4(self):
        """
        Test match_response with unmatched data, should return false.

        Maps to test scenario module:llidl:row#332
        """
        self.assert_(not self._suite.match_response('foo/bar',
        {'name':'Jack', 'rating':1.82, 'id' : 1001,
        'updateTime' : datetime.datetime.today()}))

    def testMatchResponse5(self):
        """
        Test match_response with unmatched data, should return false.

        Maps to test scenario module:llidl:row#333
        """
        self.assert_(not self._suite.match_response('foo/bar',
        ['str', 'bob', 2323]))

    def testMatchResponse6(self):
        """
         Test match_response with unmatched resource name.
         MatchError should be raised.

         Maps to test scenario module:llidl:row#334
        """
        try:
            self._suite.match_request('none/resource', {123 : 123})
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testMatchRequestFailure1(self):
        """
        Test match_request with unmatched request data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#337
        """
        try:
            self._suite.match_request('foo/bar', {'ids' : 123}, raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testMatchRequestFailure2(self):
        """
        Test match_request with unmatched request data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#338
        """
        try:
            self._suite.match_request('foo/bar', {'id' : 'strdata'}, raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testMatchRequestFailure3(self):
        """
        Test match_request with unmatched request data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#339
        """
        try:
            self._suite.match_request('foo/bar',
            {'id' : 'strdata', 'name' : 'bob'}, raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testMatchRequestFailure4(self):
        """
        Test match_request with unmatched request data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#340
        """
        try:
            self._suite.match_request('foo/bar',
            [123 , 123], raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testMatchResponseFailure1(self):
        """
        Test match_response with unmatched response data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#341
        """
        try:
            self._suite.match_response('foo/bar', {'name':'Jack', 'rating':1.82,
            'updateDate':datetime.datetime.today()},raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testMatchResponseFailure2(self):
        """
        Test match_response with unmatched response data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#342
        """
        try:
            self._suite.match_response('foo/bar', {'name':'Jack', 'rating':1.82,
            'updateTime':'today'},raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass

    def testMatchResponseFailure3(self):
        """
        Test match_response with unmatched response data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#343
        """
        try:
            self._suite.match_response('foo/bar', {'name':'Jack', 'rating':1.82,
            'updateTime':datetime.datetime.today(), 'id' : 's'},raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass



    def testMatchResponseFailure4(self):
        """
        Test match_response with unmatched response data and raises=MatchError.
        MatchError should be raised.

        Maps to test scenario module:llidl:row#344
        """
        try:
            self._suite.match_response('foo/bar', [12, 12], raises=MatchError)
            self.fail("MatchError should be raised to indicate this.")
        except MatchError:
            pass
        

# Below is the original tests before this competition, leave as legacy.

class LLIDLParsingTests(unittest.TestCase):
    def good_parse_value(self, s):
        try:
            v = llidl.parse_value(s)
        except llidl.ParseError as e:
            self.fail('Failed parsing "%s", %s' % (s, str(e)))

    def bad_parse_value(self, s, msg=None, line=None, char=None):
        try:
            v = llidl.parse_value(s)
            self.fail('Incorrectly parsed "%s" as valid' % s)
        except llidl.ParseError as e:
            if msg and msg not in str(e):
                self.fail('Mising "%s" in "%s"' % (msg, str(e)))
            if line:
                self.assertEqual(e.line, line)
            if char:
                self.assertEqual(e.char, char)
            pass

    def test_parse_simple(self):
        # good and bad type names
        for w in 'undef bool int real string uri date uuid binary'.split():
            self.good_parse_value(w)
        for w in 'blob Bool BOOL # * _'.split():
            self.bad_parse_value(w)

        # good and bad selectors
        for w in 'true false 0 1 42 1000000 "red" "blue" "a/b/c_d"'.split():
            self.good_parse_value(w)
        for w in '3.14159 -10 2x2 0x3f "" "a-b" "3" "~boo~" "feh'.split():
            self.bad_parse_value(w)

    def test_whitespace(self):
        for w in ['[ real]', '[\treal]', '[  real]', '[\t\treal]']:
            self.good_parse_value(w)
        for nl in ['\n', '\r\n', '\r', '\n\n']:
            w = ('[%s\tint,%s\tbool, ;comment and stuff!!%s\tstring%s]'
                    % (nl, nl, nl, nl))
            self.good_parse_value(w)

    def test_bad_whitespace(self):
        # parse_value() expects the value to be the entire string,
        #   other, larger, parsing constructs consume the surrounding whitespace
        self.bad_parse_value("")
        self.bad_parse_value(" ")
        self.bad_parse_value(" int")
        self.bad_parse_value("int ")

    def test_array_spacing(self):
        for w in ['[int,bool]', '[ int,bool]', '[int ,bool]',
                    '[int, bool]', '[int,bool ]']:
            self.good_parse_value(w)
        for w in ['[int,...]', '[ int,...]', '[int ,...]',
                    '[int, ...]', '[int,... ]']:
            self.good_parse_value(w)

    def test_array_commas(self):
        v = llidl.parse_value('[int]')
        self.assert_(v.match([1]));
        self.assert_(v.has_additional([1,2]));
        v = llidl.parse_value('[int,]')
        self.assert_(v.match([1]));
        self.assert_(v.has_additional([1,2]));
        v = llidl.parse_value('[int,int]')
        self.assert_(v.has_defaulted([1]));
        self.assert_(v.match([1,2]));
        self.assert_(v.has_additional([1,2,3]));
        v = llidl.parse_value('[int,int,]')
        self.assert_(v.has_defaulted([1]));
        self.assert_(v.match([1,2]));
        self.assert_(v.has_additional([1,2,3]));

    def test_empty_array(self):
        self.bad_parse_value('[]')
        self.bad_parse_value('[ ]')
        self.bad_parse_value('[...]')
        self.bad_parse_value('[ ... ]')

    def test_malformed_array(self):
        self.bad_parse_value('[int');
        self.bad_parse_value('[ bool int ]');
        self.bad_parse_value('[ bool, , int]');
        self.bad_parse_value('[ bool, int, ... string]');

    def test_map_spacing(self):
        for w in ['{a:int,b:int}', '{ a:int,b:int}', '{a :int,b:int}',
                    '{a: int,b:int}', '{a:int ,b:int}', '{a:int, b:int}',
                    '{a:int,b :int}', '{a:int,b: int}', '{a:int,b:int }']:
            self.good_parse_value(w)
        for w in ['{$:int}', '{ $:int}', '{$ :int}', '{$: int}', '{$:int }']:
            self.good_parse_value(w)

    def test_map_commas(self):
        v = llidl.parse_value('{a:int}')
        self.assert_(v.match({'a':1}));
        self.assert_(v.has_additional({'a':1,'b':2}));
        v = llidl.parse_value('{a:int,}')
        self.assert_(v.match({'a':1}));
        self.assert_(v.has_additional({'a':1,'b':2}));
        v = llidl.parse_value('{a:int,b:int}')
        self.assert_(v.has_defaulted({'a':1}));
        self.assert_(v.match({'a':1,'b':2}));
        self.assert_(v.has_additional({'a':1,'b':2,'c':3}));
        v = llidl.parse_value('{a:int,b:int,}')
        self.assert_(v.has_defaulted({'a':1}));
        self.assert_(v.match({'a':1,'b':2}));
        self.assert_(v.has_additional({'a':1,'b':2,'c':3}));

    def test_empty_map(self):
        self.bad_parse_value('{}')
        self.bad_parse_value('{ }')

    def test_malformed_map(self):
        self.bad_parse_value('{')
        self.bad_parse_value('{a}')
        self.bad_parse_value('{a:}')
        self.bad_parse_value('{:int}')
        self.bad_parse_value('{int}')
        self.bad_parse_value('{a:int,')
        self.bad_parse_value('{alpha-omega:real}')
        self.bad_parse_value('{alpha/omega:reel}')
        self.bad_parse_value('{$}')
        self.bad_parse_value('{$:}')

    def test_error_messsages(self):
        self.bad_parse_value('""', 'expected name', char=2)
        self.bad_parse_value('"3"', 'expected name', char=2)
        self.bad_parse_value('"feh', 'expected close quote', char=5)
        self.bad_parse_value('[]', 'empty array', char=3)
        self.bad_parse_value('[int', 'expected close bracket', char=5)
        self.bad_parse_value('[int,,bool]', 'expected close bracket', char=6)
        self.bad_parse_value('{}', 'empty map', char=3)
        self.bad_parse_value('{a int}', 'expected colon', char=4)
        self.bad_parse_value('{a:,b:int}', 'expected value', char=4)
    
    def test_line_reporting(self):
        # line   1-2--------3---------45-------------------6-------7
        # char   1 1-234567 1-2345678  1-23456789012345678 1-2345 1
        lines = "{ \ta:int, \tb:bool,  \tc:string,;comment \td::3 }".split(' ')
        for nl in ['\n', '\r\n', '\r']:
            self.bad_parse_value(nl.join(lines), line=6, char=4)

class LLIDLSuiteTests(unittest.TestCase):
    def test_suite(self):
        suite = llidl.parse_suite(""";test suite
%% agent/name
-> { agent_id: uuid }
<- { first: string, last: string }

%% region/hub
-> { region_id: uuid }
<- { loc: [ real, real, real ] }

%% event_record
-> { log: string, priority: int }
<- undef

%% motd
-> undef
<- { message: string }
""")
        self.assert_(
            suite.match_request('agent/name', { 'agent_id': _uuid() }))
        self.assert_(
            suite.match_response('agent/name', { 'first':'Amy', 'last':'Ant' }))
            
        self.assert_(
            suite.match_request('region/hub', { 'region_id': str(_uuid()) }))
        self.assert_(
            suite.match_response('region/hub', { 'loc': [128,128,24] }))

        self.assert_(
            suite.valid_request('event_record', { 'log': 'Beep-Beep-Beep' }))
        self.assert_(
            suite.match_response('event_record', 12345))
        
        self.assert_(
            suite.match_request('motd', "please"))
        self.assert_(
            suite.valid_response('motd',
                { 'message': "To infinity, and beyond!",
                    'author': ["Buzz", "Lightyear"] } ))

    def test_variants(self):
        suite = llidl.parse_suite(""";variant suite
%% object/info
-> undef
<- { name: string, pos: [ real, real, real ], geom: &geometry }

&geometry = { type: "sphere", radius: real }
&geometry = { type: "cube", side: real }
&geometry = { type: "prisim", faces: int, twist: real }
""")

        p = [ 128.0, 128.0, 26.0 ]
        self.assert_(
            suite.match_response('object/info',
                { 'name': 'ball', 'pos': p, 'geom':
                    { 'type': 'sphere', 'radius': 2.2 } }))
        self.assert_(
            suite.match_response('object/info',
                { 'name': 'box', 'pos': p, 'geom':
                    { 'type': 'cube', 'side': 2.2 } }))
        self.assert_(
            suite.match_response('object/info',
                { 'name': 'lith', 'pos': p, 'geom':
                    { 'type': 'prisim', 'faces': 3, 'twist': 2.2 } }))
        self.failIf(
            suite.valid_response('object/info',
                { 'name': 'blob', 'pos': p, 'geom':
                    { 'type': 'mesh', 'verticies': [ 1, 2, 3, 4 ] } }))
        

class LLIDLExceptionTests(unittest.TestCase):
    def test_value_exceptions(self):
        v = llidl.parse_value("{ size: int }")
        v.match({'size': 42}, raises=True) # shouldn't raise MatchError
        v.valid({'size': 42}, raises=True) # shouldn't raise MatchError
        
        self.assertRaises(llidl.MatchError,
            v.match, {'size': 'large'}, raises=True)
        self.assertRaises(llidl.MatchError,
            v.valid, {'size': 'large'}, raises=True)

        self.assertRaises(UserWarning,
            v.match, {'size': 'large'}, raises=UserWarning)
        self.assertRaises(UserWarning,
            v.match, {'size': 'large'}, raises=UserWarning("blah"))
    
    def test_suite_exceptions(self):
        s = llidl.parse_suite("%% message -> { id: uuid } <- { size: int }")
        s.match_request('message', {'id': _uuid()}, raises=True)
        s.valid_request('message', {'id': _uuid()}, raises=True)
        s.match_response('message', {'size': 42}, raises=True)
        s.valid_response('message', {'size': 42}, raises=True)
            # these shouldn't raise MatchError

        self.assertRaises(llidl.MatchError,
            s.match_request, 'message', {'id': 'katamari'}, raises=True)
        self.assertRaises(llidl.MatchError,
            s.valid_request, 'message', {'id': 'katamari'}, raises=True)
        self.assertRaises(llidl.MatchError,
            s.match_response, 'message', {'size': 'large'}, raises=True)
        self.assertRaises(llidl.MatchError,
            s.valid_response, 'message', {'size': 'large'}, raises=True)

        self.assertRaises(UserWarning,
            s.match_response, 'message', {'size': 'large'}, raises=UserWarning)
        self.assertRaises(UserWarning,
            s.match_response, 'message', {'size': 'large'},
                                raises=UserWarning("blah"))

    def test_suite_unknown_api(self):
        s = llidl.parse_suite("%% message -> { id: string } <- { size: int }")
        self.assertRaises(llidl.MatchError,
            s.match_request, 'some_api', {'id': 'bob'})
        try:
            s.match_request('some_api', {'id': 'bob'})
            self.fail("should have raised an exception")
        except Exception as me:
            self.assertEqual(str(me),
                "Resource name 'some_api' not found in suite.")
            
class LLIDLReportingTests(unittest.TestCase):
    __test__ = False
    def x_test_detail(self):
        """not yet implemented"""
        v = llidl.parse_value("{ size: int }")
        match = v.match({'size': 'large'})
        self.assertFalse(match)
        self.assertEqual(match.detail(),
            "size: string 'large' not convertible to int")

class LLIDLFileTests(unittest.TestCase):
    def test_parse_value_from_file(self):
        file = io.StringIO(u"[ int, int ]")
        v = llidl.parse_value(file)
        self.assert_(v.match([1,2]))
        self.assert_(v.incompatible(["one", "two"]))
        
    def test_parse_suite_from_file(self):
        file = io.StringIO(u""";test suite
%% agent/name
-> { agent_id: uuid }
<- { first: string, last: string }
""")
        suite = llidl.parse_suite(file)
        self.assert_(
            suite.match_request('agent/name', { 'agent_id': _uuid() }))
        self.assert_(
            suite.match_response('agent/name', { 'first':'Amy', 'last':'Ant' }))

if __name__ == '__main__':
    unittest.main()


