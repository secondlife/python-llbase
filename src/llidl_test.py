import datetime
import StringIO
import unittest

from indra.base import llidl
from indra.base import llsd
from indra.base import lluuid

def _dateToday():
    return datetime.datetime.today()

def _dateEpoch():
    return datetime.datetime.fromtimestamp(0)

def _uri():
    return llsd.uri('http://tools.ietf.org/html/draft-hamrick-llsd-00')

def _uuid():
    return lluuid.UUID().generate()
    
def _binary():
    return llsd.binary("\0x01\x02\x03")


class LLIDLTypeTests(unittest.TestCase):
    def test_undef(self):
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

    def test_bool(self):
        v = llidl.parse_value("bool")
        self.assert_(v.match(None))
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

    def test_int(self):
        v = llidl.parse_value("int")
        self.assert_(v.match(None))
        self.assert_(v.match(True))
        self.assert_(v.match(False))
        self.assert_(v.match(0))
        self.assert_(v.match(1))
        self.assert_(v.match(0.0))
        self.assert_(v.match(10.0))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.incompatible(6.02e23))
        self.assert_(v.match(""))
        self.assert_(v.match("0"))
        self.assert_(v.match("1"))
        self.assert_(v.match("0.0"))
        self.assert_(v.match("10.0"))
        self.assert_(v.incompatible("3.14"))
        self.assert_(v.incompatible("6.02e23"))
        self.assert_(v.incompatible("blob"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def test_real(self):
        v = llidl.parse_value("real")
        self.assert_(v.match(None))
        self.assert_(v.match(True))
        self.assert_(v.match(False))
        self.assert_(v.match(0))
        self.assert_(v.match(1))
        self.assert_(v.match(0.0))
        self.assert_(v.match(10.0))
        self.assert_(v.match(3.14))
        self.assert_(v.match(6.02e23))
        self.assert_(v.match(""))
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

    def test_string(self):
        v = llidl.parse_value("string")
        self.assert_(v.match(None))
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

    def test_date(self):
        v = llidl.parse_value("date")
        self.assert_(v.match(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.match(""))
        self.assert_(v.match("2009-02-06T22:17:38Z"))
        # self.assert_(v.match("2009-02-06T22:17:38.0025Z"))
        self.assert_(v.incompatible("bob"))
        self.assert_(v.match(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def test_uuid(self):
        v = llidl.parse_value("uuid")
        self.assert_(v.match(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.match(""))
        self.assert_(v.match("6cb93268-5148-423f-8618-eaa0884f5b6c"))
        self.assert_(v.incompatible("bob"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.match(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def test_uri(self):
        v = llidl.parse_value("uri")
        self.assert_(v.match(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.match(""))
        self.assert_(v.match("http://example.com/"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.match(_uri()))
        self.assert_(v.incompatible(_binary()))

    def test_binary(self):
        v = llidl.parse_value("binary")
        self.assert_(v.match(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(3.14))
        self.assert_(v.incompatible("bob"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.match(_binary()))

class LLIDLSelectorTests(unittest.TestCase):
    def test_true(self):
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

    def test_false(self):
        v = llidl.parse_value("false")
        self.assert_(v.match(None))
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
        
    def test_number16(self):
        v = llidl.parse_value("16")
        self.assert_(v.incompatible(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(False))
        self.assert_(v.incompatible(0))
        self.assert_(v.incompatible(3))
        self.assert_(v.match(16))
        self.assert_(v.incompatible(0.0))
        self.assert_(v.match(16.0))
        self.assert_(v.match(16.2))
        self.assert_(v.incompatible(""))
        self.assert_(v.match("16"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def test_number0(self):
        v = llidl.parse_value("0")
        self.assert_(v.match(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.match(False))
        self.assert_(v.match(0))
        self.assert_(v.incompatible(3))
        self.assert_(v.match(0.0))
        self.assert_(v.incompatible(16.0))
        self.assert_(v.match(""))
        self.assert_(v.match("0"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def test_string_bob(self):
        v = llidl.parse_value('"bob"')
        self.assert_(v.incompatible(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(False))
        self.assert_(v.incompatible(0))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(0.0))
        self.assert_(v.incompatible(16.0))
        self.assert_(v.incompatible(""))
        self.assert_(v.match("bob"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

    def x_test_string_empty(self):
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
    def test_not_simple(self):
        v = llidl.parse_value("[ string, uuid ]")
        self.assert_(v.match(None))
        self.assert_(v.incompatible(True))
        self.assert_(v.incompatible(False))
        self.assert_(v.incompatible(3))
        self.assert_(v.incompatible(16.0))
        self.assert_(v.incompatible(""))
        self.assert_(v.incompatible("bob"))
        self.assert_(v.incompatible(_dateToday()))
        self.assert_(v.incompatible(_uuid()))
        self.assert_(v.incompatible(_uri()))
        self.assert_(v.incompatible(_binary()))

        v = llidl.parse_value('[ "red", uuid ]')
        self.assert_(v.incompatible(None))
        
    def test_sizing(self):
        v = llidl.parse_value("[ int, int, int ]")
        self.assert_(v.match([]))
        self.assert_(v.match([1]))
        self.assert_(v.match([1,2]))
        self.assert_(v.match([1,2,3]))
        self.assert_(v.has_additional([1,2,3,4]))

        v = llidl.parse_value("[ int, 2, int ]")
        self.assert_(v.incompatible([]))
        self.assert_(v.incompatible([1]))
        self.assert_(v.match([1,2]))
        self.assert_(v.match([1,2,3]))
        self.assert_(v.has_additional([1,2,3,4]))

    def test_paring(self):
        v = llidl.parse_value("[ int, int ]")
        self.assert_(v.match([1,2]))
        self.assert_(v.match([1,'2']))
        self.assert_(v.match([1,None]))
        self.assert_(v.incompatible([1,_binary()]))

        self.assert_(v.match(['1',2]))
        self.assert_(v.match(['1','2']))
        self.assert_(v.match(['1',None]))
        self.assert_(v.incompatible(['1',_binary()]))

        self.assert_(v.match([None,2]))
        self.assert_(v.match([None,'2']))
        self.assert_(v.match([None,None]))
        self.assert_(v.incompatible([None,_binary()]))

        self.assert_(v.incompatible([_binary(),2]))
        self.assert_(v.incompatible([_binary(),'2']))
        self.assert_(v.incompatible([_binary(),None]))
        self.assert_(v.incompatible([_binary(),_binary()]))

    def test_repeating(self):
        v = llidl.parse_value("[ string, int, bool, ... ]")
        self.assert_(v.match([]))
        self.assert_(v.match(['a']))
        self.assert_(v.match(['a',2]))
        self.assert_(v.match(['a',2,True]))
        self.assert_(v.match(['a',2,True,'b']))
        self.assert_(v.match(['a',2,True,'b',3]))
        self.assert_(v.match(['a',2,True,'b',3,False]))
        
        self.assert_(v.match(['a',2,True,7,3,False]))
        self.assert_(v.match(['a',2,True,'b',3.0,False]))
        self.assert_(v.match(['a',2,True,'b',3,0]))
        
        self.assert_(v.incompatible(['a',2,True,_binary(),3,False]))
        self.assert_(v.incompatible(['a',2,True,'b','c',False]))
        self.assert_(v.incompatible(['a',2,True,'b',3,'d']))
        
class LLIDLMapTests(unittest.TestCase):
    def test_members(self):
        v = llidl.parse_value("{ amy: string, bob: int }")
        self.assert_(v.match({}))
        self.assert_(v.match({'amy': 'ant'}))
        self.assert_(v.match({'bob': 42}))
        self.assert_(v.match({'amy': 'ant', 'bob': 42}))
        self.assert_(v.has_additional({'amy': 'ant', 'bob': 42, 'cam': True}))

    def test_dict(self):
        v = llidl.parse_value("{ $: int }")
        self.assert_(v.match({}))
        self.assert_(v.match({'amy': 36}))
        self.assert_(v.match({'amy': 36, 'bob': 42}))
        self.assert_(v.match({'amy': 36, 'bob': 42, 'cam': 18}))
        self.assert_(v.match({'amy': None, 'bob': 42}))
        self.assert_(v.match({'amy': "36", 'bob': 42}))
        self.assert_(v.incompatible({'amy': 'ant', 'bob': 42}))
        self.assert_(v.match({'amy': 36, 'bob': None}))
        self.assert_(v.match({'amy': 36, 'bob': '42'}))
        self.assert_(v.incompatible({'amy': 36, 'bob': 'bee'}))


class LLIDLParsingTests(unittest.TestCase):
    def good_parse_value(self, s):
        try:
            v = llidl.parse_value(s)
        except llidl.ParseError, e:
            self.fail('Failed parsing "%s", %s' % (s, str(e)))

    def bad_parse_value(self, s, msg=None, line=None, char=None):
        try:
            v = llidl.parse_value(s)
            self.fail('Incorrectly parsed "%s" as valid' % s)
        except llidl.ParseError, e:
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
        self.assert_(v.match([1]));
        self.assert_(v.match([1,2]));
        self.assert_(v.has_additional([1,2,3]));
        v = llidl.parse_value('[int,int,]')
        self.assert_(v.match([1]));
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
        self.assert_(v.match({'a':1}));
        self.assert_(v.match({'a':1,'b':2}));
        self.assert_(v.has_additional({'a':1,'b':2,'c':3}));
        v = llidl.parse_value('{a:int,b:int,}')
        self.assert_(v.match({'a':1}));
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
            suite.match_request('event_record', { 'log': 'Beep-Beep-Beep' }))
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
        except Exception, me:
            self.assertEqual(str(me),
                "Resource name 'some_api' not found in suite.")
            
class LLIDLReportingTests(unittest.TestCase):
    def x_test_detail(self):
        """not yet implemented"""
        v = llidl.parse_value("{ size: int }")
        match = v.match({'size': 'large'})
        self.assertFalse(match)
        self.assertEqual(match.detail(),
            "size: string 'large' not convertible to int")

class LLIDLFileTests(unittest.TestCase):
    def test_parse_value_from_file(self):
        file = StringIO.StringIO("[ int, int ]")
        v = llidl.parse_value(file)
        self.assert_(v.match([1,2]))
        self.assert_(v.incompatible(["one", "two"]))
        
    def test_parse_suite_from_file(self):
        file = StringIO.StringIO(""";test suite
%% agent/name
-> { agent_id: uuid }
<- { first: string, last: string }
""")
        suite = llidl.parse_suite(file)
        self.assert_(
            suite.match_request('agent/name', { 'agent_id': _uuid() }))
        self.assert_(
            suite.match_response('agent/name', { 'first':'Amy', 'last':'Ant' }))

# Missing Tests
#   duplicate resources in suite
#   missing resources in suite
#   missing variants
#   variants based on numbers, w/defaults
#   variants based on bools, w/defaults


if __name__ == '__main__':
    unittest.main()


