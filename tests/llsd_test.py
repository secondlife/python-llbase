#!/usr/bin/env python
"""\
@file llsd_test.py
@brief Types as well as parsing and formatting functions for handling LLSD.

$LicenseInfo:firstyear=2006&license=mit$

Copyright (c) 2006-2009, Linden Research, Inc.

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

from itertools import islice
from datetime import datetime, tzinfo, timedelta, date
import pprint
import re
import unittest
import uuid
import struct

from llbase import llsd
from llbase import llsd_fuzz

class Foo(object):
    pass


def tuples2lists(s):
    if isinstance(s, tuple):
        s = list(s)
    if isinstance(s, list):
        for i,x in enumerate(s):
            s[i] = tuples2lists(x)
    if isinstance(s, dict):
        for k,v in s.iteritems():
            s[k] = tuples2lists(v)
    return s

sample_llsd_object = {'a':{'a1':12, 'a2':123.45}, 'b':[1234555, None],
                      'c':"this is some xml: <xml> &amp;",
                      'd':['a','small','little','text']}

class TestBase(unittest.TestCase):
    def assertEqualsPretty(self, a, b):
        try:
            self.assertEquals(a,b)
        except AssertionError:
            self.fail("\n%s\n !=\n%s" % (pprint.pformat(a), pprint.pformat(b)))
    
    def assertEqualsIgnoringTuples(self, a, b):
        """ Like assertEquals, but ignores tuples converted to lists and vice-versa."""
        try:
            self.assertEqualsPretty(a,b)
        except AssertionError:
            # try again but after converting tuples to lists
            a = tuples2lists(a)
            b = tuples2lists(b)
            self.assertEqualsPretty(a,b)

    def fuzz_parsing_base(self, fuzz_method_name, legit_exceptions):
        fuzzer = llsd_fuzz.LLSDFuzzer()
        print "Seed is", repr(fuzzer.seed)
        fuzz_method = getattr(fuzzer, fuzz_method_name)
        for f in islice(fuzz_method(sample_llsd_object), 1000):
            try:
                #print "f", repr(f)
                parsed = llsd.parse(f)
            except legit_exceptions:
                pass  # expected, since many of the inputs will be invalid
            except Exception, e:
                print "Raised exception", e.__class__
                print "Fuzzed value was", repr(f)
                raise

    def fuzz_roundtrip_base(self, formatter_method, recompare_func=None):
        fuzzer = llsd_fuzz.LLSDFuzzer()
        print "Seed is", repr(fuzzer.seed)
        for f in islice(fuzzer.structure_fuzz(sample_llsd_object), 1000):
            try:
                try:
                    text = formatter_method(f)
                except llsd.LLSDSerializationError:
                    # sometimes the fuzzer will generate invalid llsd
                    continue
                parsed = llsd.parse(text)
                try:
                    self.assertEqualsIgnoringTuples(parsed, f)
                except AssertionError:
                    if recompare_func:
                        recompare_func(parsed, f)
                    else:
                        raise
            except llsd.LLSDParseError:
                print "Failed to parse", repr(text)
                raise

class LLSDNotationUnitTest(TestBase):
    mode = 'static'
    def setUp(self):
        self.llsd = llsd.LLSD()

    def strip(self, the_string):
        return re.sub('\s', '', the_string)

    def assert_notation_roundtrip(self, py_in, str_in, is_alternate_notation=False):
        py_out = self.llsd.parse(str_in)
        str_out = self.llsd.as_notation(py_in)
        py_roundtrip = self.llsd.parse(str_out)
        str_roundtrip = self.llsd.as_notation(py_out)
        self.assertEqual(py_in, py_out)
        self.assertEqual(py_in, py_roundtrip)

        # If str_in is an alternate notation, we can't compare it directly.
        if not is_alternate_notation:
            self.assertEqual(self.strip(str_out), self.strip(str_in))
        self.assertEqual(self.strip(str_out), self.strip(str_roundtrip))

    def testMap(self):
        map_notation = "{'foo':'bar'}"
        map_within_map_notation = "{'foo':'bar','doo':{'goo':'poo'}}"
        blank_map_notation = "{}"

        python_map = {"foo":"bar"}
        python_map_within_map = {"foo":"bar", "doo":{"goo":"poo"}}

        self.assert_notation_roundtrip(python_map, map_notation)
        self.assert_notation_roundtrip(python_map_within_map,
                                             map_within_map_notation)
        self.assert_notation_roundtrip({}, blank_map_notation)

    def testArray(self):
        array_notation = "['foo', 'bar']"
        array_within_array_notation = "['foo', 'bar',['foo', 'bar']]"
        blank_array_notation = "[]"

        python_array = ["foo", "bar"]
        python_array_within_array = ["foo", "bar",["foo", "bar"]]

        self.assert_notation_roundtrip(python_array, array_notation)
        self.assert_notation_roundtrip(python_array_within_array,
                                             array_within_array_notation)
        self.assert_notation_roundtrip([], blank_array_notation)

    def testString(self):
        sample_data = [('have a nice day',"'have a nice day'"),
                       ('have a nice day','"have a nice day"'),
                       ('have a nice day','s(15)"have a nice day"'),
                       ('have a "nice" day','\'have a "nice" day\''),
                       ('have a "nice" day','"have a \\"nice\\" day"'),
                       ('have a "nice" day','s(17)"have a "nice" day"'),
                       ("have a 'nice' day","'have a \\'nice\\' day'"),
                       ("have a 'nice' day",'"have a \'nice\' day"'),
                       ("have a 'nice' day",'s(17)"have a \'nice\' day"'),
                       ("Kanji: '\xe5\xb0\x8f\xe5\xbf\x83\xe8\x80\x85'", 
                       "'Kanji: \\'\xe5\xb0\x8f\xe5\xbf\x83\xe8\x80\x85\\''"),
                       ("Kanji: '\xe5\xb0\x8f\xe5\xbf\x83\xe8\x80\x85'", 
                       "\"Kanji: '\\xe5\\xb0\\x8f\\xe5\\xbf\\x83\\xe8\\x80\\x85'\"")
                 ]
        for py, notation in sample_data:
            is_alternate_notation = False
            if notation[0] != "'":
                is_alternate_notation = True
            self.assert_notation_roundtrip(py, notation, is_alternate_notation)

    def testInteger(self):
        ## TODO test <integer />
        pos_int_notation = "i289343"
        neg_int_notation = "i-289343"
        blank_int_notation = "i0"

        python_pos_int = 289343
        python_neg_int = -289343

        self.assert_notation_roundtrip(python_pos_int,
                                             pos_int_notation)
        self.assert_notation_roundtrip(python_neg_int,
                                             neg_int_notation)
        self.assertEqual(0, self.llsd.parse(blank_int_notation))

    def testReal(self):
        pos_real_notation = "r2983287453.3"
        neg_real_notation = "r-2983287453.3"
        blank_real_notation = "r0"

        python_pos_real = 2983287453.3
        python_neg_real = -2983287453.3

        self.assert_notation_roundtrip(python_pos_real,
                                             pos_real_notation)
        self.assert_notation_roundtrip(python_neg_real,
                                             neg_real_notation)
        self.assertEqual(0, self.llsd.parse(blank_real_notation))

    def testBoolean(self):
        sample_data = [(True,"TRUE"),
                       (True,"true"),
                       (True,"T"),
                       (True,"t"),
                       (True,"1"),
                       (False,"FALSE"),
                       (False,"false"),
                       (False,"F"),
                       (False,"f"),
                       (False,"0")
                 ]
        for py, notation in sample_data:
            is_alternate_notation = False
            if notation not in ("true", "false"):
                is_alternate_notation = True
            self.assert_notation_roundtrip(py, notation, is_alternate_notation)

        blank_notation = ""
        self.assertEqual(False, self.llsd.parse(blank_notation))

    def testDate(self):
        valid_date_notation = 'd"2006-02-01T14:29:53.460000Z"'
        valid_date_notation_no_float = 'd"2006-02-01T14:29:53Z"'
        valid_date_notation_zero_seconds = 'd"2006-02-01T14:29:00Z"'
        valid_date_notation_filled = 'd"2006-02-01T14:29:05Z"'

        blank_date_notation = 'd""'

        python_valid_date = datetime(2006, 2, 1, 14, 29, 53, 460000)
        python_valid_date_no_float = datetime(2006, 2, 1, 14, 29, 53)
        python_valid_date_zero_seconds = datetime(2006, 2, 1, 14, 29, 0)
        python_valid_date_filled = datetime(2006, 2, 1, 14, 29, 05)

        python_blank_date = datetime(1970, 1, 1)

        self.assert_notation_roundtrip(python_valid_date,
                                       valid_date_notation)
        self.assert_notation_roundtrip(python_valid_date_no_float,
                                       valid_date_notation_no_float)
        self.assert_notation_roundtrip(python_valid_date_zero_seconds,
                                       valid_date_notation_zero_seconds)
        self.assert_notation_roundtrip(python_valid_date_filled,
                                       valid_date_notation_filled)

        self.assert_notation_roundtrip(python_valid_date_filled,
                                       valid_date_notation_filled)

        self.assertEqual(python_blank_date, self.llsd.parse(blank_date_notation))

    #def testBinary(self):
    #    sample_data = [("the quick brown fox",'b(??)"???"'),
    #                   ("the quick brown fox",'b64"dGhlIHF1aWNrIGJyb3duIGZveA=="'),
    #                   ("the quick brown fox",'b16"???"'),
    #                   ("", 'b(0)""'),
    #                   ("", 'b64""'),
    #                   ("", 'b16""')
    #             ]

    #    for py, notation in sample_data:
    #        is_alternate_notation = False
    #        if notation not in ("true", "false"):
    #            is_alternate_notation = True
    #        self.assert_notation_roundtrip(py, notation, is_alternate_notation)

    #    self.assertEqual(False, self.llsd.parse(blank_notation))

    #    # <binary /> should return blank binary blob... in python I guess this is just nil
    #    python_binary = llsd.binary("the quick brown fox")
    #    self.assert_notation_roundtrip(python_binary,
    #                                         base64_binary_notation)

    def testUUID(self):
        uuid_tests = {
            uuid.UUID(hex='d7f4aeca-88f1-42a1-b385-b9db18abb255'):"ud7f4aeca-88f1-42a1-b385-b9db18abb255",
            uuid.UUID(hex='00000000-0000-0000-0000-000000000000'):"u00000000-0000-0000-0000-000000000000"
}

        for py, notation in uuid_tests.items():
            self.assert_notation_roundtrip(py, notation)

    def testURI(self):
        uri_tests = {
            llsd.uri('http://sim956.agni.lindenlab.com:12035/runtime/agents'):'l"http://sim956.agni.lindenlab.com:12035/runtime/agents"',
            llsd.uri('http://sim956.agni.lindenlab.com:12035/runtime/agents'):"l'http://sim956.agni.lindenlab.com:12035/runtime/agents'"}

        blank_uri_notation = 'l""'

        for py, notation in uri_tests.items():
            is_alternate_notation = False
            if notation[1] != '"':
                is_alternate_notation = True
            self.assert_notation_roundtrip(py, notation, is_alternate_notation)
        self.assertEqual(None, self.llsd.parse(blank_uri_notation))

    def testUndefined(self):
        undef_notation = "!"
        self.assert_notation_roundtrip(None, undef_notation)

    def test_llsd_serialization_exception(self):
        # make an object not supported by llsd
        python_native_obj = Foo()

        # assert than an exception is raised
        self.assertRaises(TypeError, self.llsd.as_notation, python_native_obj)
        self.assertRaises(llsd.LLSDParseError, self.llsd.parse, '2')
        
    def test_fuzz_parsing(self):
        self.fuzz_parsing_base('notation_fuzz',
            (llsd.LLSDParseError, IndexError, ValueError))
    
    def test_fuzz_roundtrip(self):
        self.fuzz_roundtrip_base(llsd.format_notation)


class LLSDXMLUnitTest(TestBase):
    mode = 'static'
    def setUp(self):
        self.llsd = llsd.LLSD()

    def assert_xml_roundtrip(self, py, xml):
        parsed_py = self.llsd.parse(xml)
        formatted_xml = self.llsd.as_xml(py)
        self.assertEqual(parsed_py, py)
        self.assertEqual(self.strip(formatted_xml),
                         self.strip(xml))
        self.assertEqual(py, self.llsd.parse(formatted_xml))
        self.assertEqual(self.strip(xml),
                         self.strip(self.llsd.as_xml(parsed_py)))

    def test_cllsd(self):
        import sys
        if not sys.platform.lower().startswith('win'):
            self.assert_(llsd.cllsd is not None)

    def testMap(self):
        map_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<map>\
<key>foo</key>\
<string>bar</string>\
</map>\
</llsd>"

        map_within_map_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<map>\
<key>foo</key>\
<string>bar</string>\
<key>doo</key>\
<map>\
<key>goo</key>\
<string>poo</string>\
</map>\
</map>\
</llsd>"

        blank_map_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<map />\
</llsd>"

        python_map = {"foo":"bar"}
        python_map_within_map = {"foo":"bar", "doo":{"goo":"poo"}}

        self.assert_xml_roundtrip(python_map, map_xml)
        self.assert_xml_roundtrip(python_map_within_map,
                                             map_within_map_xml)
        self.assert_xml_roundtrip({}, blank_map_xml)

    def testArray(self):
        array_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array>\
<string>foo</string>\
<string>bar</string>\
</array>\
</llsd>"

        array_within_array_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array>\
<string>foo</string>\
<string>bar</string>\
<array>\
<string>foo</string>\
<string>bar</string>\
</array>\
</array>\
</llsd>"

        blank_array_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array />\
</llsd>"

        python_array = ["foo", "bar"]
        python_array_within_array = ["foo", "bar",["foo", "bar"]]

        self.assert_xml_roundtrip(python_array, array_xml)
        self.assert_xml_roundtrip(python_array_within_array,
                                             array_within_array_xml)
        self.assert_xml_roundtrip([], blank_array_xml)

    def testString(self):
        sample_data = {'foo':"\
<?xml version=\"1.0\" ?>\
<llsd>\
<string>foo</string>\
</llsd>",
                 '':"\
<?xml version=\"1.0\" ?>\
<llsd>\
<string />\
</llsd>",
                 '<xml>&ent;</xml>':"\
<?xml version=\"1.0\" ?>\
<llsd>\
<string>&lt;xml&gt;&amp;ent;&lt;/xml&gt;</string>\
</llsd>"         
                 }
        for py, xml in sample_data.items():
            self.assert_xml_roundtrip(py, xml)

    def testInteger(self):
        ## TODO test <integer />
        pos_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer>289343</integer>\
</llsd>"

        neg_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer>-289343</integer>\
</llsd>"

        blank_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer />\
</llsd>"

        python_pos_int = 289343
        python_neg_int = -289343

        self.assert_xml_roundtrip(python_pos_int,
                                             pos_int_xml)
        self.assert_xml_roundtrip(python_neg_int,
                                             neg_int_xml)
        self.assertEqual(0, self.llsd.parse(blank_int_xml))

    def testReal(self):
        ## TODO test <real />
        pos_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real>2983287453.3000002</real>\
</llsd>"

        neg_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real>-2983287453.3000002</real>\
</llsd>"

        blank_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real />\
</llsd>"

        python_pos_real = 2983287453.3
        python_neg_real = -2983287453.3

        self.assert_xml_roundtrip(python_pos_real,
                                             pos_real_xml)
        self.assert_xml_roundtrip(python_neg_real,
                                             neg_real_xml)
        self.assertEqual(0, self.llsd.parse(blank_real_xml))

    def testBoolean(self):
        true_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean>true</boolean>\
</llsd>"

        false_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean>false</boolean>\
</llsd>"

        blank_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean />\
</llsd>"

        self.assert_xml_roundtrip(True, true_xml)
        self.assert_xml_roundtrip(False, false_xml)
        self.assertEqual(False, self.llsd.parse(blank_xml))

    def testDate(self):
        valid_date_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<date>2006-02-01T14:29:53.460000Z</date>\
</llsd>"

        valid_date_xml_no_fractional = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<date>2006-02-01T14:29:53Z</date>\
</llsd>"
        valid_date_xml_filled ="\
<?xml version=\"1.0\" ?>\
<llsd>\
<date>2006-02-01T14:29:05Z</date>\
</llsd>"

        blank_date_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<date />\
</llsd>"


        python_valid_date = datetime(2006, 2, 1, 14, 29, 53, 460000)
        python_valid_date_no_fractional = datetime(2006, 2, 1, 14, 29, 53)
        python_valid_date_filled = datetime(2006, 2, 1, 14, 29, 05)
        python_blank_date = datetime(1970, 1, 1)
        self.assert_xml_roundtrip(python_valid_date,
                                  valid_date_xml)
        self.assert_xml_roundtrip(python_valid_date_no_fractional,
                                  valid_date_xml_no_fractional)
        self.assert_xml_roundtrip(python_valid_date_filled,
                                  valid_date_xml_filled)
        self.assertEqual(python_blank_date, self.llsd.parse(blank_date_xml))

    def testBinary(self):
        base64_binary_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<binary>dGhlIHF1aWNrIGJyb3duIGZveA==</binary>\
</llsd>"

        # <binary /> should return blank binary blob... in python I guess this is just nil
        python_binary = llsd.binary("the quick brown fox")
        self.assert_xml_roundtrip(python_binary,
                                             base64_binary_xml)

    def testUUID(self):
        uuid_tests = {
            uuid.UUID(hex='d7f4aeca-88f1-42a1-b385-b9db18abb255'):"\
<?xml version=\"1.0\" ?>\
<llsd>\
<uuid>d7f4aeca-88f1-42a1-b385-b9db18abb255</uuid>\
</llsd>",
            uuid.UUID(int=0):"\
<?xml version=\"1.0\" ?>\
<llsd>\
<uuid />\
</llsd>"}

        for py, xml in uuid_tests.items():
            self.assert_xml_roundtrip(py, xml)

    def testURI(self):
        uri_tests = {
            llsd.uri('http://sim956.agni.lindenlab.com:12035/runtime/agents'):"\
<?xml version=\"1.0\" ?>\
<llsd>\
<uri>http://sim956.agni.lindenlab.com:12035/runtime/agents</uri>\
</llsd>"}

        blank_uri_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<uri />\
</llsd>"

        for py, xml in uri_tests.items():
            self.assert_xml_roundtrip(py, xml)
        self.assertEqual('', self.llsd.parse(blank_uri_xml))

    def testUndefined(self):
        undef_xml = "<?xml version=\"1.0\" ?><llsd><undef /></llsd>"
        self.assert_xml_roundtrip(None, undef_xml)

    def test_llsd_serialization_exception(self):
        # make an object not supported by llsd
        python_native_obj = Foo()

        # assert than an exception is raised
        self.assertRaises(TypeError, self.llsd.as_xml, python_native_obj)


    def strip(self, the_string):
        return re.sub('\s', '', the_string)        

class LLSDBinaryUnitTest(TestBase):
    mode = 'static'
    def setUp(self):
        self.llsd = llsd.LLSD()

    def roundTrip(self, something):
        binary = self.llsd.as_binary(something)
        return self.llsd.parse(binary)

    def testMap(self):
        map_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<map>\
<key>foo</key>\
<string>bar</string>\
</map>\
</llsd>"

        map_within_map_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<map>\
<key>foo</key>\
<string>bar</string>\
<key>doo</key>\
<map>\
<key>goo</key>\
<string>poo</string>\
</map>\
</map>\
</llsd>"

        blank_map_xml = "\
<llsd>\
<map />\
</llsd>"

        python_map = {"foo":"bar"}
        python_map_within_map = {"foo":"bar", "doo":{"goo":"poo"}}

        self.assertEqual(python_map, self.roundTrip(self.llsd.parse(map_xml)))
        self.assertEqual(
            python_map_within_map,
            self.roundTrip(self.llsd.parse(map_within_map_xml)))
        self.assertEqual({}, self.roundTrip(self.llsd.parse(blank_map_xml)))

    def testArray(self):
        array_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array>\
<string>foo</string>\
<string>bar</string>\
</array>\
</llsd>"
        array_within_array_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array>\
<string>foo</string>\
<string>bar</string>\
<array>\
<string>foo</string>\
<string>bar</string>\
</array>\
</array>\
</llsd>"
        blank_array_xml = "\
<llsd>\
<array />\
</llsd>"

        python_array = ["foo", "bar"]
        python_array_within_array = ["foo", "bar",["foo", "bar"]]

        self.assertEqual(
            python_array,
            self.roundTrip(self.llsd.parse(array_xml)))
        self.assertEqual(
            python_array_within_array,
            self.roundTrip(self.llsd.parse(array_within_array_xml)))
        self.assertEqual(
            [],
            self.roundTrip(self.llsd.parse(blank_array_xml)))

    def testString(self):
        normal_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<string>foo</string>\
</llsd>"

        blank_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<string />\
</llsd>"

        self.assertEqual("foo", self.roundTrip(self.llsd.parse(normal_xml)))
        self.assertEqual("", self.roundTrip(self.llsd.parse(blank_xml)))

    def testInteger(self):
        ## TODO test <integer />
        pos_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer>289343</integer>\
</llsd>"

        neg_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer>-289343</integer>\
</llsd>"

        blank_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer />\
</llsd>"

        python_pos_int = 289343
        python_neg_int = -289343

        self.assertEqual(
            python_pos_int,
            self.roundTrip(self.llsd.parse(pos_int_xml)))
        self.assertEqual(
            python_neg_int,
            self.roundTrip(self.llsd.parse(neg_int_xml)))
        self.assertEqual(
            0,
            self.roundTrip(self.llsd.parse(blank_int_xml)))

    def testReal(self):
        pos_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real>2983287453.3</real>\
</llsd>"

        neg_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real>-2983287453.3</real>\
</llsd>"

        blank_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real />\
</llsd>"

        python_pos_real = 2983287453.3
        python_neg_real = -2983287453.3

        self.assertEqual(
            python_pos_real,
            self.roundTrip(self.llsd.parse(pos_real_xml)))
        self.assertEqual(
            python_neg_real,
            self.roundTrip(self.llsd.parse(neg_real_xml)))
        self.assertEqual(
            0,
            self.roundTrip(self.llsd.parse(blank_real_xml)))

    def testBoolean(self):
        true_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean>true</boolean>\
</llsd>"

        false_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean>false</boolean>\
</llsd>"

        blank_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean />\
</llsd>"

        self.assertEqual(True, self.roundTrip(self.llsd.parse(true_xml)))
        self.assertEqual(False, self.roundTrip(self.llsd.parse(false_xml)))
        self.assertEqual(False, self.roundTrip(self.llsd.parse(blank_xml)))

    def testDate(self):
        valid_date_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<date>2006-02-01T14:29:53Z</date>\
</llsd>"

        blank_date_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<date />\
</llsd>"
        python_valid_date = datetime(2006, 2, 1, 14, 29, 53)
        python_blank_date = datetime(1970, 1, 1)

        self.assertEqual(
            python_valid_date,
            self.roundTrip(self.llsd.parse(valid_date_xml)))
        self.assertEqual(
            python_blank_date,
            self.roundTrip(self.llsd.parse(blank_date_xml)))

    def testBinary(self):
        base64_binary_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<binary>dGhlIHF1aWNrIGJyb3duIGZveA==</binary>\
</llsd>"

        foo = self.llsd.parse(base64_binary_xml)
        self.assertEqual(
            llsd.binary("the quick brown fox"),
            self.roundTrip(foo))

    def testUUID(self):
        valid_uuid_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<uuid>d7f4aeca-88f1-42a1-b385-b9db18abb255</uuid>\
</llsd>"
        blank_uuid_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<uuid />\
</llsd>"
        self.assertEqual(
            'd7f4aeca-88f1-42a1-b385-b9db18abb255',
            self.roundTrip(str(self.llsd.parse(valid_uuid_xml))))
        self.assertEqual(
            '00000000-0000-0000-0000-000000000000',
            self.roundTrip(str(self.llsd.parse(blank_uuid_xml))))

    def testURI(self):
        valid_uri_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<uri>http://sim956.agni.lindenlab.com:12035/runtime/agents</uri>\
</llsd>"

        blank_uri_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<uri />\
</llsd>"

        self.assertEqual(
            'http://sim956.agni.lindenlab.com:12035/runtime/agents',
            self.roundTrip(self.llsd.parse(valid_uri_xml)))
        self.assertEqual(
            None,
            self.roundTrip(self.llsd.parse(blank_uri_xml)))

    def testUndefined(self):
        undef_xml = "<?xml version=\"1.0\" ?><llsd><undef /></llsd>"
        self.assertEqual(
            None,
            self.roundTrip(self.llsd.parse(undef_xml)))


    def testMulti(self):
        multi_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array>\
<array>\
<map>\
<key>content-type</key><string>application/binary</string>\
</map>\
<binary>MTIzNDU2Cg==</binary>\
</array>\
<array>\
<map>\
<key>content-type</key><string>application/exe</string>\
</map>\
<binary>d2hpbGUoMSkgeyBwcmludCAneWVzJ307Cg==</binary>\
</array>\
</array>\
</llsd>"

        multi_python = [
            [{'content-type':'application/binary'},'123456\n'],
            [{'content-type':'application/exe'},"while(1) { print 'yes'};\n"]]

        self.assertEqual(
            multi_python,
            self.roundTrip(self.llsd.parse(multi_xml)))


    def dtestBench(self):
        obj = {'a':{'a1':12, 'a2':123.45}, 'b':[1234555, None],
               'c':"this is some xml: <xml> &amp;",
               'd':['a','small','little','text']}
        for i in range(0, 5000):
            x = llsd.format_xml(obj)
        n = 10000
        import time
        t = time.clock()
        for i in range(0, n):
            x = llsd.format_xml(obj)
        delta = time.clock() - t
        print "Time:", delta

class LLSDPythonXMLUnitTest(TestBase):
    mode = 'static'
    def setUp(self):
        self.llsd = llsd.LLSD()
        
        # null out cllsd so that we test the pure python
        # implementation.
        self._cllsd = llsd.cllsd
        llsd.cllsd = None

    def tearDown(self):
        # restore the cllsd module if it was there in the first place 
        llsd.cllsd = self._cllsd

    def assert_xml_roundtrip(self, py, xml):
        parsed_py = self.llsd.parse(xml)
        formatted_xml = self.llsd.as_xml(py)
        self.assertEqual(parsed_py, py)
        self.assertEqual(self.strip(formatted_xml),
                         self.strip(xml))
        self.assertEqual(py, self.llsd.parse(formatted_xml))
        self.assertEqual(self.strip(xml),
                         self.strip(self.llsd.as_xml(parsed_py)))

    def testMap(self):
        map_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<map>\
<key>foo</key>\
<string>bar</string>\
</map>\
</llsd>"

        map_within_map_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<map>\
<key>foo</key>\
<string>bar</string>\
<key>doo</key>\
<map>\
<key>goo</key>\
<string>poo</string>\
</map>\
</map>\
</llsd>"

        blank_map_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<map />\
</llsd>"

        python_map = {"foo":"bar"}
        python_map_within_map = {"foo":"bar", "doo":{"goo":"poo"}}

        self.assert_xml_roundtrip(python_map, map_xml)
        self.assert_xml_roundtrip(python_map_within_map,
                                             map_within_map_xml)
        self.assert_xml_roundtrip({}, blank_map_xml)

    def testArray(self):
        array_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array>\
<string>foo</string>\
<string>bar</string>\
</array>\
</llsd>"

        array_within_array_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array>\
<string>foo</string>\
<string>bar</string>\
<array>\
<string>foo</string>\
<string>bar</string>\
</array>\
</array>\
</llsd>"

        blank_array_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array />\
</llsd>"

        python_array = ["foo", "bar"]
        python_array_within_array = ["foo", "bar",["foo", "bar"]]

        self.assert_xml_roundtrip(python_array, array_xml)
        self.assert_xml_roundtrip(python_array_within_array,
                                             array_within_array_xml)
        self.assert_xml_roundtrip([], blank_array_xml)

    def testString(self):
        sample_data = {'foo':"\
<?xml version=\"1.0\" ?>\
<llsd>\
<string>foo</string>\
</llsd>",
                 '':"\
<?xml version=\"1.0\" ?>\
<llsd>\
<string />\
</llsd>",
                 '<xml>&ent;</xml>':"\
<?xml version=\"1.0\" ?>\
<llsd>\
<string>&lt;xml&gt;&amp;ent;&lt;/xml&gt;</string>\
</llsd>"         
                 }
        for py, xml in sample_data.items():
            self.assert_xml_roundtrip(py, xml)

    def testInteger(self):
        ## TODO test <integer />
        pos_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer>289343</integer>\
</llsd>"

        neg_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer>-289343</integer>\
</llsd>"

        blank_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer />\
</llsd>"

        python_pos_int = 289343
        python_neg_int = -289343

        self.assert_xml_roundtrip(python_pos_int,
                                             pos_int_xml)
        self.assert_xml_roundtrip(python_neg_int,
                                             neg_int_xml)
        self.assertEqual(0, self.llsd.parse(blank_int_xml))

    def testReal(self):
        ## TODO test <real />
        pos_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real>2983287453.3000002</real>\
</llsd>"

        neg_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real>-2983287453.3000002</real>\
</llsd>"

        blank_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real />\
</llsd>"

        python_pos_real = 2983287453.3
        python_neg_real = -2983287453.3

        self.assert_xml_roundtrip(python_pos_real,
                                             pos_real_xml)
        self.assert_xml_roundtrip(python_neg_real,
                                             neg_real_xml)
        self.assertEqual(0, self.llsd.parse(blank_real_xml))

    def testBoolean(self):
        true_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean>true</boolean>\
</llsd>"

        false_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean>false</boolean>\
</llsd>"

        blank_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean />\
</llsd>"

        self.assert_xml_roundtrip(True, true_xml)
        self.assert_xml_roundtrip(False, false_xml)
        self.assertEqual(False, self.llsd.parse(blank_xml))

    def testDate(self):
        valid_date_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<date>2006-02-01T14:29:53.460000Z</date>\
</llsd>"

        valid_date_xml_no_fractional = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<date>2006-02-01T14:29:53Z</date>\
</llsd>"
        valid_date_xml_filled ="\
<?xml version=\"1.0\" ?>\
<llsd>\
<date>2006-02-01T14:29:05Z</date>\
</llsd>"

        blank_date_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<date />\
</llsd>"


        python_valid_date = datetime(2006, 2, 1, 14, 29, 53, 460000)
        python_valid_date_no_fractional = datetime(2006, 2, 1, 14, 29, 53)
        python_valid_date_filled = datetime(2006, 2, 1, 14, 29, 05)
        python_blank_date = datetime(1970, 1, 1)
        self.assert_xml_roundtrip(python_valid_date,
                                  valid_date_xml)
        self.assert_xml_roundtrip(python_valid_date_no_fractional,
                                  valid_date_xml_no_fractional)
        self.assert_xml_roundtrip(python_valid_date_filled,
                                  valid_date_xml_filled)
        self.assertEqual(python_blank_date, self.llsd.parse(blank_date_xml))

    def testBinary(self):
        base64_binary_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<binary>dGhlIHF1aWNrIGJyb3duIGZveA==</binary>\
</llsd>"

        # <binary /> should return blank binary blob... in python I guess this is just nil
        python_binary = llsd.binary("the quick brown fox")
        self.assert_xml_roundtrip(python_binary,
                                             base64_binary_xml)

    def testUUID(self):
        uuid_tests = {
            uuid.UUID(hex='d7f4aeca-88f1-42a1-b385-b9db18abb255'):"\
<?xml version=\"1.0\" ?>\
<llsd>\
<uuid>d7f4aeca-88f1-42a1-b385-b9db18abb255</uuid>\
</llsd>",
            uuid.UUID(int=0):"\
<?xml version=\"1.0\" ?>\
<llsd>\
<uuid />\
</llsd>"}

        for py, xml in uuid_tests.items():
            self.assert_xml_roundtrip(py, xml)

    def testURI(self):
        uri_tests = {
            llsd.uri('http://sim956.agni.lindenlab.com:12035/runtime/agents'):"\
<?xml version=\"1.0\" ?>\
<llsd>\
<uri>http://sim956.agni.lindenlab.com:12035/runtime/agents</uri>\
</llsd>"}

        blank_uri_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<uri />\
</llsd>"

        for py, xml in uri_tests.items():
            self.assert_xml_roundtrip(py, xml)
        self.assertEqual(None, self.llsd.parse(blank_uri_xml))

    def testUndefined(self):
        undef_xml = "<?xml version=\"1.0\" ?><llsd><undef /></llsd>"
        self.assert_xml_roundtrip(None, undef_xml)

    def test_llsd_serialization_exception(self):
        # make an object not supported by llsd
        python_native_obj = Foo()

        # assert than an exception is raised
        self.assertRaises(TypeError, self.llsd.as_xml, python_native_obj)


    def strip(self, the_string):
        return re.sub('\s', '', the_string)

    def test_segfault(self):
        for i, badstring in enumerate([
            '<?xml \xee\xae\x94 ?>',
            '<?xml \xc4\x9d ?>',
            '<?xml \xc8\x84 ?>',
            '<?xml \xd9\xb5 ?>',
            '<?xml \xd9\xaa ?>',
            '<?xml \xc9\x88 ?>',
            '<?xml \xcb\x8c ?>']):
            self.assertRaises(llsd.LLSDParseError, llsd.parse, badstring)

    def test_fuzz_parsing(self):
        self.fuzz_parsing_base('xml_fuzz',
            (llsd.LLSDParseError, IndexError, ValueError))
    
    def test_fuzz_roundtrip(self):
        def isnan(x):
            return x != x
        def normalize(s):
            """ Certain transformations of input data are permitted by
            the spec; this function normalizes a python data structure
            so it receives these transformations as well.
            * codepoints disallowed in xml dropped from strings
            * \r -> \n
            * \n\n -> \n (not sure about this one)
            * date objects -> datetime objects (parser only parses datetimes)
            * nan converted to None (just because nan's are incomparable)
            """
            if isinstance(s, (str, unicode)):
                s = llsd.remove_invalid_xml_codepoints(s)
                s = s.replace('\r', '\n')
                s = s.replace('\n\n', '\n')
                return s
            if isnan(s):
                return None
            if isinstance(s, date):
                return datetime(s.year, s.month, s.day)
            if isinstance(s, list):
                for i,x in enumerate(s):
                    s[i] = normalize(x)
            if isinstance(s, dict):
                new_s = {}
                for k,v in s.iteritems():
                    new_s[normalize(k)] = normalize(v)
                s = new_s
            return s

        def recompare(a,b):
            self.assertEqualsPretty(normalize(a),
                                    normalize(b))
        self.fuzz_roundtrip_base(llsd.format_xml, recompare)

class LLSDBinaryUnitTest(TestBase):
    mode = 'static'
    def setUp(self):
        self.llsd = llsd.LLSD()

    def roundTrip(self, something):
        binary = self.llsd.as_binary(something)
        return self.llsd.parse(binary)

    def testMap(self):
        map_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<map>\
<key>foo</key>\
<string>bar</string>\
</map>\
</llsd>"

        map_within_map_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<map>\
<key>foo</key>\
<string>bar</string>\
<key>doo</key>\
<map>\
<key>goo</key>\
<string>poo</string>\
</map>\
</map>\
</llsd>"

        blank_map_xml = "\
<llsd>\
<map />\
</llsd>"

        python_map = {"foo":"bar"}
        python_map_within_map = {"foo":"bar", "doo":{"goo":"poo"}}

        self.assertEqual(python_map, self.roundTrip(self.llsd.parse(map_xml)))
        self.assertEqual(
            python_map_within_map,
            self.roundTrip(self.llsd.parse(map_within_map_xml)))
        self.assertEqual({}, self.roundTrip(self.llsd.parse(blank_map_xml)))

    def testArray(self):
        array_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array>\
<string>foo</string>\
<string>bar</string>\
</array>\
</llsd>"
        array_within_array_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array>\
<string>foo</string>\
<string>bar</string>\
<array>\
<string>foo</string>\
<string>bar</string>\
</array>\
</array>\
</llsd>"
        blank_array_xml = "\
<llsd>\
<array />\
</llsd>"

        python_array = ["foo", "bar"]
        python_array_within_array = ["foo", "bar",["foo", "bar"]]

        self.assertEqual(
            python_array,
            self.roundTrip(self.llsd.parse(array_xml)))
        self.assertEqual(
            python_array_within_array,
            self.roundTrip(self.llsd.parse(array_within_array_xml)))
        self.assertEqual(
            [],
            self.roundTrip(self.llsd.parse(blank_array_xml)))

    def testString(self):
        normal_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<string>foo</string>\
</llsd>"

        blank_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<string />\
</llsd>"

        self.assertEqual("foo", self.roundTrip(self.llsd.parse(normal_xml)))
        self.assertEqual("", self.roundTrip(self.llsd.parse(blank_xml)))

    def testInteger(self):
        ## TODO test <integer />
        pos_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer>289343</integer>\
</llsd>"

        neg_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer>-289343</integer>\
</llsd>"

        blank_int_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<integer />\
</llsd>"

        python_pos_int = 289343
        python_neg_int = -289343

        self.assertEqual(
            python_pos_int,
            self.roundTrip(self.llsd.parse(pos_int_xml)))
        self.assertEqual(
            python_neg_int,
            self.roundTrip(self.llsd.parse(neg_int_xml)))
        self.assertEqual(
            0,
            self.roundTrip(self.llsd.parse(blank_int_xml)))

    def testReal(self):
        pos_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real>2983287453.3</real>\
</llsd>"

        neg_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real>-2983287453.3</real>\
</llsd>"

        blank_real_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<real />\
</llsd>"

        python_pos_real = 2983287453.3
        python_neg_real = -2983287453.3

        self.assertEqual(
            python_pos_real,
            self.roundTrip(self.llsd.parse(pos_real_xml)))
        self.assertEqual(
            python_neg_real,
            self.roundTrip(self.llsd.parse(neg_real_xml)))
        self.assertEqual(
            0,
            self.roundTrip(self.llsd.parse(blank_real_xml)))

    def testBoolean(self):
        true_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean>true</boolean>\
</llsd>"

        false_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean>false</boolean>\
</llsd>"

        blank_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<boolean />\
</llsd>"

        self.assertEqual(True, self.roundTrip(self.llsd.parse(true_xml)))
        self.assertEqual(False, self.roundTrip(self.llsd.parse(false_xml)))
        self.assertEqual(False, self.roundTrip(self.llsd.parse(blank_xml)))

    def testDate(self):
        valid_date_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<date>2006-02-01T14:29:53Z</date>\
</llsd>"

        blank_date_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<date />\
</llsd>"
        python_valid_date = datetime(2006, 2, 1, 14, 29, 53)
        python_blank_date = datetime(1970, 1, 1)

        self.assertEqual(
            python_valid_date,
            self.roundTrip(self.llsd.parse(valid_date_xml)))
        self.assertEqual(
            python_blank_date,
            self.roundTrip(self.llsd.parse(blank_date_xml)))

    def testBinary(self):
        base64_binary_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<binary>dGhlIHF1aWNrIGJyb3duIGZveA==</binary>\
</llsd>"

        foo = self.llsd.parse(base64_binary_xml)
        self.assertEqual(
            llsd.binary("the quick brown fox"),
            self.roundTrip(foo))

    def testUUID(self):
        valid_uuid_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<uuid>d7f4aeca-88f1-42a1-b385-b9db18abb255</uuid>\
</llsd>"
        blank_uuid_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<uuid />\
</llsd>"
        self.assertEqual(
            'd7f4aeca-88f1-42a1-b385-b9db18abb255',
            self.roundTrip(str(self.llsd.parse(valid_uuid_xml))))
        self.assertEqual(
            '00000000-0000-0000-0000-000000000000',
            self.roundTrip(str(self.llsd.parse(blank_uuid_xml))))

    def testURI(self):
        valid_uri_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<uri>http://sim956.agni.lindenlab.com:12035/runtime/agents</uri>\
</llsd>"

        blank_uri_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<uri />\
</llsd>"

        self.assertEqual(
            'http://sim956.agni.lindenlab.com:12035/runtime/agents',
            self.roundTrip(self.llsd.parse(valid_uri_xml)))
        self.assertEqual(
            None,
            self.roundTrip(self.llsd.parse(blank_uri_xml)))

    def testUndefined(self):
        undef_xml = "<?xml version=\"1.0\" ?><llsd><undef /></llsd>"
        self.assertEqual(
            None,
            self.roundTrip(self.llsd.parse(undef_xml)))


    def testMulti(self):
        multi_xml = "\
<?xml version=\"1.0\" ?>\
<llsd>\
<array>\
<array>\
<map>\
<key>content-type</key><string>application/binary</string>\
</map>\
<binary>MTIzNDU2Cg==</binary>\
</array>\
<array>\
<map>\
<key>content-type</key><string>application/exe</string>\
</map>\
<binary>d2hpbGUoMSkgeyBwcmludCAneWVzJ307Cg==</binary>\
</array>\
</array>\
</llsd>"

        multi_python = [
            [{'content-type':'application/binary'},'123456\n'],
            [{'content-type':'application/exe'},"while(1) { print 'yes'};\n"]]

        self.assertEqual(
            multi_python,
            self.roundTrip(self.llsd.parse(multi_xml)))


    

    def dtestBench(self):
        obj = {'a':{'a1':12, 'a2':123.45}, 'b':[1234555, None],
               'c':"this is some xml: <xml> &amp;",
               'd':['a','small','little','text']}
        for i in range(0, 5000):
            x = llsd.format_xml(obj)
        n = 10000
        import time
        t = time.clock()
        for i in range(0, n):
            x = llsd.format_xml(obj)
        delta = time.clock() - t
        print "Time:", delta
    
    def test_fuzz_parsing(self):
        self.fuzz_parsing_base('binary_fuzz',
            (llsd.LLSDParseError, IndexError, ValueError))
    
    def test_fuzz_roundtrip(self):
        self.fuzz_roundtrip_base(llsd.format_binary)

if __name__ == '__main__':
    unittest.main()
