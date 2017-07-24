#!/usr/bin/env python
# file: llidl_speed_test.py
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
Performance tests for llidl
"""
from __future__ import print_function
from __future__ import division

import random
import string
import time

from llbase import llidl

def random_string():
    s = random.choice(string.ascii_uppercase)
    for i in range(1,random.randint(2,11)):
        s += random.choice(string.ascii_lowercase)
    return s

def time_llidl_match(n, k):
    value = llidl.parse_value("[ { name: [ string, string ], size: int }, ... ]")
    
    data_set = []
    for i in range(0,n):
        item = []
        for i in range(0, k // 5):
            n1 = random_string()
            n2 = random_string()
            s = random.randint(100,10000)
            item.append({'name': [ n1, n2 ], 'size': s})
        data_set.append(item)
        
    t = - time.time()
    c = - time.clock()
    
    for item in data_set:
        value.match(item, raises=True)
    
    c += time.clock()
    t += time.time()
    
    return (c,t)


def simple_llidl_match():
    (c,t) = time_llidl_match(1000, 100)
    
    print ("matched 1000 items of 100 values each")
    print ("%f process clock, %f wall clock" % (c, t))


def grid():
    trial_range = range(100,1100,100)
    size_range = range(0,550,50)
    
    print("trials,%s" % (",".join(["%d items" % d for d in size_range])))
    for n in trial_range:
        cs = []
        for k in size_range:
            (c,t) = time_llidl_match(n,k)
            cs.append(c)
        print("%d,%s" % (n, ','.join(map(str, cs))))
    
if __name__ == '__main__':
    simple_llidl_match()
    #grid()
