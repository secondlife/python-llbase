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


import base64
import binascii
import calendar
import datetime
import re
import struct
import time
import types
import uuid
import urlparse
import os
import exceptions

from fastest_elementtree import ElementTreeError, fromstring

try:
    import _cllsd as cllsd
except ImportError:
    cllsd = None

XML_MIME_TYPE = 'application/llsd+xml'
BINARY_MIME_TYPE = 'application/llsd+binary'
NOTATION_MIME_TYPE = 'application/llsd+notation'

class LLSDParseError(Exception):
    "Exception raised when the parser fails."
    pass

class LLSDSerializationError(TypeError):
    "Exception raised when serialization fails."
    pass


class binary(str):
    "Simple wrapper for llsd.binary data."
    pass

class uri(str):
    "Simple wrapper for llsd.uri data."
    pass

_int_regex = re.compile(r"[-+]?\d+")
_real_regex = re.compile(r"[-+]?(?:(\d+(\.\d*)?|\d*\.\d+)([eE][-+]?\d+)?)|[-+]?inf|[-+]?nan")
_alpha_regex = re.compile(r"[a-zA-Z]+")
_true_regex = re.compile(r"TRUE|true|\b[Tt]\b")
_false_regex = re.compile(r"FALSE|false|\b[Ff]\b")
_date_regex = re.compile(r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T"
                        r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
                        r"(?P<second_float>(\.\d+)?)Z")
#date: d"YYYY-MM-DDTHH:MM:SS.FFFFFFZ"

def _format_datestr(v):
    """
    Formats a datetime or date object into the string format shared by
    xml and notation serializations.
    """
    if not isinstance(v, datetime.date) and not isinstance(v, datetime.datetime):
        raise LLSDParseError("invalid date string %s passed to date formatter" % s)
    
    if not isinstance(v, datetime.datetime):
        v = datetime.datetime.combine(v, datetime.time(0))
    
    return v.isoformat() + 'Z'

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
    if val in ('1', '1.0', 'true'):
        return True
    else:
        return False

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
    except binascii.Error, exc:
        # convert exception class so it's more catchable
        return LLSDParseError("Encoded binary data: " + str(exc))
    except exceptions.TypeError, exc:
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


ALL_CHARS = "".join([chr(x) for x in range(256)])
INVALID_XML_BYTES = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c'\
                    '\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18'\
                    '\x19\x1a\x1b\x1c\x1d\x1e\x1f'
INVALID_XML_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
def remove_invalid_xml_bytes(s):
    try:
        # Dropping chars that cannot be parsed later on.  The
        # translate() function was benchmarked to be the fastest way
        # to do this.
        return s.translate(ALL_CHARS, INVALID_XML_BYTES)
    except TypeError:
        # we get here if s is a unicode object (should be limited to
        # unit tests)
        return INVALID_XML_RE.sub('', s)


