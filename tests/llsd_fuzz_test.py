# $LicenseInfo:firstyear=2006&license=mit$
#
# Copyright (c) 2006-2009, Linden Research, Inc.
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

from llbase import llsd
import copy
import string
import uuid
import unittest
from llbase.test import llsd_fuzz
from datetime import datetime, date
from itertools import islice, izip, count


def is_nan(o):
    return isinstance(o, float) and o != o


class Base(unittest.TestCase):
    def setUp(self):
        self.lf = llsd_fuzz.LLSDFuzzer()
        self.lf2 = llsd_fuzz.LLSDFuzzer(self.lf.seed)


class Random(Base):
    def test_random_boolean(self):
        for i in xrange(10):
            rb = self.lf.random_boolean()
            self.assert_(isinstance(rb, bool))
            self.assertEquals(self.lf2.random_boolean(), rb)

    def test_random_integer(self):
        for i in xrange(10):
            self.assert_(isinstance(self.lf.random_integer(), (int, long)))

    def test_random_real(self):
        for i in xrange(10):
            self.assert_(isinstance(self.lf.random_real(), float))

    def test_random_uuid(self):
        for i in xrange(10):
            self.assert_(isinstance(self.lf.random_uuid(), uuid.UUID))

    def test_random_printable(self):
        self.assertEquals(len(self.lf.random_printable(100)), 100)
        for i in xrange(10):
            printed = self.lf.random_printable()
            self.assert_(isinstance(printed, str))
            for c in printed:
                self.assert_(c in string.printable)
                
    def test_random_unicode(self):
        for i in xrange(10):
            printed = self.lf.random_unicode()
            self.assert_(isinstance(printed, unicode))

    def test_random_bytes(self):
        for i in xrange(10):
            length = 17 + i
            randbytes = self.lf.random_bytes(length)
            self.assert_(isinstance(randbytes, str))
            self.assertEquals(len(randbytes), length)
            for i in randbytes:
                self.assert_(ord(i) >= 0)
                self.assert_(ord(i) < 256)            

    def test_random_binary(self):
        for i in xrange(10):
            self.assert_(isinstance(self.lf.random_binary(), llsd.binary))

    def test_random_uri(self):
        for i in xrange(10):
            self.assert_(isinstance(self.lf.random_uri(), llsd.uri))
            
    def test_random_date(self):
        for i in xrange(10):
            self.assert_(isinstance(self.lf.random_date(), datetime))

    def test_random_map(self):
        for i in xrange(10):
            generated = self.lf.random_map()
            self.assert_(isinstance(generated, dict))
            self.assert_(len(generated) > 0)
            for k in generated.iterkeys():
                self.assert_(isinstance(k, (str, unicode)))
                
    def test_random_array(self):
        for i in xrange(10):
            generated = self.lf.random_array()
            self.assert_(isinstance(generated, list))
            self.assert_(len(generated) > 0)


class Permute(Base):
    def permute(self, func, arg, size=100):
        perms = [func(arg) for x in xrange(size)]
        self.assert_(len(perms) == size)
        return perms

    def test_permute_undef(self):
        for i in self.permute(self.lf.permute_undef, True):
            self.assert_(i is None)

    def test_permute_boolean(self):
        for i in self.permute(self.lf.permute_boolean, True):
            self.assert_(isinstance(i, bool))

    def test_permute_integer(self):        
        for i in self.permute(self.lf.permute_integer, 1):
            self.assert_(isinstance(i, (int,long)))

    def test_permute_real(self):
        for i in self.permute(self.lf.permute_real, 1.0):
            self.assert_(isinstance(i, float))
            
    def test_permute_uuid(self):
        for i in self.permute(self.lf.permute_uuid, uuid.UUID(int=0)):
            self.assert_(isinstance(i, uuid.UUID))
            
    def test_permute_string(self):
        for i in self.permute(self.lf.permute_string, 'abc'):
            self.assert_(isinstance(i, (str, unicode)))
        for i in self.permute(self.lf.permute_string, u'abc'):
            self.assert_(isinstance(i, (str, unicode)))
    
    def test_permute_binary(self):
        for i in self.permute(self.lf.permute_binary, llsd.binary('123')):
            self.assert_(isinstance(i, llsd.binary))

    def test_permute_date(self):
        for i in self.permute(self.lf.permute_date, datetime.now()):
            self.assert_(isinstance(i, (date,datetime)))
        # try and trigger that OverflowError
        for i in self.permute(self.lf.permute_date, date.max):
            self.assert_(isinstance(i, (date, datetime)), repr(i))
  
    def test_permute_uri(self):
        for i in self.permute(self.lf.permute_uri, llsd.uri('abc')):
            self.assert_(isinstance(i, llsd.uri))
            
    def test_permute_map(self):
        for i in self.permute(self.lf.permute_map, {'a':'b'}):
            self.assert_(isinstance(i, dict))

    def test_permute_array(self):
        for i in self.permute(self.lf.permute_array, [1,2]):
            self.assert_(isinstance(i, (list, tuple)), repr(i))

            
            

