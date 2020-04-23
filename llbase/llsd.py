# file llsd.py
#
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

"""
Types as well as parsing and formatting functions for handling LLSD.

This is the llsd module -- parsers and formatters between the
supported subset of mime types and python objects. Documentation
available on the Second Life wiki:

http://wiki.secondlife.com/wiki/LLSD
"""
from __future__ import absolute_import
from __future__ import division


import sys
import base64
import binascii
import calendar
import datetime
try:
    # If the future package is installed, then we support it.  Any clients in
    # python 2 using its str builtin replacement will actually be using instances
    # of newstr, so we need to properly detect that as a string type
    # for details see the docs: http://python-future.org/str_object.html
    from future.types.newstr import newstr
except ImportError:
    # otherwise we pass over it in silence
    newstr = str
import re
import struct
import time
import types
import uuid
import os

from .fastest_elementtree import ElementTreeError, fromstring

PY2 = sys.version_info[0] == 2

XML_MIME_TYPE = 'application/llsd+xml'
BINARY_MIME_TYPE = 'application/llsd+binary'
NOTATION_MIME_TYPE = 'application/llsd+notation'

class LLSDParseError(Exception):
    "Exception raised when the parser fails."
    pass

class LLSDSerializationError(TypeError):
    "Exception raised when serialization fails."
    pass

if PY2:
    class binary(str):
        "Simple wrapper for llsd.binary data."
        pass
else: 
    binary = bytes

class uri(str):
    "Simple wrapper for llsd.uri data."
    pass

# In Python 2, this expression produces (str, unicode); in Python 3 it's
# simply (str,). Either way, it's valid to test isinstance(somevar,
# StringTypes). (Some consumers test (type(somevar) in StringTypes), so we do
# want (str,) rather than plain str.)
StringTypes = tuple(set((type(''), type(u''), newstr)))

try:
    LongType = long
    IntTypes = (int, long)
except NameError:
    LongType = int
    IntTypes = int

try:
    UnicodeType = unicode
except NameError:
    UnicodeType = str

# can't just check for NameError: 'bytes' is defined in both Python 2 and 3
if PY2:
    BytesType = str
else:
    BytesType = bytes

try:
    b'%s' % (b'yes',)
except TypeError:
    # There's a range of Python 3 versions, up through Python 3.4, for which
    # bytes interpolation (bytes value with % operator) does not work. This
    # hack can be removed once we no longer care about Python 3.4 -- in other
    # words, once we're beyond jessie everywhere.
    class B(object):
        """
        Instead of writing:
        b'format string' % stuff
        write:
        B('format string') % stuff
        This class performs the conversions necessary to support bytes
        interpolation when the language doesn't natively support it.
        (We considered naming this class b, but that would be too confusing.)
        """
        def __init__(self, fmt):
            # Instead of storing the format string as bytes and converting it
            # to string every time, convert initially and store the string.
            try:
                self.strfmt = fmt.decode('utf-8')
            except AttributeError:
                # caller passed a string literal rather than a bytes literal
                self.strfmt = fmt

        def __mod__(self, args):
            # __mod__() is engaged for (self % args)
            if not isinstance(args, tuple):
                # Unify the tuple and non-tuple cases.
                args = (args,)
            # In principle, this is simple: convert everything to string,
            # interpolate, convert back. It's complicated by the fact that we
            # must handle non-bytes args.
            strargs = []
            for arg in args:
                try:
                    decoder = arg.decode
                except AttributeError:
                    # use arg exactly as is
                    strargs.append(arg)
                else:
                    # convert from bytes to string
                    strargs.append(decoder('utf-8'))
            return (self.strfmt % tuple(strargs)).encode('utf-8')
else:
    # bytes interpolation Just Works
    def B(fmt):
        try:
            # In the usual case, caller wrote B('fmt') rather than b'fmt'. But
            # s/he really wants a bytes literal here. Encode the passed string.
            return fmt.encode('utf-8')
        except AttributeError:
            # Caller wrote B(b'fmt')?
            return fmt

def is_integer(o):
    """ portable test if an object is like an int """
    return isinstance(o, IntTypes)

def is_unicode(o):
    """ portable check if an object is unicode and not bytes """
    return isinstance(o, UnicodeType)

def is_string(o):
    """ portable check if an object is string-like """
    return isinstance(o, StringTypes)

def is_bytes(o):
    """ portable check if an object is an immutable byte array """
    return isinstance(o, BytesType)

_int_regex = re.compile(br"[-+]?\d+")
_real_regex = re.compile(br"[-+]?(?:(\d+(\.\d*)?|\d*\.\d+)([eE][-+]?\d+)?)|[-+]?inf|[-+]?nan")
_alpha_regex = re.compile(br"[a-zA-Z]+")
_true_regex = re.compile(br"TRUE|true|\b[Tt]\b")
_false_regex = re.compile(br"FALSE|false|\b[Ff]\b")
_date_regex = re.compile(r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T"
                        r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
                        r"(?P<second_float>(\.\d+)?)Z")
#date: d"YYYY-MM-DDTHH:MM:SS.FFFFFFZ"

def _str_to_bytes(s):
    if is_unicode(s):
        return s.encode('utf-8')
    else:
        return s