class LLSDXMLFormatter(object):
    """
    Class which implements LLSD XML serialization..

    http://wiki.secondlife.com/wiki/LLSD#XML_Serialization

    This class wraps both a pure python and c-extension for formatting
    a limited subset of python objects as application/llsd+xml. You do
    not generally need to make an instance of this object since the
    module level format_xml is the most convenient interface to this
    functionality.
    """

    def __init__(self):
        "Construct a new formatter."
        self.type_map = {
            type(None) : self.UNDEF,
            bool : self.BOOLEAN,
            int : self.INTEGER,
            long : self.INTEGER,
            float : self.REAL,
            uuid.UUID : self.UUID,
            binary : self.BINARY,
            str : self.STRING,
            unicode : self.STRING,
            uri : self.URI,
            datetime.datetime : self.DATE,
            datetime.date : self.DATE,
            list : self.ARRAY,
            tuple : self.ARRAY,
            types.GeneratorType : self.ARRAY,
            dict : self.MAP,
            LLSD : self.LLSD
            }

    def _elt(self, name, contents=None):
        "Serialize a single element."
        if contents in (None, ''):
            return "<%s />" % (name,)
        else:
            if type(contents) is unicode:
                contents = contents.encode('utf-8')
            return "<%s>%s</%s>" % (name, contents, name)

    def xml_esc(self, v):
        "Escape string or unicode object v for xml output"
        if type(v) is unicode:
            # we need to drop these invalid characters because they
            # cannot be parsed (and encode() doesn't drop them for us)
            v = v.replace(u'\uffff', '')
            v = v.replace(u'\ufffe', '')
            v = v.encode('utf-8')
        v = remove_invalid_xml_bytes(v)
        return v.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

    def LLSD(self, v):
        return self._generate(v.thing)
    def UNDEF(self, _v):
        return self._elt('undef')
    def BOOLEAN(self, v):
        if v:
            return self._elt('boolean', 'true')
        else:
            return self._elt('boolean', 'false')
    def INTEGER(self, v):
        return self._elt('integer', v)
    def REAL(self, v):
        return self._elt('real', repr(v))
    def UUID(self, v):
        if v.int == 0:
            return self._elt('uuid')
        else:
            return self._elt('uuid', v)
    def BINARY(self, v):
        return self._elt('binary', base64.b64encode(v).strip())
    def STRING(self, v):
        return self._elt('string', self.xml_esc(v))
    def URI(self, v):
        return self._elt('uri', self.xml_esc(str(v)))
    def DATE(self, v):
        return self._elt('date', _format_datestr(v))
    def ARRAY(self, v):
        return self._elt(
            'array',
            ''.join([self._generate(item) for item in v]))
    def MAP(self, v):
        return self._elt(
            'map',
            ''.join(["%s%s" % (self._elt('key', self.xml_esc(key)),
                               self._generate(value))
             for key, value in v.items()]))

    typeof = type
    def _generate(self, something):
        "Generate xml from a single python object."
        t = self.typeof(something)
        if self.type_map.has_key(t):
            return self.type_map[t](something)
        else:
            raise LLSDSerializationError(
                "Cannot serialize unknown type: %s (%s)" % (t, something))

    def _format(self, something):
        "Pure Python implementation of the formatter."
        return '<?xml version="1.0" ?>' + self._elt("llsd", self._generate(something))

    def format(self, something):
        """
        Format a python object as application/llsd+xml

        :param something: A python object (typically a dict) to be serialized.
        :returns: Returns an XML formatted string.
        """
        if cllsd:
            return cllsd.llsd_to_xml(something)
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

    This class is not necessarily suited for serializing very large
    objects. It is not optimized by the cllsd module, and sorts on
    dict (llsd map) keys alphabetically to ease human reading.
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
            self._indent_atom = '  '
        else:
            self._indent_atom = indent_atom

    def _indent(self):
        "Return an indentation based on the atom and indentation level."
        return self._indent_atom * self._indent_level

    def PRETTY_ARRAY(self, v):
        "Recursively format an array with pretty turned on."
        rv = []
        rv.append('<array>\n')
        self._indent_level = self._indent_level + 1
        rv.extend(["%s%s\n" %
                   (self._indent(),
                    self._generate(item))
                   for item in v])
        self._indent_level = self._indent_level - 1
        rv.append(self._indent())
        rv.append('</array>')
        return ''.join(rv)

    def PRETTY_MAP(self, v):
        "Recursively format a map with pretty turned on."
        rv = []
        rv.append('<map>\n')
        self._indent_level = self._indent_level + 1
        keys = v.keys()
        keys.sort()
        rv.extend(["%s%s\n%s%s\n" %
                   (self._indent(),
                    self._elt('key', key),
                    self._indent(),
                    self._generate(v[key]))
                   for key in keys])
        self._indent_level = self._indent_level - 1
        rv.append(self._indent())
        rv.append('</map>')
        return ''.join(rv)

    def format(self, something):
        """
        Format a python object as application/llsd+xml

        :param something: a python object (typically a dict) to be serialized.
        :returns: Returns an XML formatted string.
        """
        data = []
        data.append('<?xml version="1.0" ?>\n<llsd>')
        data.append(self._generate(something))
        data.append('</llsd>\n')
        return '\n'.join(data)

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
    objects. It is not optimized by the cllsd module, and sorts on
    dict (llsd map) keys alphabetically to ease human reading.
    """
    return LLSDXMLPrettyFormatter().format(something)

class LLSDNotationFormatter(object):
    """
    Serialize a python object as application/llsd+notation 

    See http://wiki.secondlife.com/wiki/LLSD#Notation_Serialization
    """
    def __init__(self):
        "Construct a notation serializer."
        self.type_map = {
            type(None) : self.UNDEF,
            bool : self.BOOLEAN,
            int : self.INTEGER,
            long : self.INTEGER,
            float : self.REAL,
            uuid.UUID : self.UUID,
            binary : self.BINARY,
            str : self.STRING,
            unicode : self.STRING,
            uri : self.URI,
            datetime.datetime : self.DATE,
            datetime.date : self.DATE,
            list : self.ARRAY,
            tuple : self.ARRAY,
            types.GeneratorType : self.ARRAY,
            dict : self.MAP,
            LLSD : self.LLSD
        }

    def LLSD(self, v):
        return self._generate(v.thing)
    def UNDEF(self, v):
        return '!'
    def BOOLEAN(self, v):
        if v:
            return 'true'
        else:
            return 'false'
    def INTEGER(self, v):
        return "i%s" % v
    def REAL(self, v):
        return "r%r" % v
    def UUID(self, v):
        return "u%s" % v
    def BINARY(self, v):
        return 'b64"' + base64.b64encode(v).strip() + '"'

    def STRING(self, v):
        if isinstance(v, unicode):
            v = v.encode('utf-8')
        return "'%s'" % v.replace("\\", "\\\\").replace("'", "\\'")
    def URI(self, v):
        return 'l"%s"' % str(v).replace("\\", "\\\\").replace('"', '\\"')
    def DATE(self, v):
        return 'd"%s"' % _format_datestr(v)
    def ARRAY(self, v):
        return "[%s]" % ','.join([self._generate(item) for item in v])
    def MAP(self, v):
        def fix(key):
            if isinstance(key, unicode):
                return key.encode('utf-8')
            return key
        return "{%s}" % ','.join(["'%s':%s" % (fix(key).replace("\\", "\\\\").replace("'", "\\'"), self._generate(value))
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
    if (hex >= '0') and (hex <= '9'):
        return ord(hex) - ord('0')
    elif (hex >= 'a') and (hex <='f'):
        return 10 + ord(hex) - ord('a')
    elif (hex >= 'A') and (hex <='F'):
        return 10 + ord(hex) - ord('A')
    else:
        raise LLSDParseError('Invalid hex character: %s' % hex)

class LLSDBinaryParser(object):
    """
    Parse application/llsd+binary to a python object.

    See http://wiki.secondlife.com/wiki/LLSD#Binary_Serialization
    """
    def __init__(self):
        pass

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
        except struct.error, exc:
            raise LLSDParseError(exc)

    def _parse(self):
        "The actual parser which is called recursively when necessary."
        cc = self._buffer[self._index]
        self._index += 1
        if cc == '{':
            try:
                return self._parse_map()
            except IndexError:
                raise LLSDParseError("Found unterminated map ")
        elif cc == '[':
            return self._parse_array()
        elif cc == '!':
            return None
        elif cc == '0':
            return False
        elif cc == '1':
            return True
        elif cc == 'i':
            # 'i' = integer
            idx = self._index
            self._index += 4
            return struct.unpack("!i", self._buffer[idx:idx+4])[0]
        elif cc == ('r'):
            # 'r' = real number
            idx = self._index
            self._index += 8
            return struct.unpack("!d", self._buffer[idx:idx+8])[0]
        elif cc == 'u':
            # 'u' = uuid
            idx = self._index
            self._index += 16
            return uuid.UUID(bytes=self._buffer[idx:idx+16])
        elif cc == 's':
            # 's' = string
            return self._parse_string()
        elif cc in ("'", '"'):
            # delimited/escaped string
            return self._parse_string_delim(cc)
        elif cc == 'l':
            # 'l' = uri
            return uri(self._parse_string())
        elif cc == ('d'):
            # 'd' = date in seconds since epoch
            idx = self._index
            self._index += 8
            seconds = struct.unpack("<d", self._buffer[idx:idx+8])[0]
            return datetime.datetime.utcfromtimestamp(seconds)
        elif cc == 'b':
            b = binary(self._parse_string_raw())
            if self._keep_binary:
                return b
            # *NOTE: maybe have a binary placeholder which has the
            # length.
            return None
        else:
            raise LLSDParseError("invalid binary token at byte %d: %d" % (
                self._index - 1, ord(cc)))

    def _parse_map(self):
        "Parse a single llsd map"
        rv = {}
        size = struct.unpack("!i", self._buffer[self._index:self._index+4])[0]
        self._index += 4
        count = 0
        cc = self._buffer[self._index]
        self._index += 1
        key = ''
        while (cc != '}') and (count < size):
            if cc == 'k':
                key = self._parse_string()
            elif cc in ("'", '"'):
                key = self._parse_string_delim(cc)
            else:
                raise LLSDParseError("invalid map key at byte %d." % (
                    self._index - 1,))
            value = self._parse()
            rv[key] = value
            count += 1
            cc = self._buffer[self._index]
            self._index += 1
        if cc != '}':
            raise LLSDParseError("invalid map close token at byte %d." % (
                self._index,))
        return rv

    def _parse_array(self):
        "Parse a single llsd array"
        rv = []
        size = struct.unpack("!i", self._buffer[self._index:self._index+4])[0]
        self._index += 4
        count = 0
        cc = self._buffer[self._index]
        while (cc != ']') and (count < size):
            rv.append(self._parse())
            count += 1
            cc = self._buffer[self._index]
        if cc != ']':
            raise LLSDParseError("invalid array close token at byte %d." % (
                self._index,))
        self._index += 1
        return rv

    def _parse_string(self):
        try:
            return self._parse_string_raw().decode('utf-8')
        except UnicodeDecodeError, exc:
            raise LLSDParseError(exc)

    def _parse_string_raw(self):
        "Parse a string which has the leadings size indicator"
        try:
            size = struct.unpack("!i", self._buffer[self._index:self._index+4])[0]
        except struct.error, exc:
            # convert exception class for client convenience
            raise LLSDParseError("struct " + str(exc))
        self._index += 4
        rv = self._buffer[self._index:self._index+size]
        self._index += size
        return rv

    def _parse_string_delim(self, delim):
        "Parse a delimited string."
        parts = []
        found_escape = False
        found_hex = False
        found_digit = False
        byte = 0
        while True:
            cc = self._buffer[self._index]
            self._index += 1
            if found_escape:
                if found_hex:
                    if found_digit:
                        found_escape = False
                        found_hex = False
                        found_digit = False
                        byte <<= 4
                        byte |= _hex_as_nybble(cc)
                        parts.append(chr(byte))
                        byte = 0
                    else:
                        found_digit = True
                        byte = _hex_as_nybble(cc)
                elif cc == 'x':
                    found_hex = True
                else:
                    if cc == 'a':
                        parts.append('\a')
                    elif cc == 'b':
                        parts.append('\b')
                    elif cc == 'f':
                        parts.append('\f')
                    elif cc == 'n':
                        parts.append('\n')
                    elif cc == 'r':
                        parts.append('\r')
                    elif cc == 't':
                        parts.append('\t')
                    elif cc == 'v':
                        parts.append('\v')
                    else:
                        parts.append(cc)
                    found_escape = False
            elif cc == '\\':
                found_escape = True
            elif cc == delim:
                break
            else:
                parts.append(cc)
        try:
            return ''.join(parts).decode('utf-8')
        except UnicodeDecodeError, exc:
            raise LLSDParseError(exc)


class LLSDNotationParser(object):
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
        "Construct a notation parser"
        pass

    def parse(self, buffer, ignore_binary = False):
        """
        This is the basic public interface for parsing.
        
        :param buffer: the notation string to parse.
        :param ignore_binary: parser throws away data in llsd binary nodes.
        :returns: returns a python object.
        """
        if buffer == "":
            return False

        self._buffer = buffer
        self._index = 0
        return self._parse()

    def _error(self, message):
        raise LLSDParseError("%s at index %d" % (message, self._index))

    def _peek(self):
        if self._index >= len(self._buffer):
            self._error("unexpected end of data")
        return self._buffer[self._index]

    def _getc(self, num=1):
        if self._index == len(self._buffer):
            self._error("Unexpected end of data")
        if self._index + num > len(self._buffer):
            self._error("Trying to read past end of buffer")
        chars = self._buffer[self._index:self._index + num]
        self._index += num
        return chars

    def _get_until(self, delim):
        start = self._index
        end = self._buffer.find(delim, start)
        if end == -1:
            return None
        else:
            self._index = end + 1
            return self._buffer[start:end]

    def _get_re(self, regex):
        match = re.match(regex, self._buffer[self._index:])
        if not match:
            return None
        else:
            self._index += match.end()
            return match.group(0)

    def _parse(self):
        "The notation parser workhorse."
        cc = self._peek()
        if cc == '{':
            # map
            return self._parse_map()
        elif cc == '[':
            # array
           return self._parse_array()
        elif cc == '!':
            # undefined
            self._getc() # eat the '!'
            return None
        elif cc == '0':
            # false
            self._getc() # eat the '0'
            return False
        elif cc == '1':
            # true
            self._getc() # eat the '1'
            return True
        elif cc in ('F', 'f'):
            # false, must check for F|f|false|FALSE
            if self._get_re(_false_regex) is None:
                self._error("Expected 'false' token")
            return False
        elif cc in ('T', 't'):
            # true, must check for T|t|true|TRUE
            if self._get_re(_true_regex) is None:
                self._error("Expected 'true' token")
            return True
        elif cc == 'i':
            # 'i' = integer
            return self._parse_integer()
        elif cc == ('r'):
            # 'r' = real number
            return self._parse_real()
        elif cc == 'u':
            # 'u' = uuid
            return self._parse_uuid()
        elif cc in ("'", '"', 's'):
            # string
            return self._parse_string()
        elif cc == 'l':
            # 'l' = uri
            return self._parse_uri()
        elif cc == ('d'):
            # 'd' = date in seconds since epoch
            return self._parse_date()
        elif cc == 'b':
            return self._parse_binary()
       
        # output error if the token wasn't handled
        self._error("Invalid token %d" % ord(cc))

    def _parse_binary(self):
        "parse a single binary object."
        
        self._getc()    # eat the beginning 'b'
        cc = self._peek()
        if cc == '(':
            # parse raw binary
            paren = self._getc()

            # grab the 'expected' size of the binary data
            size = self._get_undil(')')
            if size == None:
                self._error("Invalid binary size")
            size = int(size)

            # grab the opening quote
            q = self._getc()
            if q != '"':
                self._error('Expected " to start binary value')

            # grab the data
            data = self._getc(size)

            # grab the closing quote
            q = self._getc()
            if q != '"':
                self._error('Expected " to end binary value')

            return binary(data)

        else:
            # get the encoding base
            base = self._getc(2)
            if base not in ('16', '64'):
                self._error('Found unsupported binary encoding')

            # grab the double quote
            q = self._getc()
            if q != '"':
                self._error('Expected " to start binary value')

            # grab the encoded data
            encoded = self._get_until(q)

            try:
                if base == '16':
                    # parse base16 encoded data
                    return binary(base64.b16decode(encoded or ''))
                elif base == '64':
                    # parse base64 encoded data
                    return binary(base64.b64decode(encoded or ''))
                elif base == '85':
                    self._error("Parser doesn't support base85 encoding")
            except binascii.Error, exc:
                # convert exception class so it's more catchable
                self._error("Encoded binary data: " + str(exc))
            except exceptions.TypeError, exc:
                # convert exception class so it's more catchable
                self._error("Bad binary data: " + str(exc))
    
    def _parse_map(self):
        """
        parse a single map

        map: { string:object, string:object }
        """
        rv = {}
        key = ''
        found_key = False
        self._getc()   # eat the beginning '{'
        cc = self._peek()
        while (cc != '}'):
            if cc is None:
                self._error("Unclosed map")
            if not found_key:
                if cc in ("'", '"', 's'):
                    key = self._parse_string()
                    found_key = True
                elif cc.isspace() or cc == ',':
                    self._getc()    # eat the character
                    pass
                else:
                    self._error("Invalid map key")
            elif cc.isspace():
                self._getc()    # eat the space
                pass
            elif cc == ':':
                self._getc()    # eat the ':'
                value = self._parse()
                rv[key] = value
                found_key = False
            else:
                self._error("missing separator")
            cc = self._peek()

        if self._getc() != '}':
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
        while (cc != ']'):
            if cc is None:
                self._error('Unclosed array')
            if cc.isspace() or cc == ',':
                self._getc()
                cc = self._peek()
                continue
            rv.append(self._parse())
            cc = self._peek()

        if self._getc() != ']':
            self._error("Invalid array close token")
        return rv

    def _parse_uuid(self):
        "Parse a uuid."
        self._getc()    # eat the beginning 'u'
        return uuid.UUID(hex=self._getc(36))

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
        match = self._get_re(_real_regex)
        if match == None:
            self._error("Invalid real token")
        return float(match)

    def _parse_integer(self):
        "Parse an integer."
        self._getc()    # eat the beginning 'i'
        match = self._get_re(_int_regex)
        if match == None:
            self._error("Invalid integer token")
        return int(match)

    def _parse_string(self):
        """
        Parse a string

        string: "g\'day" | 'have a "nice" day' | s(size)"raw data"
        """
        rv = ""
        delim = self._peek()
        if delim in ("'", '"'):
            rv = self._parse_string_delim()
        elif delim == 's':
            rv = self._parse_string_raw()
        else:
            self._error("invalid string token")

        return rv

    def _parse_string_delim(self):
        """
        Parse a delimited string

        string: "g'day 'un" | 'have a "nice" day'
        """
        parts = []
        found_escape = False
        found_hex = False
        found_digit = False
        byte = 0
        delim = self._getc()    # get the delimeter
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
                        parts.append(chr(byte))
                        byte = 0
                    else:
                        found_digit = True
                        byte = _hex_as_nybble(cc)
                elif cc == 'x':
                    found_hex = True
                else:
                    if cc == 'a':
                        parts.append('\a')
                    elif cc == 'b':
                        parts.append('\b')
                    elif cc == 'f':
                        parts.append('\f')
                    elif cc == 'n':
                        parts.append('\n')
                    elif cc == 'r':
                        parts.append('\r')
                    elif cc == 't':
                        parts.append('\t')
                    elif cc == 'v':
                        parts.append('\v')
                    else:
                        parts.append(cc)
                    found_escape = False
            elif cc == '\\':
                found_escape = True
            elif cc == delim:
                break
            else:
                parts.append(cc)
        try:
            return ''.join(parts).decode('utf-8')
        except UnicodeDecodeError, exc:
            raise LLSDParseError(exc)

    def _parse_string_raw(self):
        """
        Parse a sized specified string.

        string: s(size)"raw data"
        """ 
        self._getc()    # eat the beginning 's'
        # Read the (size) portion.
        cc = self._getc()
        if cc != '(':
            self._error("Invalid string token")

        size = self._get_until(')')
        if size == None:
            self._error("Invalid string size")
        size = int(size)

        delim = self._getc()
        if delim not in ("'", '"'):
            self._error("Invalid string token")

        rv = self._getc(size)
        cc = self._getc()
        if cc != delim:
            self._error("Invalid string closure token")
        try:
            return rv.decode('utf-8')
        except UnicodeDecodeError, exc:
            raise LLSDParseError(exc)

def format_binary(something):
    """
    Format application/llsd+binary to a python object.
 
    See http://wiki.secondlife.com/wiki/LLSD#Binary_Serialization

   :param something: a python object (typically a dict) to be serialized.
   :returns: Returns a LLSD binary formatted string.
    """
    return '<?llsd/binary?>\n' + _format_binary_recurse(something)

def _format_binary_recurse(something):
    "Binary formatter workhorse."
    def _format_list(something):
        array_builder = []
        array_builder.append('[' + struct.pack('!i', len(something)))
        for item in something:
            array_builder.append(_format_binary_recurse(item))
        array_builder.append(']')
        return ''.join(array_builder)

    if something is None:
        return '!'
    elif isinstance(something, LLSD):
        return _format_binary_recurse(something.thing)
    elif isinstance(something, bool):
        if something:
            return '1'
        else:
            return '0'
    elif isinstance(something, (int, long)):
        try:
            return 'i' + struct.pack('!i', something)
        except (OverflowError, struct.error), exc:
            raise LLSDSerializationError(str(exc), something)
    elif isinstance(something, float):
        try:
            return 'r' + struct.pack('!d', something)
        except SystemError, exc:
            raise LLSDSerializationError(str(exc), something)
    elif isinstance(something, uuid.UUID):
        return 'u' + something.bytes
    elif isinstance(something, binary):
        return 'b' + struct.pack('!i', len(something)) + something
    elif isinstance(something, str):
        return 's' + struct.pack('!i', len(something)) + something
    elif isinstance(something, unicode):
        something = something.encode('utf-8')
        return 's' + struct.pack('!i', len(something)) + something
    elif isinstance(something, uri):
        return 'l' + struct.pack('!i', len(something)) + something
    elif isinstance(something, datetime.datetime):
        seconds_since_epoch = calendar.timegm(something.utctimetuple()) \
                              + something.microsecond / 1e6
        return 'd' + struct.pack('<d', seconds_since_epoch)
    elif isinstance(something, datetime.date):
        seconds_since_epoch = calendar.timegm(something.timetuple())
        return 'd' + struct.pack('<d', seconds_since_epoch)
    elif isinstance(something, (list, tuple)):
        return _format_list(something)
    elif isinstance(something, dict):
        map_builder = []
        map_builder.append('{' + struct.pack('!i', len(something)))
        for key, value in something.items():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            map_builder.append('k' + struct.pack('!i', len(key)) + key)
            map_builder.append(_format_binary_recurse(value))
        map_builder.append('}')
        return ''.join(map_builder)
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
    if _startswith('<?llsd/binary?>', something):
        just_binary = something.split('\n', 1)[1]
    else:
        just_binary = something
    return LLSDBinaryParser().parse(just_binary)


declaration_regex = re.compile(r'^\s*(?:<\?[\x09\x0A\x0D\x20-\x7e]+\?>)|(?:<llsd>)')
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
    except ElementTreeError, err:
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

    :param something: The data to parse.
    :param mime_type: The mime_type of the data if it is known.
    :returns: Returns a python object.
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
        if _startswith('<?llsd/binary?>', something):
            return parse_binary(something)
        # This should be better.
        elif _startswith('<', something):
            return parse_xml(something)
        else:
            return parse_notation(something)
    except KeyError, e:
        raise LLSDParseError('LLSD could not be parsed: %s' % (e,))

class LLSD(object):
    "Simple wrapper class for a thing."
    def __init__(self, thing=None):
        self.thing = thing

    def __str__(self):
        return self.as_xml(self.thing)

    parse = staticmethod(parse)
    as_xml = staticmethod(format_xml)
    as_pretty_xml = staticmethod(format_pretty_xml)
    as_binary = staticmethod(format_binary)
    as_notation = staticmethod(format_notation)

undef = LLSD(None)
