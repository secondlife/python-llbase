#!/usr/bin/env python
"""\
@file cllsd_test.py
@brief Types as well as parsing and formatting functions for handling LLSD.

$LicenseInfo:firstyear=2008&license=mit$

Copyright (c) 2008-2009, Linden Research, Inc.

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


from datetime import datetime
import os.path
import sys
import time
import uuid


# *HACK: in order to import a private library module, we have to dip
# into the actual module level and import it there. Modify and restore
old_first = sys.path[0]
sys.path[0] = os.path.join(old_first, 'llbase')
import _cllsd as cllsd
sys.path[0] = old_first

from llbase import llsd


class myint(int):
    pass

values = (
    '&<>',
    u'\u81acj',
    llsd.uri('http://foo<'),
    uuid.UUID(int=0),
    llsd.LLSD(['thing']),
    1,
    myint(31337),
    sys.maxint + 10,
    llsd.binary('foo'),
    [],
    {},
    {u'f&\u1212': 3},
    3.1,
    True,
    None,
    datetime.fromtimestamp(time.time()),
    )

def valuator(values):
    for v in values:
        yield v

def test():
    longvalues = () # (values, list(values), iter(values), valuator(values))

    for v in values + longvalues:
        print '%r => %r' % (v, cllsd.llsd_to_xml(v))

    a = [[{'a':3}]] * 1000000

    s = time.time()
    print hash(cllsd.llsd_to_xml(a))
    e = time.time()
    t1 = e - s
    print t1

    s = time.time()
    print hash(llsd.LLSDXMLFormatter()._format(a))
    e = time.time()
    t2 = e - s
    print t2

    print 'Speedup:', t2 / t1