def _format_datestr(v):
    """
    Formats a datetime or date object into the string format shared by
    xml and notation serializations.
    """
    if not isinstance(v, datetime.date) and not isinstance(v, datetime.datetime):
        raise LLSDParseError("invalid date string %s passed to date formatter" % s)
    
    if not isinstance(v, datetime.datetime):
        v = datetime.datetime.combine(v, datetime.time(0))
    
    return _str_to_bytes(v.isoformat() + 'Z')

def _parse_datestr(datestr):
    """
    Parses a datetime object from the string format shared by
    xml and notation serializations.
    """
    if datestr == "":
        return datetime.datetime(1970, 1, 1)
    
    match = re.match(_date_regex, datestr)
    if not match:
        raise LLSDParseError("invalid date string '%s'." % datestr)
    
    year = int(match.group('year'))
    month = int(match.group('month'))
    day = int(match.group('day'))
    hour = int(match.group('hour'))
    minute = int(match.group('minute'))
    second = int(match.group('second'))
    seconds_float = match.group('second_float')
    usec = 0
    if seconds_float:
        usec = int(float('0' + seconds_float) * 1e6)
    return datetime.datetime(year, month, day, hour, minute, second, usec)


def _bool_to_python(node):
    "Convert boolean node to a python object."
    val = node.text or ''
    try:
        # string value, accept 'true' or 'True' or whatever
        return (val.lower() in ('true', '1', '1.0'))
    except AttributeError:
       # not a string (no lower() method), use normal Python rules
       return bool(val)

def _int_to_python(node):
    "Convert integer node to a python object."
    val = node.text or ''
    if not val.strip():
        return 0
    return int(val)

def _real_to_python(node):
    "Convert floating point node to a python object."
    val = node.text or ''
    if not val.strip():
        return 0.0
    return float(val)

def _uuid_to_python(node):
    "Convert uuid node to a python object."
    if node.text:
        return uuid.UUID(hex=node.text)
    return uuid.UUID(int=0)

def _str_to_python(node):
    "Convert string node to a python object."
    return node.text or ''

def _bin_to_python(node):
    base = node.get('encoding') or 'base64'
    try:
        if base == 'base16':
            # parse base16 encoded data
            return binary(base64.b16decode(node.text or ''))
        elif base == 'base64':
            # parse base64 encoded data
            return binary(base64.b64decode(node.text or ''))
        elif base == 'base85':
            return LLSDParseError("Parser doesn't support base85 encoding")
    except binascii.Error as exc:
        # convert exception class so it's more catchable
        return LLSDParseError("Encoded binary data: " + str(exc))
    except TypeError as exc:
        # convert exception class so it's more catchable
        return LLSDParseError("Bad binary data: " + str(exc))

def _date_to_python(node):
    "Convert date node to a python object."
    val = node.text or ''
    if not val:
        val = "1970-01-01T00:00:00Z"
    return _parse_datestr(val)
    

def _uri_to_python(node):
    "Convert uri node to a python object."
    val = node.text or ''
    return uri(val)

def _map_to_python(node):
    "Convert map node to a python object."
    result = {}
    for index in range(len(node))[::2]:
        if node[index].text is None:
            result[''] = _to_python(node[index+1])
        else:
            result[node[index].text] = _to_python(node[index+1])
    return result

def _array_to_python(node):
    "Convert array node to a python object."
    return [_to_python(child) for child in node]


NODE_HANDLERS = dict(
    undef=lambda x: None,
    boolean=_bool_to_python,
    integer=_int_to_python,
    real=_real_to_python,
    uuid=_uuid_to_python,
    string=_str_to_python,
    binary=_bin_to_python,
    date=_date_to_python,
    uri=_uri_to_python,
    map=_map_to_python,
    array=_array_to_python,
    )

def _to_python(node):
    "Convert node to a python object."
    return NODE_HANDLERS[node.tag](node)


if PY2:
    ALL_CHARS = str(bytearray(range(256)))
else:
    ALL_CHARS = bytes(range(256))
INVALID_XML_BYTES = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c'\
                    b'\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18'\
                    b'\x19\x1a\x1b\x1c\x1d\x1e\x1f'
INVALID_XML_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
def remove_invalid_xml_bytes(b):
    try:
        # Dropping chars that cannot be parsed later on.  The
        # translate() function was benchmarked to be the fastest way
        # to do this.
        return b.translate(ALL_CHARS, INVALID_XML_BYTES)
    except TypeError:
        # we get here if s is a unicode object (should be limited to
        # unit tests)
        return INVALID_XML_RE.sub('', b)


class LLSDBaseFormatter(object):
    """
    This base class cannot be instantiated on its own: it assumes a subclass
    containing methods with canonical names specified in self.__init__(). The
    role of this base class is to provide self.type_map based on the methods
    defined in its subclass.
    """
    def __init__(self):
        "Construct a new formatter dispatch table."
        self.type_map = {
            type(None) :          self.UNDEF,
            bool :                self.BOOLEAN,
            int :                 self.INTEGER,
            LongType :            self.INTEGER,
            float :               self.REAL,
            uuid.UUID :           self.UUID,
            binary :              self.BINARY,
            str :                 self.STRING,
            UnicodeType :         self.STRING,
            newstr :              self.STRING,
            uri :                 self.URI,
            datetime.datetime :   self.DATE,
            datetime.date :       self.DATE,
            list :                self.ARRAY,
            tuple :               self.ARRAY,
            types.GeneratorType : self.ARRAY,
            dict :                self.MAP,
            LLSD :                self.LLSD
            }