class Fuzz(Base):
    type_map = None
    def recursive_type_check(self, obj):
        """ Verifies that the object contains only types that
        are legal llsd inputs."""
        if self.type_map is None:
            self.type_map = llsd.LLSDXMLFormatter().type_map
        self.assert_(type(obj) in self.type_map, repr(obj))
        if not isinstance(obj, (str, unicode)):
            try:
                for x in obj:
                    self.recursive_type_check(x)
            except TypeError:
                pass  # not iterable
                
                
    def contains_nan(self, obj):
        """ Returns true if the object has a NaN value somewhere in it."""
        if is_nan(obj):
            return True
        if not isinstance(obj, (str, unicode)):
            try:
                for x in obj:
                    if self.contains_nan(x):
                        return True
            except TypeError:
                pass  # not iterable
        return False
                
    # contains every type we should be expected to deal with
    base_obj = {'a':True, 
                'c': [1,2L,3.0], 
                'd': datetime.now(),
                'e':(1,2,3, 'j', u'y'),
                'f':date.today(),
                'g':uuid.UUID(int=1),
                'h':llsd.binary('hi'),
                'i':llsd.uri('http://www.example.com')}

    def test_structure_fuzz(self):
         for i in xrange(10):
            fuzzed = list(islice(self.lf.structure_fuzz(self.base_obj), 200))
            self.assert_(len(fuzzed) == 200)
            for f in fuzzed:
                self.recursive_type_check(f)
                
    def test_determinisim(self):
        base_obj = list(xrange(10))
        seed = self.lf.seed
        fuzzed_1 = list(islice(self.lf.structure_fuzz(base_obj), 1000))

        self.lf = llsd_fuzz.LLSDFuzzer(seed)
        fuzzed_2 = list(islice(self.lf.structure_fuzz(base_obj), 1000))
        
        if not fuzzed_1 != fuzzed_2:
            for i,v in enumerate(fuzzed_1):
                # nan is never equal to nan, so we have to exclude
                # items that differ solely because they happen to contain nan
                if v != fuzzed_2[i]:
                    if self.contains_nan(v):
                        continue
                    else:
                        self.assertEquals(v, fuzzed_2[i])
    
        
    def test_unrecognized_type(self):
        fuzz_it = self.lf.structure_fuzz(set())
        try:
            fuzz_it.next()
        except KeyError, e:
            pass
            
    def test_unmodified(self):
        copy_of_base_obj = copy.deepcopy(self.base_obj)
        fuzz_it = self.lf.structure_fuzz(copy_of_base_obj)
        list(islice(fuzz_it, 500))
        self.assertEquals(copy_of_base_obj, self.base_obj)

    def _string_fuzz_tester(self, func_name):
        seed = self.lf.seed
        quantity = 500
        func = getattr(self.lf, func_name)
        fuzzed = list(islice(func(self.base_obj), quantity))
        self.assert_(len(fuzzed) == quantity)
        empties = 0
        for f in fuzzed:
            self.assert_(isinstance(f, str))
            if len(f) == 0:
                empties += 1
        # no more than 1% should be zero-length
        self.assert_(empties < quantity/100.0,
                     "%s zero-length strings, using seed %r" % (empties, self.lf.seed))
    
        # determinism
        self.lf = llsd_fuzz.LLSDFuzzer(seed)
        func = getattr(self.lf, func_name)
        fuzzed2 = list(islice(func(self.base_obj), quantity))
        if not fuzzed == fuzzed2:
            for i,v in enumerate(fuzzed):
                self.assertEquals(v, fuzzed2[i])
        
    def test_binary_fuzz(self):
        self._string_fuzz_tester('binary_fuzz')

    def test_xml_fuzz(self):
        self._string_fuzz_tester('xml_fuzz')
        
    def test_notation_fuzz(self):
        self._string_fuzz_tester('notation_fuzz')


def show_permuted():
    lf = llsd_fuzz.LLSDFuzzer()
    print "seed", lf.seed
    ft = lf.structure_fuzz(Fuzz.base_obj)
    for i in xrange(10000):
        x = ft.next()
        import pprint
        pprint.pprint(x)
        print
        print "---------------------"
            
def run_profile():
    def time_test():
        lf = llsd_fuzz.LLSDFuzzer()
        ft = lf.structure_fuzz(Fuzz.base_obj)
        for i in xrange(10000):
            x = ft.next()

    import cProfile, pstats
    prof = cProfile.Profile()
    prof = prof.runctx("time_test()", globals(), locals())
    stats = pstats.Stats(prof)
    stats.sort_stats("time")
    stats.print_stats(20)

if __name__ == '__main__':
    unittest.main()
