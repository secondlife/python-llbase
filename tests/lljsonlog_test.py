#!/usr/bin/python
"""\
@file   lljsonlog_test.py
@author Nat Goodspeed
@date   2018-02-21
@brief  test lljsonlog module

$LicenseInfo:firstyear=2018&license=mit$
Copyright (c) 2018, Linden Research, Inc.
$/LicenseInfo$
"""

from __future__ import print_function

import json
import logging
import sys
import unittest

# use whichever StringIO implementation is used by lljsonlog
from llbase.lljsonlog import JsonFormatter, StringIO

class Error(Exception):
    pass

class LLJsonLogTester(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test")
        self.stream = StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        ##print("\ntearDown():", self.stream.getvalue(), file=sys.stderr)
        pass

    def parseLastLine(self):
        # It would be good to also verify that the number of lines in
        # getvalue() matches the number of logging calls we've made so far,
        # but in practice that would make future test maintenance tricky. Just
        # take the last line and be happy.
        lastline = self.stream.getvalue().splitlines()[-1]
        # If lastline isn't valid JSON, will blow with ValueError
        blob = json.loads(lastline)
        # assert presence of keys, else KeyError
        blob["name"]
        blob["level"]
        blob["time"]
        blob["msg"]
        return blob

    def test_info(self):
        self.logger.info("info message")
        lines = self.stream.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        blob = self.parseLastLine()
        self.assertEqual(blob["name"], "test")
        self.assertEqual(blob["level"], "INFO")
        ##self.assertEqual(blob["time"], ...)  nope.
        self.assertEqual(blob["msg"], "info message")

    def test_debug(self):
        self.logger.debug("debug message")
        blob = self.parseLastLine()
        self.assertEqual(blob["level"], "DEBUG")
        self.assertEqual(blob["msg"], "debug message")

    def test_warning(self):
        self.logger.warning("warning message")
        blob = self.parseLastLine()
        self.assertEqual(blob["level"], "WARNING")
        self.assertEqual(blob["msg"], "warning message")

    def test_exception(self):
        try:
            raise Error("sample exception")
        except Error:
            self.logger.exception("exception happened")

        blob = self.parseLastLine()
        self.assertEqual(blob["name"], "test")
        self.assertEqual(blob["level"], "ERROR")
        self.assertEqual(blob["msg"], "exception happened")
        self.assertEqual(blob["error_message"], "sample exception")
        self.assertEqual(blob["error_type"], "Error")

        traceback = blob["traceback"]
        # look for certain signature cgitb output, in plain-text form (not HTML)
        assert "\nA problem occurred in a Python script." in traceback
        assert "\nThe above is a description of an error in a Python program." in traceback

if __name__ == '__main__':
    unittest.main()