class LLSDXMLFormatter(LLSDBaseFormatter):
    """
    Class which implements LLSD XML serialization..

    http://wiki.secondlife.com/wiki/LLSD#XML_Serialization

    This class wraps both a pure python and c-extension for formatting
    a limited subset of python objects as application/llsd+xml. You do
    not generally need to make an instance of this object since the
    module level format_xml is the most convenient interface to this
    functionality.
    """

    def _elt(self, name, contents=None):
        "Serialize a single element."
        if not contents:
            return B("<%s />") % (name,)
        else:
            return B("<%s>%s</%s>") % (name, _str_to_bytes(contents), name)

    def xml_esc(self, v):
        "Escape string or unicode object v for xml output"

        # Use is_unicode() instead of is_string() because in python 2, str is
        # bytes, not unicode, and should not be "encode()"'d. attempts to
        # encode("utf-8") a bytes type will result in an implicit
        # decode("ascii") that will throw a UnicodeDecodeError if the string
        # contains non-ascii characters
        if is_unicode(v):
            # we need to drop these invalid characters because they
            # cannot be parsed (and encode() doesn't drop them for us)
            v = v.replace(u'\uffff', u'')
            v = v.replace(u'\ufffe', u'')
            v = v.encode('utf-8')
        v = remove_invalid_xml_bytes(v)
        return v.replace(b'&',b'&amp;').replace(b'<',b'&lt;').replace(b'>',b'&gt;')

    def LLSD(self, v):
        return self._generate(v.thing)
    def UNDEF(self, _v):
        return self._elt(b'undef')
    def BOOLEAN(self, v):
        if v:
            return self._elt(b'boolean', b'true')
        else:
            return self._elt(b'boolean', b'false')
    def INTEGER(self, v):
        return self._elt(b'integer', str(v))
    def REAL(self, v):
        return self._elt(b'real', repr(v))
    def UUID(self, v):
        if v.int == 0:
            return self._elt(b'uuid')
        else:
            return self._elt(b'uuid', str(v))
    def BINARY(self, v):
        return self._elt(b'binary', base64.b64encode(v).strip())
    def STRING(self, v):
        return self._elt(b'string', self.xml_esc(v))
    def URI(self, v):
        return self._elt(b'uri', self.xml_esc(str(v)))
    def DATE(self, v):
        return self._elt(b'date', _format_datestr(v))
    def ARRAY(self, v):
        return self._elt(
            b'array',
            b''.join([self._generate(item) for item in v]))
    def MAP(self, v):
        return self._elt(
            b'map',
            b''.join([B("%s%s") % (self._elt(b'key', self.xml_esc(UnicodeType(key))),
                               self._generate(value))
             for key, value in v.items()]))

    typeof = type
    def _generate(self, something):
        "Generate xml from a single python object."
        t = self.typeof(something)
        if t in self.type_map:
            return self.type_map[t](something)
        else:
            raise LLSDSerializationError(
                "Cannot serialize unknown type: %s (%s)" % (t, something))

    def _format(self, something):
        "Pure Python implementation of the formatter."
        return b'<?xml version="1.0" ?>' + self._elt(b"llsd", self._generate(something))

    def format(self, something):
        """
        Format a python object as application/llsd+xml

        :param something: A python object (typically a dict) to be serialized.
        :returns: Returns an XML formatted string.
        """
        return self._format(something)

_g_xml_formatter = None
def format_xml(something):
    """
    Format a python object as application/llsd+xml

    :param something: a python object (typically a dict) to be serialized.
    :returns: Returns an XML formatted string.

    Ssee http://wiki.secondlife.com/wiki/LLSD#XML_Serialization

    This function wraps both a pure python and c-extension for formatting
    a limited subset of python objects as application/llsd+xml.
    """
    global _g_xml_formatter
    if _g_xml_formatter is None:
        _g_xml_formatter = LLSDXMLFormatter()
    return _g_xml_formatter.format(something)

