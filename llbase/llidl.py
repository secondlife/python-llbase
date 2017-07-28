# file: llidl.py
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
LLIDL parser and value checker.

LLIDL is an interface description language for REST like protocols based on
the LLSD type system.
"""
from __future__ import absolute_import

import datetime
import re
import uuid
from functools import total_ordering

from . import llsd
from . import lluuid

NoneType = type(None)
StringTypes = llsd.StringTypes

@total_ordering
class _Result(object):
    """
    The result of a llsd/llidl spciciation comparison

    When comparing a particular llsd value to an llidl specification, there
    are several possible outcomes:
        MATCHED: the structure is as expected, the values all the right type
        CONVERTED: the structure is as expected, but some values were of
            convertable values, structure may have gone through a system with
            more a restrictive type system
        DEFAULTED: parts of the structure were missing, or set to undef
            these will be read as the default value, this may indicate that
            the structure comes from a system with an older definition
        ADDITIONAL: parts of the structure do not correspond with the spec,
            they will be ignored
        MIXED: some were defaulted , some were newer
        INCOMPATIBLE: there were values that just didn't match and can't
            be converted        
    """
    def __init__(self, value, name):
        self._value = value
        self._name = name
    
    def __repr__(self):
        return "llidl." + self._name
        
    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self._value == other._value

    def __lt__(self, other):
        return self._value < other._value

    def __and__(self, other):
        sv = int(self._value)
        ov = int(other._value)
        if sv < ov: return self
        if ov < sv: return other
        if self._value != other._value:
            return MIXED
        return self

    def __or__(self, other):
        if self._value >= other._value:
            return self
        return other

MATCHED         = _Result(4, "MATCHED")
CONVERTED       = _Result(3, "CONVERTED")
DEFAULTED       = _Result(2.2, "DEFAULTED")
ADDITIONAL      = _Result(2.1, "ADDITIONAL")
MIXED           = _Result(1, "MIXED")
INCOMPATIBLE    = _Result(0, "INCOMPATIBLE")


class MatchError(Exception):
    """A mis-match between an LLSD and a LLIDL value description"""
    def __init__(self, mesg):
        self.mesg = mesg

    def __repr__(self):
        return self.mesg

    def __str__(self):
        return self.__repr__()
        

class MatchErrorStack(Exception):
    def __init__(self, vtype, val, r=None):
        if r is not None:
            self.stack=[ (vtype, val, r) ] 
        else:
            self.stack=[ (vtype, val) ] 

    def push(self, vtype, val):
        self.stack.insert(0, ( vtype, val ) )

    def format_entry(self, klass, val):
        if type(klass) == tuple:
            klass, name = klass
            return "%s::%s (%s)" % (klass.__name__, name, val)
        else:
            return "%s (%s)" % (klass.__name__, val)

    def format_stack(self, paths, path, stack):
        for entry in stack:
            if len(entry) == 3:
                klass, val, r = entry
                paths.append("%s <<%s>>" % (' -> '.join(path + [self.format_entry(klass, val)]), r))
                continue
            klass, val = entry
            if type(val) == list:
                entries=val
                klass, val = klass
                for variant in entries:
                    self.format_stack(paths, path+["&%s" % val], variant.stack)
            else:
                path.append(self.format_entry(klass, val))

    def __repr__(self):
        paths=[]
        self.format_stack(paths, [], self.stack)
        return '\n'.join(paths)

    def __str__(self):
        return self.__repr__()
    
    
class Value(object):
    """
    A single value specification from a LLIDL suite
    
    Tests:

    * match(actual) -- True if the value matches structurally and all 
      conversions are valid (non-defaulted)
    * valid(actual) -- True if the value matches structurally though
      defaulted or additional data is acceptable,
      all conversions must still be valid (non-defaulted)
        
    The above two tests take an optional keyword argument 'raises'
    which determines the exception behavior: If it is None (the default),
    then the test result is simply returned. Otherwise a exception is
    raised if the test fails. Which exception is determined by the value
    of raises

    * True        -- raises a MatchError
    * a class     -- raises a new instance of the class
    * an instance -- raises that instance
    * a callable  -- raises the result of calling it

    In the case of both a class or a callable, the error string is supplied
    as the only argument to constructing or calling.
        
    * has_additional(actual)  -- True if the value has additional data
    * has_defaulted(actual) -- True if the value has defaulted data
    * incompatible(actual) -- True if the value is incompatible
        
    The above three tests are primarily for unit testing and do not support
    the raises feature.
    """
    
    def _set_suite(self, suite):
        pass
        
    def _variants_referenced(self):
        return set() # faster than frozenset, really!

    def _compare(self, actual, raise_level=None):
        """Compare an LLSD value to the value spec.; return a Result"""
        return INCOMPATIBLE
    
    def _failure(self, raises, message):
        if raises is not None:
            if raises is True:
                raises = MatchError(message)
            if callable(raises):
                raises = raises(message)
            raise raises
        return False    
    
    def match(self, actual, raises=None, match_level=CONVERTED):
        """Return True if the value matches exactly"""
        raise_level=None
        if raises is not None:
            raise_level=match_level
        try:
            return (self._compare(actual, raise_level=raise_level) >= match_level
                 or self._failure(raises, "did not match"))
        except MatchErrorStack as e:
            return self._failure(raises, str(e))
    
    def valid(self, actual, raises=None, match_level=MIXED):
        """Return True if the value matches, or has additional data"""
        return self.match(actual, match_level=match_level, raises=raises)

    def has_additional(self, actual):
        """Return True if the value has additional data"""
        r = self._compare(actual)
        return r == ADDITIONAL or r == MIXED

    def has_defaulted(self, actual):
        """Return True if the value has defaulted (missing) data"""
        r = self._compare(actual)
        return r == DEFAULTED or r == MIXED
    
    def incompatible(self, actual):
        """Return True if the value is incompatible"""
        return self._compare(actual) == INCOMPATIBLE
    


class _UndefMatcher(Value):
    def _compare(self, actual, raise_level=None):
        return MATCHED    # every value matches undef


class _BoolMatcher(Value):
    def _compare(self, actual, raise_level=None):
        t = type(actual)
        r = INCOMPATIBLE
        if t == NoneType:
            r = DEFAULTED
        elif t == bool:
            r = MATCHED
        elif t == int:
            if actual == 0 or actual == 1:
                r = CONVERTED
        elif t == float:
            if actual == 0.0 or actual == 1.0:
                r = CONVERTED
        elif t in StringTypes:
            if actual == "" or actual == "true":
                r = CONVERTED
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=self.__class__, val=actual, r=r)
        return r


class _TrueMatcher(Value):
    def _compare(self, actual, raise_level=None):
        t = type(actual)
        r = INCOMPATIBLE
        if t == NoneType:
            pass
        elif t == bool:
            if actual:
                r = MATCHED
        elif t == int:
            if actual == 1:
                r = CONVERTED
        elif t == float:
            if actual == 1.0:
                r = CONVERTED
        elif t in StringTypes:
            if actual == "true":
                r = CONVERTED
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=(self.__class__, True), val=actual, r=r)
        return r

   
class _FalseMatcher(Value):
    def _compare(self, actual, raise_level=None):
        t = type(actual)
        r = INCOMPATIBLE
        if t == NoneType:
            r = DEFAULTED
        elif t == bool:
            if not actual:
                r = MATCHED
        elif t == int:
            if actual == 0:
                r = CONVERTED
        elif t == float:
            if actual == 0.0:
                r = CONVERTED
        elif t in StringTypes:
            if actual == "":
                r = CONVERTED
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=self.__class__, val=actual, r=r)
        return r


class _IntMatcher(Value):
    def _compare(self, actual, raise_level=None):
        t = type(actual)
        r = INCOMPATIBLE
        if t == NoneType:
            r = DEFAULTED
        elif t == bool:
            r = CONVERTED
        elif t == int:
            r = MATCHED
        elif t == float:
            try:
                i = int(actual)
                if actual == i and type(i) == int:
                    r = CONVERTED
            except:
                pass
        elif t in StringTypes:
            try:
                f = float(actual)
                i = int(f)
                if f == i and type(i) == int:
                    r = CONVERTED
            except:
                if actual == "":
                    r = DEFAULTED
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=self.__class__, val=actual, r=r)
        return r


class _NumberMatcher(Value):
    def __init__(self, number):
        self._number = int(number)
        
    def _compare(self, actual, raise_level=None):
        n = 0
        r = CONVERTED
        
        t = type(actual)
        if t == NoneType:
            n = 0
            r = DEFAULTED
        elif t == bool:
            n = actual and 1 or 0
            r = CONVERTED
        elif t == int:
            n = actual
            r = MATCHED
        elif t == float:
            n = int(actual)
            r = CONVERTED
        elif t in StringTypes:
            try:
                n = int(float(actual))
                r = CONVERTED
            except:
                if actual == "":
                    n = 0
                    r = DEFAULTED
                else:
                    r = INCOMPATIBLE
        else:
            r = INCOMPATIBLE
        
        if r != INCOMPATIBLE:
            if n != self._number:
                r = INCOMPATIBLE
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=(self.__class__, self._number), val=actual, r=r)
        return r

                
class _RealMatcher(Value):
    def _compare(self, actual, raise_level=None):
        t = type(actual)
        r = INCOMPATIBLE
        if t == NoneType:
            r = DEFAULTED
        elif t == bool:
            r = CONVERTED
        elif t == int:
            r = CONVERTED
        elif t == float:
            r = MATCHED
        elif t in StringTypes:
            try:
                f = float(actual)
                r = CONVERTED
            except:
                if actual == "":
                    return DEFAULTED
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=self.__class__, val=actual, r=r)
        return r


class _StringMatcher(Value):
    def _compare(self, actual, raise_level=None):
        t = type(actual)
        r = CONVERTED
        if t == NoneType:
            r = DEFAULTED
        elif t in StringTypes:
            r = MATCHED
        elif t == llsd.binary:
            r = INCOMPATIBLE
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=self.__class__, val=actual, r=r)
        return r


class _NameMatcher(Value):
    def __init__(self, name):
        self._name = str(name)

    def _compare(self, actual, raise_level=None):
        t = type(actual)
        r = INCOMPATIBLE
        if t == NoneType:
            if self._name == "":
                r = DEFAULTED
        elif t in StringTypes:
            if self._name == actual:
                r = MATCHED
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=(self.__class__, self._name), val=actual, r=r)
        return r



class _DateMatcher(Value):
    
    _dateRE = re.compile(r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d(.\d+)?Z');
    
    def _compare(self, actual, raise_level=None):
        t = type(actual)
        r = INCOMPATIBLE
        if t == NoneType:
            r = DEFAULTED
        elif t in StringTypes:
            if self._dateRE.match(actual):
                r = CONVERTED
            elif actual == "":
                r = DEFAULTED
        elif t == datetime.datetime or t == datetime.date:
            r = MATCHED
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=self.__class__, val=actual, r=r)
        return r


class _UUIDMatcher(Value):
    
    _uuidRE = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}');
    
    def _compare(self, actual, raise_level=None):
        t = type(actual)
        r = INCOMPATIBLE
        if t == NoneType:
            r = DEFAULTED
        elif t in StringTypes:
            if self._uuidRE.match(actual):
                r = CONVERTED
            elif actual == "":
                r = DEFAULTED
        elif t == uuid.UUID:
            r = MATCHED
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=self.__class__, val=actual, r=r)
        return r


class _URIMatcher(Value):
    def _compare(self, actual, raise_level=None):
        t = type(actual)
        r = INCOMPATIBLE
        if t == NoneType:
            r = DEFAULTED
        elif t in StringTypes:
            if actual == "":
                r = DEFAULTED
            else:
                r = CONVERTED
        elif t == llsd.uri:
            r = MATCHED
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=self.__class__, val=actual, r=r)
        return r


class _BinaryMatcher(Value):
    def _compare(self, actual, raise_level=None):
        t = type(actual)
        r = INCOMPATIBLE
        if t == NoneType:
            r = DEFAULTED
        elif t == llsd.binary:
            r = MATCHED
        if raise_level is not None and r < raise_level:
            raise MatchErrorStack(vtype=self.__class__, val=actual, r=r)
        return r


def _roundup(value, multiple):
    return value - 1 + (multiple - (value - 1) % multiple)
    

class _ArrayMatcher(Value):
    def __init__(self, values, repeating):
        self._values = values
        self._repeating = repeating
    
    def _set_suite(self, suite):
        for v in self._values:
            v._set_suite(suite)

    def _variants_referenced(self):
        s = set()
        for v in self._values:
            s |= v._variants_referenced()
        return s
            
    def _compare(self, actual, raise_level=None):
        if actual is None:
            actual = []
        if type(actual) != list:
            if raise_level is not None:
                raise MatchErrorStack(vtype=self.__class__, val=actual, r=INCOMPATIBLE)
            return INCOMPATIBLE
        
        r = MATCHED

        vlen = len(self._values)
        alen = len(actual)
        tlen = vlen
        if self._repeating:
            tlen = _roundup(alen, vlen)
        elif alen > vlen:
            r &= ADDITIONAL
            if raise_level is not None and r < raise_level:
                raise MatchErrorStack(vtype=self.__class__, val=actual, r=ADDITIONAL)
            
        for i in range(0,tlen):
            v = None
            if i < alen:
                v = actual[i]
            try:
                r &= self._values[i%vlen]._compare(v, raise_level=raise_level)
            except MatchErrorStack as e:
                e.push(vtype=self.__class__, val=i)
                raise
        return r

        
class _MapMatcher(Value):
    def __init__(self, members):
        self._members = members
    
    def _set_suite(self, suite):
        for v in self._members.values():
            v._set_suite(suite)

    def _variants_referenced(self):
        s = set()
        for v in self._members.values():
            s |= v._variants_referenced()
        return s
            

    def _compare(self, actual, raise_level=None):
        if actual is None:
            actual = {}
        if type(actual) != dict:
            if raise_level is not None:
                raise MatchErrorStack(vtype=self.__class__, val=actual, r=INCOMPATIBLE)
            return INCOMPATIBLE
        
        r = MATCHED
        for (name, value) in self._members.items():
            v = None
            if name in actual:
                v = actual[name]
            try:
                r &= value._compare(v, raise_level=raise_level)
            except MatchErrorStack as e:
                e.push(vtype=self.__class__, val=name)
                raise e
        # iterates through keys
        for name in actual:
            if name not in self._members:
                r &= ADDITIONAL
                if raise_level is not None and r < raise_level:
                    raise MatchErrorStack(vtype=self.__class__, val=name, r=ADDITIONAL)
                break
        return r


class _DictMatcher(Value):
    def __init__(self, value):
        self._value = value
    
    def _set_suite(self, suite):
        self._value._set_suite(suite)
    
    def _variants_referenced(self):
        return self._value._variants_referenced()
        
    def _compare(self, actual, raise_level=None):
        if actual is None:
            actual = {}
        if type(actual) != dict:
            return INCOMPATIBLE
        
        r = MATCHED
        for (k, v) in actual.items():
            try:
                r &= self._value._compare(v, raise_level=raise_level)
            except MatchErrorStack as e:
                e.push(vtype=self.__class__, val=k)
                raise
        return r


class _VariantMatcher(Value):
    def __init__(self, name):
        self._name = name
        self._suite = None
        
    def _set_suite(self, suite):
        self._suite = suite
    
    def _variants_referenced(self):
        return set([self._name])
    
    def _compare(self, actual, raise_level=None):
        if self._suite is None:
            return INCOMPATIBLE
        r = INCOMPATIBLE
        match_errors=[]
        for option in self._suite._get_variant_options(self._name):
            try:
                r |= option._compare(actual, raise_level=raise_level)
            except MatchErrorStack as e:
                match_errors.append(e)
        if match_errors and r < raise_level:
            raise MatchErrorStack(vtype=(self.__class__, self._name), val=match_errors)
        return r


class Suite(object):
    """
    A full suite of LLIDL resource descriptions
    
    See Value.match() and Value.valid() for meanings of match and valid
    tests, and the operation of the optional raises keyword argument.
    """
    
    def __init__(self):
        self._requests = { }
        self._responses = { }
        self._variants = { }
    
    def _add_resource(self, name, request, response):
        request._set_suite(self)
        response._set_suite(self)
        self._requests[name] = request
        self._responses[name] = response
    
    def _has_resource(self, name):
        return name in self._requests
        
    def _get_request(self, name):
        try:
            return self._requests[name]
        except KeyError:
            raise MatchError("Resource name '%s' not found in suite." % name)
    
    def _get_response(self, name):
        try:
            return self._responses[name]
        except KeyError:
            raise MatchError("Resource name '%s' not found in suite." % name)
    
    def _add_variant(self, name, value):
        value._set_suite(self)
        self._variants.setdefault(name, []).append(value)
    
    def _get_variant_options(self, name):
        return self._variants.get(name, [])
    
    def _missing_variants(self):
        refs = set()
        for v in self._requests.values():
            refs |= v._variants_referenced()
        for w in self._responses.values():
            refs |= w._variants_referenced()
        # set of keys
        return refs - set(self._variants)
            
    def match_request(self, name, *args, **kwargs):
        """Compare an LLSD value to a resource's request description"""
        return self._get_request(name).match(*args, **kwargs)
    
    def match_response(self, name, *args, **kwargs):
        """Compare an LLSD value to a resource's response description"""
        return self._get_response(name).match(*args, **kwargs)

    def valid_request(self, name, *args, **kwargs):
        """Compare an LLSD value to a resource's request description"""
        return self._get_request(name).valid(*args, **kwargs)
    
    def valid_response(self, name, *args, **kwargs):
        """Compare an LLSD value to a resource's response description"""
        return self._get_response(name).valid(*args, **kwargs)
    

    
