# file lluuid.py
#
# $LicenseInfo:firstyear=2004&license=mit$
#
# Copyright (c) 2004-2009, Linden Research, Inc.
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
System uuid wrapper for our usage
"""

import uuid
try:
    # Python 2.6
    from hashlib import md5
except ImportError:
    # Python 2.5 and earlier
    from md5 import new as md5

def generate():
    "The linden c++ source code uses md5 UUID generation. Provide the api."
    m = md5()
    m.update(uuid.uuid1().bytes)
    return uuid.UUID(bytes = m.digest())

def is_str_uuid(id_str):
    """
    Check if a passed in string can be interpreted as a UUID. Returns
    True on success and False otherwise. This function essentially
    strips the hypens so both 589EF487-197B-4822-911A-811BB011716A and
    589EF487197B4822911A811BB011716A. will be treated as valid uuids.

    :param uuid_str: The string to test
    """
    try:
        the_id = uuid.UUID(id_str)
    except ValueError:
        return False
    return True