class LLSDXMLPrettyFormatter(LLSDXMLFormatter):
    """
    Class which implements 'pretty' LLSD XML serialization..

    See http://wiki.secondlife.com/wiki/LLSD#XML_Serialization

    The output conforms to the LLSD DTD, unlike the output from the
    standard python xml.dom DOM::toprettyxml() method which does not
    preserve significant whitespace. 

    This class is not necessarily suited for serializing very large objects.
    It sorts on dict (llsd map) keys alphabetically to ease human reading.
    """
    def __init__(self, indent_atom = None):
        "Construct a pretty serializer."
        # Call the super class constructor so that we have the type map
        super(LLSDXMLPrettyFormatter, self).__init__()

        # Override the type map to use our specialized formatters to
        # emit the pretty output.
        self.type_map[list] = self.PRETTY_ARRAY
        self.type_map[tuple] = self.PRETTY_ARRAY
        self.type_map[types.GeneratorType] = self.PRETTY_ARRAY,
        self.type_map[dict] = self.PRETTY_MAP

        # Private data used for indentation.
        self._indent_level = 1
        if indent_atom is None:
            self._indent_atom = b'  '
        else:
            self._indent_atom = indent_atom

    def _indent(self):
        "Return an indentation based on the atom and indentation level."
        return self._indent_atom * self._indent_level

    def PRETTY_ARRAY(self, v):
        "Recursively format an array with pretty turned on."
        rv = []
        rv.append(b'<array>\n')
        self._indent_level = self._indent_level + 1
        rv.extend([B("%s%s\n") %
                   (self._indent(),
                    self._generate(item))
                   for item in v])
        self._indent_level = self._indent_level - 1
        rv.append(self._indent())
        rv.append(b'</array>')
        return b''.join(rv)

    def PRETTY_MAP(self, v):
        "Recursively format a map with pretty turned on."
        rv = []
        rv.append(b'<map>\n')
        self._indent_level = self._indent_level + 1
        # list of keys
        keys = list(v)
        keys.sort()
        rv.extend([B("%s%s\n%s%s\n") %
                   (self._indent(),
                    self._elt(b'key', UnicodeType(key)),
                    self._indent(),
                    self._generate(v[key]))
                   for key in keys])
        self._indent_level = self._indent_level - 1
        rv.append(self._indent())
        rv.append(b'</map>')
        return b''.join(rv)

    def format(self, something):
        """
        Format a python object as application/llsd+xml

        :param something: a python object (typically a dict) to be serialized.
        :returns: Returns an XML formatted string.
        """
        data = []
        data.append(b'<?xml version="1.0" ?>\n<llsd>')
        data.append(self._generate(something))
        data.append(b'</llsd>\n')
        return b'\n'.join(data)

def format_pretty_xml(something):
    """
    Serialize a python object as 'pretty' application/llsd+xml.

    :param something: a python object (typically a dict) to be serialized.
    :returns: Returns an XML formatted string.

    See http://wiki.secondlife.com/wiki/LLSD#XML_Serialization

    The output conforms to the LLSD DTD, unlike the output from the
    standard python xml.dom DOM::toprettyxml() method which does not
    preserve significant whitespace. 
    This function is not necessarily suited for serializing very large
    objects. It sorts on dict (llsd map) keys alphabetically to ease human
    reading.
    """
    return LLSDXMLPrettyFormatter().format(something)

class LLSDNotationFormatter(LLSDBaseFormatter):
    """
    Serialize a python object as application/llsd+notation 

    See http://wiki.secondlife.com/wiki/LLSD#Notation_Serialization
    """
    def LLSD(self, v):
        return self._generate(v.thing)
    def UNDEF(self, v):
        return b'!'
    def BOOLEAN(self, v):
        if v:
            return b'true'
        else:
            return b'false'
    def INTEGER(self, v):
        return B("i%d") % v
    def REAL(self, v):
        return B("r%r") % v
    def UUID(self, v):
        # latin-1 is the byte-to-byte encoding, mapping \x00-\xFF ->
        # \u0000-\u00FF. It's also the fastest encoding, I believe, from
        # https://docs.python.org/3/library/codecs.html#encodings-and-unicode
        # UUID doesn't like the hex to be a bytes object, so I have to
        # convert it to a string. I chose latin-1 to exactly match the old
        # error behavior in case someone passes an invalid hex string, with
        # things other than 0-9a-fA-F, so that they will fail in the UUID
        # decode, rather than with a UnicodeError.
        return B("u%s") % str(v).encode('latin-1')
    def BINARY(self, v):
        return b'b64"' + base64.b64encode(v).strip() + b'"'

    def STRING(self, v):
        return B("'%s'") % _str_to_bytes(v).replace(b"\\", b"\\\\").replace(b"'", b"\\'")
    def URI(self, v):
        return B('l"%s"') % _str_to_bytes(v).replace(b"\\", b"\\\\").replace(b'"', b'\\"')
    def DATE(self, v):
        return B('d"%s"') % _format_datestr(v)
    def ARRAY(self, v):
        return B("[%s]") % b','.join([self._generate(item) for item in v])
    def MAP(self, v):
        return B("{%s}") % b','.join([B("'%s':%s") % (_str_to_bytes(UnicodeType(key)).replace(b"\\", b"\\\\").replace(b"'", b"\\'"), self._generate(value))
             for key, value in v.items()])

    def _generate(self, something):
        "Generate notation from a single python object."
        t = type(something)
        handler = self.type_map.get(t)
        if handler:
            return handler(something)
        else:
            try:
                return self.ARRAY(iter(something))
            except TypeError:
                raise LLSDSerializationError(
                    "Cannot serialize unknown type: %s (%s)" % (t, something))

    def format(self, something):
        """
        Format a python object as application/llsd+notation

        :param something: a python object (typically a dict) to be serialized.
        :returns: Returns a LLSD notation formatted string.
        """
        return self._generate(something)

def format_notation(something):
    """
    Format a python object as application/llsd+notation

    :param something: a python object (typically a dict) to be serialized.
    :returns: Returns a LLSD notation formatted string.

    See http://wiki.secondlife.com/wiki/LLSD#Notation_Serialization
    """
    return LLSDNotationFormatter().format(something)