class ParseError(Exception):
    """
    An error encountered when parsing an LLIDL text.

    Properties

    * line - the line the error occurred on
    * char - the character number on the line
    """
    
    def __init__(self, msg, line, char):
        Exception.__init__(self, line, msg)
        self.line = line
        self.char = char
    
    def __str__(self):
        return "line %d, char %d: %s" % (self.line, self.char, 
                                            Exception.__str__(self))


class _Parser(object):
    def __init__(self, input):
        if hasattr(input, "read"):
            self._string = input.read()
            input.close()
        else:
            self._string = input
        self._offset = 0
        self._line = 0
        self._lineoffset = self._offset

    def error(self, msg):
        raise ParseError(msg, self._line + 1, self._offset - self._lineoffset + 1)
        
    def required(self, r, message):
        if r is not None:
            return r;
        self.error(message)


    def parse_eof(self):
        if self._offset == len(self._string):
            return True
        return None
        
    def parse_literal(self, lit):
        n = len(lit)
        o = self._offset
        if self._string[o:o+n] == lit:
            self._offset = o + n
            return lit
        return None
    
    def parse_re(self, re):
        m = re.match(self._string, self._offset)
        if m:
            self._offset = m.end()
            return m.group()
        return None
    
    _ws_re = re.compile(r'(\t| |;[^\n\r]*)*')
    _nl_re = re.compile(r'\n|\r\n?')
    def parse_s(self):
        while True:
            self.parse_re(self._ws_re)
            if self.parse_re(self._nl_re):
                self._line += 1
                self._lineoffset = self._offset
            else:
                break
        
    _number_re = re.compile(r'\d+')
    def parseNumber(self):
        return self.parse_re(self._number_re)
    
    _name_re = re.compile(r'[a-zA-Z_](?:[a-zA-Z0-9_/]|-(?!>))*')
        # Hyphen's are not legal inside names, but by including them here
        # a very common error is caught and attributed to the name, rather than
        # the next token. Note that "foo->" must be preserved as a legal parse.
    def parseName(self):
        n = self.parse_re(self._name_re)
        if n and '-' in n:
            self.error("malformed name: hyphen (-) not allowed")
        return n 
    
    _typemap = { 
            'undef':    _UndefMatcher(),
            'bool':     _BoolMatcher(),
            'int':      _IntMatcher(),
            'real':     _RealMatcher(),
            'string':   _StringMatcher(),
            'date':     _DateMatcher(),
            'uuid':     _UUIDMatcher(),
            'uri':      _URIMatcher(),
            'binary':   _BinaryMatcher(),
            'true':     _TrueMatcher(),
            'false':    _FalseMatcher()
        }
    _undefMatcher = _typemap['undef']

    def _parse_rest_of_array(self):
        self.parse_s()
        values = []
        repeating = False
        while True:
            v = self.parse_value()
            if not v:
                break
            values.append(v)
            self.parse_s()
            if self.parse_literal(','):
                self.parse_s()
            else:
                break
        if self.parse_literal('...'):
            repeating = True
            self.parse_s()
        self.required(self.parse_literal(']'), 'expected close bracket')
        if not values:
            self.error('empty array')
        return _ArrayMatcher(values, repeating)
    
    def _parse_rest_of_map(self):
        self.parse_s()
        if self.parse_literal('$'):
            self.parse_s()
            self.required(self.parse_literal(':'), 'expected colon')
            self.parse_s()
            value = self.required(self.parse_value(), 'expected value')
            self.parse_s()
            self.required(self.parse_literal('}'), 'expected close bracket')
            return _DictMatcher(value)
                    
        members = { }
        while True:
            k = self.parseName()
            if not k:
                break
            if k in members:
                self.error('duplicate key in map')
            self.parse_s()
            self.required(self.parse_literal(':'), 'expected colon')
            self.parse_s()
            v = self.required(self.parse_value(), 'expected value')
            members[k] = v
            self.parse_s()
            if self.parse_literal(','):
                self.parse_s()
            else:
                break
        self.required(self.parse_literal('}'), 'expected close bracket')
        if not members:
            self.error('empty map')
        return _MapMatcher(members)
    
    def parse_value(self):
        if self.parse_literal('"'):
            name = self.required(self.parseName(), 'expected name in quotes')
            self.required(self.parse_literal('"'), 'expected close quote')
            return _NameMatcher(name)
        
        if self.parse_literal('['):
            return self._parse_rest_of_array()
            
        if self.parse_literal('{'):
            return self._parse_rest_of_map()
        
        if self.parse_literal('&'):
            name = self.required(self.parseName(), 'expected variant name')
            return _VariantMatcher(name)
                
        number = self.parseNumber()
        if number is not None:
            return _NumberMatcher(number)
            
        type_or_selector = self.parseName()
        if type_or_selector is not None:
            if type_or_selector in self._typemap:
                return self._typemap[type_or_selector]
            self.error('unknown type')
            
        return None

    def _parse_rest_of_post_resource(self):
        self.parse_s()
        req = self.required(self.parse_value(), 'expected request value')
        self.parse_s()
        self.required(self.parse_literal('<-'), 'expected result arrow')
        self.parse_s()
        res = self.required(self.parse_value(), 'expected result value')
        return (req, res)

    def _parse_rest_of_body_resource(self):
        self.parse_s()
        return self.required(self.parse_value(), 'expected body value')

    def _parse_rest_of_get_resource(self):
        body = self._parse_rest_of_body_resource()
        return (self._undefMatcher, body)

    def _parse_rest_of_put_resource(self):
        body = self._parse_rest_of_body_resource()
        return (body, self._undefMatcher)

    def _parse_rest_of_getput_resource(self):
        body = self._parse_rest_of_body_resource()
        return (body, body)

    def _parse_rest_of_getputdel_resource(self):
        body = self._parse_rest_of_body_resource()
        return (body, body)

    def _parse_rest_of_resource(self, suite):
        self.parse_s()
        name = self.required(self.parseName(), 'expected resource name')
        if suite._has_resource(name):
            self.error('duplicate resource name')
        self.parse_s()
        if self.parse_literal('->'):
            (req, res) = self._parse_rest_of_post_resource()
        elif self.parse_literal('<<'):
            (req, res) = self._parse_rest_of_get_resource()
        elif self.parse_literal('>>'):
            (req, res) = self._parse_rest_of_put_resource()
        elif self.parse_literal('<>'):
            (req, res) = self._parse_rest_of_getput_resource()
        elif self.parse_literal('<x>'):
            (req, res) = self._parse_rest_of_getputdel_resource()
        else:
            self.error('unknown resource type, expected ->, <<, >>, <> or <*>')
        suite._add_resource(name, req, res)
        

    def _parse_rest_of_variant(self, suite):
        name = self.required(self.parseName(), 'expected variant name')
        self.parse_s()
        self.required(self.parse_literal('='), 'expected equals sign')
        self.parse_s()
        val = self.required(self.parse_value(), 'expected variant value')
        suite._add_variant(name, val)
    
    def parse_suite(self):
        suite = Suite()
        while True:
            self.parse_s()
            if self.parse_literal('%%'):
                self._parse_rest_of_resource(suite)
            elif self.parse_literal('&'):
                self._parse_rest_of_variant(suite)
            else:
                break
        missing = suite._missing_variants()
        if missing:
            self.error('missing definitions of variants: ' + ', '.join(missing))
        return suite

             
def parse_value(spec):
    """Parse the LLIDL specification of a single value, return a Value"""
    p = _Parser(spec)
    r = p.required(p.parse_value(), 'expected value')
    p.required(p.parse_eof(), 'expected end of input')
    return r

def parse_suite(spec):
    """Parse a whole LLIDL suite, return a Suite"""
    p = _Parser(spec)
    s = p.required(p.parse_suite(), 'expected suite')
    p.required(p.parse_eof(), 'expected end of input')
    return s