def _hex_as_nybble(hex):
    "Accepts a single hex character and returns a nybble."
    if (hex >= b'0') and (hex <= b'9'):
        return ord(hex) - ord(b'0')
    elif (hex >= b'a') and (hex <=b'f'):
        return 10 + ord(hex) - ord(b'a')
    elif (hex >= b'A') and (hex <=b'F'):
        return 10 + ord(hex) - ord(b'A')
    else:
        raise LLSDParseError('Invalid hex character: %s' % hex)


class LLSDBaseParser(object):
    """
    Utility methods useful for parser subclasses.
    """
    def __init__(self):
        self._buffer = b''
        self._index  = 0

    def _error(self, message, offset=0):
        try:
            byte = self._buffer[self._index+offset]
        except IndexError:
            byte = None
        raise LLSDParseError("%s at byte %d: %s" % (message, self._index+offset, byte))

    def _peek(self, num=1):
        if num < 0:
            # There aren't many ways this can happen. The likeliest is that
            # we've just read garbage length bytes from a binary input string.
            # We happen to know that lengths are encoded as 4 bytes, so back
            # off by 4 bytes to try to point the user at the right spot.
            self._error("Invalid length field %d" % num, -4)
        if self._index + num > len(self._buffer):
            self._error("Trying to read past end of buffer")
        return self._buffer[self._index:self._index + num]

    def _getc(self, num=1):
        chars = self._peek(num)
        self._index += num
        return chars

    # map char following escape char to corresponding character
    _escaped = {
        b'a': b'\a',
        b'b': b'\b',
        b'f': b'\f',
        b'n': b'\n',
        b'r': b'\r',
        b't': b'\t',
        b'v': b'\v',
        }

    def _parse_string_delim(self, delim):
        "Parse a delimited string."
        parts = bytearray()
        found_escape = False
        found_hex = False
        found_digit = False
        byte = 0
        while True:
            cc = self._getc()
            if found_escape:
                if found_hex:
                    if found_digit:
                        found_escape = False
                        found_hex = False
                        found_digit = False
                        byte <<= 4
                        byte |= _hex_as_nybble(cc)
                        parts.append(byte)
                        byte = 0
                    else:
                        found_digit = True
                        byte = _hex_as_nybble(cc)
                elif cc == b'x':
                    found_hex = True
                else:
                    found_escape = False
                    # escape char preceding anything other than the chars in
                    # _escaped just results in that same char without the
                    # escape char
                    parts.extend(self._escaped.get(cc, cc))
            elif cc == b'\\':
                found_escape = True
            elif cc == delim:
                break
            else:
                parts.extend(cc)
        try:
            return parts.decode('utf-8')
        except UnicodeDecodeError as exc:
            self._error(exc)


class LLSDBinaryParser(LLSDBaseParser):
    """
    Parse application/llsd+binary to a python object.

    See http://wiki.secondlife.com/wiki/LLSD#Binary_Serialization
    """
    def __init__(self):
        super(LLSDBinaryParser, self).__init__()
        # One way of dispatching based on the next character we see would be a
        # dict lookup, and indeed that's the best way to express it in source.
        _dispatch_dict = {
            b'{': self._parse_map,
            b'[': self._parse_array,
            b'!': lambda: None,
            b'0': lambda: False,
            b'1': lambda: True,
            # 'i' = integer
            b'i': lambda: struct.unpack("!i", self._getc(4))[0],
            # 'r' = real number
            b'r': lambda: struct.unpack("!d", self._getc(8))[0],
            # 'u' = uuid
            b'u': lambda: uuid.UUID(bytes=self._getc(16)),
            # 's' = string
            b's': self._parse_string,
            # delimited/escaped string
            b"'": lambda: self._parse_string_delim(b"'"),
            b'"': lambda: self._parse_string_delim(b'"'),
            # 'l' = uri
            b'l': lambda: uri(self._parse_string()),
            # 'd' = date in seconds since epoch
            b'd': self._parse_date,
            # 'b' = binary
            # *NOTE: if not self._keep_binary, maybe have a binary placeholder
            # which has the length.
            b'b': lambda: binary(self._parse_string_raw()) if self._keep_binary else None,
            }
        # But in fact it should be even faster to construct a list indexed by
        # ord(char). Start by filling it with the 'else' case. Use offset=-1
        # because by the time we perform this lookup, we've scanned past the
        # lookup char.
        self._dispatch = 256*[lambda: self._error("invalid binary token", -1)]
        # Now use the entries in _dispatch_dict to set the corresponding
        # entries in _dispatch.
        for c, func in _dispatch_dict.items():
            self._dispatch[ord(c)] = func

    def parse(self, buffer, ignore_binary = False):
        """
        This is the basic public interface for parsing.

        :param buffer: the binary data to parse in an indexable sequence.
        :param ignore_binary: parser throws away data in llsd binary nodes.
        :returns: returns a python object.
        """
        self._buffer = buffer
        self._index = 0
        self._keep_binary = not ignore_binary
        try:
            return self._parse()
        except struct.error as exc:
            self._error(exc)

    def _parse(self):
        "The actual parser which is called recursively when necessary."
        cc = self._getc()
        try:
            func = self._dispatch[ord(cc)]
        except IndexError:
            self._error("invalid binary token", -1)
        else:
            return func()

    def _parse_map(self):
        "Parse a single llsd map"
        rv = {}
        size = struct.unpack("!i", self._getc(4))[0]
        count = 0
        cc = self._getc()
        key = b''
        while (cc != b'}') and (count < size):
            if cc == b'k':
                key = self._parse_string()
            elif cc in (b"'", b'"'):
                key = self._parse_string_delim(cc)
            else:
                self._error("invalid map key", -1)
            value = self._parse()
            rv[key] = value
            count += 1
            cc = self._getc()
        if cc != b'}':
            self._error("invalid map close token")
        return rv

    def _parse_array(self):
        "Parse a single llsd array"
        rv = []
        size = struct.unpack("!i", self._getc(4))[0]
        count = 0
        cc = self._peek()
        while (cc != b']') and (count < size):
            rv.append(self._parse())
            count += 1
            cc = self._peek()
        if cc != b']':
            self._error("invalid array close token")
        self._index += 1
        return rv

    def _parse_string(self):
        try:
            return self._parse_string_raw().decode('utf-8')
        except UnicodeDecodeError as exc:
            self._error(exc)

    def _parse_string_raw(self):
        "Parse a string which has the leadings size indicator"
        try:
            size = struct.unpack("!i", self._getc(4))[0]
        except struct.error as exc:
            # convert exception class for client convenience
            self._error("struct " + str(exc))
        rv = self._getc(size)
        return rv

    def _parse_date(self):
        seconds = struct.unpack("<d", self._getc(8))[0]
        try:
            return datetime.datetime.utcfromtimestamp(seconds)
        except OverflowError as exc:
            # A garbage seconds value can cause utcfromtimestamp() to raise
            # OverflowError: timestamp out of range for platform time_t
            self._error(exc, -8)


class LLSDNotationParser(LLSDBaseParser):
    """
    Parse LLSD notation.

    See http://wiki.secondlife.com/wiki/LLSD#Notation_Serialization

    * map: { string:object, string:object }
    * array: [ object, object, object ]
    * undef: !
    * boolean: true | false | 1 | 0 | T | F | t | f | TRUE | FALSE
    * integer: i####
    * real: r####
    * uuid: u####
    * string: "g\'day" | 'have a "nice" day' | s(size)"raw data"
    * uri: l"escaped"
    * date: d"YYYY-MM-DDTHH:MM:SS.FFZ"
    * binary: b##"ff3120ab1" | b(size)"raw data"
    """
    def __init__(self):
        super(LLSDNotationParser, self).__init__()
        # Like LLSDBinaryParser, we want to dispatch based on the current
        # character.
        _dispatch_dict = {
            # map
            b'{': self._parse_map,
            # array
            b'[': self._parse_array,
            # undefined -- have to eat the '!'
            b'!': lambda: self._skip_then(None),
            # false -- have to eat the '0'
            b'0': lambda: self._skip_then(False),
            # true -- have to eat the '1'
            b'1': lambda: self._skip_then(True),
            # false, must check for F|f|false|FALSE
            b'F': lambda: self._get_re("'false'", _false_regex, False),
            b'f': lambda: self._get_re("'false'", _false_regex, False),
            # true, must check for T|t|true|TRUE
            b'T': lambda: self._get_re("'true'", _true_regex, True),
            b't': lambda: self._get_re("'true'", _true_regex, True),
            # 'i' = integer
            b'i': self._parse_integer,
            # 'r' = real number
            b'r': self._parse_real,
            # 'u' = uuid
            b'u': self._parse_uuid,
            # string
            b"'": self._parse_string,
            b'"': self._parse_string,
            b's': self._parse_string,
            # 'l' = uri
            b'l': self._parse_uri,
            # 'd' = date in seconds since epoch
            b'd': self._parse_date,
            # 'b' = binary
            b'b': self._parse_binary,
            }
        # Like LLSDBinaryParser, construct a lookup list from this dict. Start
        # by filling with the 'else' case.
        self._dispatch = 256*[lambda: self._error("Invalid notation token")]
        # Then fill in specific entries based on the dict above.
        for c, func in _dispatch_dict.items():
            self._dispatch[ord(c)] = func

    def parse(self, buffer, ignore_binary = False):
        """
        This is the basic public interface for parsing.
        
        :param buffer: the notation string to parse.
        :param ignore_binary: parser throws away data in llsd binary nodes.
        :returns: returns a python object.
        """
        if buffer == b"":
            return False

        self._buffer = buffer
        self._index = 0
        return self._parse()

    def _get_until(self, delim):
        start = self._index
        end = self._buffer.find(delim, start)
        if end == -1:
            return None
        else:
            self._index = end + 1
            return self._buffer[start:end]

    def _skip_then(self, value):
        # We've already _peek()ed at the current character, which is how we
        # decided to call this method. Skip past it and return constant value.
        self._getc()
        return value

    def _get_re(self, desc, regex, override=None):
        match = re.match(regex, self._buffer[self._index:])
        if not match:
            self._error("Invalid %s token" % desc)
        else:
            self._index += match.end()
            return override if override is not None else match.group(0)

    def _parse(self):
        "The notation parser workhorse."
        cc = self._peek()
        try:
            func = self._dispatch[ord(cc)]
        except IndexError:
            # output error if the token was out of range
            self._error("Invalid notation token")
        else:
            return func()

    def _parse_binary(self):
        "parse a single binary object."
        
        self._getc()    # eat the beginning 'b'
        cc = self._peek()
        if cc == b'(':
            # parse raw binary
            paren = self._getc()

            # grab the 'expected' size of the binary data
            size = self._get_until(b')')
            if size == None:
                self._error("Invalid binary size")
            size = int(size)

            # grab the opening quote
            q = self._getc()
            if q != b'"':
                self._error('Expected " to start binary value')

            # grab the data
            data = self._getc(size)

            # grab the closing quote
            q = self._getc()
            if q != b'"':
                self._error('Expected " to end binary value')

            return binary(data)

        else:
            # get the encoding base
            base = self._getc(2)
            try:
                decoder = {
                    b'16': base64.b16decode,
                    b'64': base64.b64decode,
                    }[base]
            except KeyError:
                self._error("Parser doesn't support base %s encoding" %
                            base.decode('latin-1'))

            # grab the double quote
            q = self._getc()
            if q != b'"':
                self._error('Expected " to start binary value')

            # grab the encoded data
            encoded = self._get_until(q)

            try:
                return binary(decoder(encoded or b''))
            except binascii.Error as exc:
                # convert exception class so it's more catchable
                self._error("Encoded binary data: " + str(exc))
            except TypeError as exc:
                # convert exception class so it's more catchable
                self._error("Bad binary data: " + str(exc))
    
    def _parse_map(self):
        """
        parse a single map

        map: { string:object, string:object }
        """
        rv = {}
        key = b''
        found_key = False
        self._getc()   # eat the beginning '{'
        cc = self._peek()
        while (cc != b'}'):
            if cc is None:
                self._error("Unclosed map")
            if not found_key:
                if cc in (b"'", b'"', b's'):
                    key = self._parse_string()
                    found_key = True
                elif cc.isspace() or cc == b',':
                    self._getc()    # eat the character
                    pass
                else:
                    self._error("Invalid map key")
            elif cc.isspace():
                self._getc()    # eat the space
                pass
            elif cc == b':':
                self._getc()    # eat the ':'
                value = self._parse()
                rv[key] = value
                found_key = False
            else:
                self._error("missing separator")
            cc = self._peek()

        if self._getc() != b'}':
            self._error("Invalid map close token")

        return rv

    def _parse_array(self):
        """
        parse a single array.

        array: [ object, object, object ]
        """
        rv = []
        self._getc()    # eat the beginning '['
        cc = self._peek()
        while (cc != b']'):
            if cc is None:
                self._error('Unclosed array')
            if cc.isspace() or cc == b',':
                self._getc()
                cc = self._peek()
                continue
            rv.append(self._parse())
            cc = self._peek()

        if self._getc() != b']':
            self._error("Invalid array close token")
        return rv

    def _parse_uuid(self):
        "Parse a uuid."
        self._getc()    # eat the beginning 'u'
        # see comment on LLSDNotationFormatter.UUID() re use of latin-1
        return uuid.UUID(hex=self._getc(36).decode('latin-1'))

    def _parse_uri(self):
        "Parse a URI."
        self._getc()    # eat the beginning 'l'
        return uri(self._parse_string())

    def _parse_date(self):
        "Parse a date."
        self._getc()    # eat the beginning 'd'
        datestr = self._parse_string()
        return _parse_datestr(datestr)

    def _parse_real(self):
        "Parse a floating point number."
        self._getc()    # eat the beginning 'r'
        return float(self._get_re("real", _real_regex))

    def _parse_integer(self):
        "Parse an integer."
        self._getc()    # eat the beginning 'i'
        return int(self._get_re("integer", _int_regex))

    def _parse_string(self):
        """
        Parse a string

        string: "g\'day" | 'have a "nice" day' | s(size)"raw data"
        """
        rv = ""
        delim = self._peek()
        if delim in (b"'", b'"'):
            delim = self._getc()        # eat the beginning delim
            rv = self._parse_string_delim(delim)
        elif delim == b's':
            rv = self._parse_string_raw()
        else:
            self._error("invalid string token")

        return rv

    def _parse_string_raw(self):
        """
        Parse a sized specified string.

        string: s(size)"raw data"
        """ 
        self._getc()    # eat the beginning 's'
        # Read the (size) portion.
        cc = self._getc()
        if cc != b'(':
            self._error("Invalid string token")

        size = self._get_until(b')')
        if size == None:
            self._error("Invalid string size")
        size = int(size)

        delim = self._getc()
        if delim not in (b"'", b'"'):
            self._error("Invalid string token")

        rv = self._getc(size)
        cc = self._getc()
        if cc != delim:
            self._error("Invalid string closure token")
        try:
            return rv.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise LLSDParseError(exc)

def format_binary(something):
    """
    Format application/llsd+binary to a python object.
 
    See http://wiki.secondlife.com/wiki/LLSD#Binary_Serialization

   :param something: a python object (typically a dict) to be serialized.
   :returns: Returns a LLSD binary formatted string.
    """
    return b'<?llsd/binary?>\n' + _format_binary_recurse(something)

def _format_binary_recurse(something):
    "Binary formatter workhorse."
    def _format_list(something):
        array_builder = []
        array_builder.append(b'[' + struct.pack('!i', len(something)))
        for item in something:
            array_builder.append(_format_binary_recurse(item))
        array_builder.append(b']')
        return b''.join(array_builder)

    if something is None:
        return b'!'
    elif isinstance(something, LLSD):
        return _format_binary_recurse(something.thing)
    elif isinstance(something, bool):
        if something:
            return b'1'
        else:
            return b'0'
    elif is_integer(something):
        try:
            return b'i' + struct.pack('!i', something)
        except (OverflowError, struct.error) as exc:
            raise LLSDSerializationError(str(exc), something)
    elif isinstance(something, float):
        try:
            return b'r' + struct.pack('!d', something)
        except SystemError as exc:
            raise LLSDSerializationError(str(exc), something)
    elif isinstance(something, uuid.UUID):
        return b'u' + something.bytes
    elif isinstance(something, binary):
        return b'b' + struct.pack('!i', len(something)) + something
    elif is_string(something):
        something = _str_to_bytes(something)
        return b's' + struct.pack('!i', len(something)) + something
    elif isinstance(something, uri):
        return b'l' + struct.pack('!i', len(something)) + something
    elif isinstance(something, datetime.datetime):
        seconds_since_epoch = calendar.timegm(something.utctimetuple()) \
                              + something.microsecond // 1e6
        return b'd' + struct.pack('<d', seconds_since_epoch)
    elif isinstance(something, datetime.date):
        seconds_since_epoch = calendar.timegm(something.timetuple())
        return b'd' + struct.pack('<d', seconds_since_epoch)
    elif isinstance(something, (list, tuple)):
        return _format_list(something)
    elif isinstance(something, dict):
        map_builder = []
        map_builder.append(b'{' + struct.pack('!i', len(something)))
        for key, value in something.items():
            key = _str_to_bytes(key)
            map_builder.append(b'k' + struct.pack('!i', len(key)) + key)
            map_builder.append(_format_binary_recurse(value))
        map_builder.append(b'}')
        return b''.join(map_builder)
    else:
        try:
            return _format_list(list(something))
        except TypeError:
            raise LLSDSerializationError(
                "Cannot serialize unknown type: %s (%s)" %
                (type(something), something))

def _startswith(startstr, something):
    if hasattr(something, 'startswith'):
        return something.startswith(startstr)
    else:
        pos = something.tell()
        s = something.read(len(startstr))
        something.seek(pos, os.SEEK_SET)
        return (s == startstr)

def parse_binary(something):
    """
    This is the basic public interface for parsing llsd+binary.

    :param something: The data to parse in an indexable sequence.
    :returns: Returns a python object.
    """
    if _startswith(b'<?llsd/binary?>', something):
        just_binary = something.split(b'\n', 1)[1]
    else:
        just_binary = something
    return LLSDBinaryParser().parse(just_binary)


declaration_regex = re.compile(br'^\s*(?:<\?[\x09\x0A\x0D\x20-\x7e]+\?>)|(?:<llsd>)')
def validate_xml_declaration(something):
    if not declaration_regex.match(something):
        raise LLSDParseError("Invalid XML Declaration")

def parse_xml(something):
    """
    This is the basic public interface for parsing llsd+xml.

    :param something: The data to parse.
    :returns: Returns a python object.
    """
    try:
        # validate xml declaration manually until http://bugs.python.org/issue7138 is fixed
        validate_xml_declaration(something)
        return _to_python(fromstring(something)[0])
    except ElementTreeError as err:
        raise LLSDParseError(*err.args)

def parse_notation(something):
    """
    This is the basic public interface for parsing llsd+notation.

    :param something: The data to parse.
    :returns: Returns a python object.
    """
    return LLSDNotationParser().parse(something)

def parse(something, mime_type = None):
    """
    This is the basic public interface for parsing llsd.

    :param something: The data to parse. This is expected to be bytes, not strings
    :param mime_type: The mime_type of the data if it is known.
    :returns: Returns a python object.
    
    Python 3 Note: when reading LLSD from a file, use open()'s 'rb' mode explicitly
    """
    if mime_type in (XML_MIME_TYPE, 'application/llsd'):
        return parse_xml(something)
    elif mime_type == BINARY_MIME_TYPE:
        return parse_binary(something)
    elif mime_type == NOTATION_MIME_TYPE:
        return parse_notation(something)
    #elif content_type == 'application/json':
    #    return parse_notation(something)
    try:
        something = something.lstrip()   #remove any pre-trailing whitespace
        if _startswith(b'<?llsd/binary?>', something):
            return parse_binary(something)
        # This should be better.
        elif _startswith(b'<', something):
            return parse_xml(something)
        else:
            return parse_notation(something)
    except KeyError as e:
        raise LLSDParseError('LLSD could not be parsed: %s' % (e,))
    except TypeError as e:
        raise LLSDParseError('Input stream not of type bytes. %s' % (e,))

class LLSD(object):
    "Simple wrapper class for a thing."
    def __init__(self, thing=None):
        self.thing = thing

    def __bytes__(self):
        return self.as_xml(self.thing)

    def __str__(self):
        return self.__bytes__().decode()

    parse = staticmethod(parse)
    as_xml = staticmethod(format_xml)
    as_pretty_xml = staticmethod(format_pretty_xml)
    as_binary = staticmethod(format_binary)
    as_notation = staticmethod(format_notation)

undef = LLSD(None)
