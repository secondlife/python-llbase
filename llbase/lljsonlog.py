from __future__ import absolute_import

from datetime import datetime
import cgitb
import json
import logging
import time
import traceback

try:
    unicode
except NameError:
    # Python 3 compatibility: the type formerly known as unicode has become
    # plain str, but in Python 2 land we need to still be able to invoke it as
    # unicode.
    unicode = str
    # In Python 3, StringIO comes from the io module
    from io import StringIO
else:
    # In Python 2, use "classic" StringIO. Even though Python 2.6 introduced
    # an io.StringIO, the new StringIO.write() requires a unicode -- not str
    # -- argument. But since all the write() calls we care about are within
    # cgitb, which we don't control, we need something with a write() method
    # accepting str. We could wrap io.StringIO; but given StringIO.StringIO,
    # why bother?
    from StringIO import StringIO

try:
    dict.iteritems
except AttributeError:
    # Additional Python 3 compatability. Python 2's dict.iteritems is 3's dict.items
    iteritems = dict.items
else:
    iteritems = dict.iteritems

# This module provides a Python logging formatter that serializes messages into a JSON object suitable for logging to BNW MMA.
#
# Use handler.setFormatter() to set a handler's formatter to a `JsonFormatter` instance:
#
#     log_handler = logging.StreamHandler(sys.stderr)
#     log_handler.setFormatter( JsonFormatter() )
#
# For general documentation on how to use custom log formatters, see
# https://docs.python.org/2/library/logging.html?highlight=logging#logging.Handler.setFormatter
#
# In a Django project, specify it as a `json` formatter in the `LOGGING` config:
#
#     LOGGING = {
#         'version': 1,
#         'disable_existing_loggers': False,
#         'formatters': {
#             'json': {
#                 '()': 'llbase.lljsonlog.JsonFormatter',
#             },
#         },
#         'handlers': {
#             'stdout': {
#                 'level': 'DEBUG' if DEBUG else 'WARNING',
#                 'class': 'logging.StreamHandler',
#                 'formatter': 'json',
#             },
#         },
#         # ...
#     }
################################################################

# The uninteresting keys were discovered by dumping what's in a typical LogRecord's __dict__.
# Ideally we'd have a better way to figure these out, since technically then
# they could change with Python version. But eh.
UNINTERESTING_LOGRECORD_KEYS = {
    'args', 'created', 'exc_info', 'exc_text', 'filename', 'funcName', 'levelname', 'levelno',
    'lineno', 'module', 'msecs', 'msg', 'name', 'pathname', 'process', 'processName',
    'relativeCreated', 'stack_info', 'thread', 'threadName',
}
"""Uninteresting data found in a `logging.LogRecord` instance."""

try:
    # Python 2's basestring and long classes do not exist in Python 3
    DOCUMENTED_JSON_TYPES = (basestring, long)
except NameError:
    DOCUMENTED_JSON_TYPES = (str,)

DOCUMENTED_JSON_TYPES += (dict, list, tuple, int, float, bool, type(None))


class JsonFormatter(logging.Formatter):
    """A `logging.Formatter` that formats records as JSON objects."""

    def __init__(self, exception_formatter='traceback'):
        # Format times in GMT
        # https://docs.python.org/2/library/logging.html#formatter-objects
        self.converter = time.gmtime
        self._fmt_exc = self._fmt_exc_cgitb if exception_formatter == 'cgitb' else self._fmt_exc_traceback

    def format(self, record):
        data = {
            'name': record.name,  # logger name
            'level': record.levelname,
            'msg': record.getMessage(),
            'time': self.formatTime(record),
        }
        if record.exc_info:
            exc_type, exc, exc_trace = record.exc_info
            data.update({
                'error_type': exc_type.__name__,
                'error_message': unicode(exc),
                'traceback': self.formatException(record.exc_info),
            })

        # Include any 'extra' data filtered by a couple predicates. Generators are chained together
        # before enumeration to avoid extra work.
        items = iteritems(record.__dict__)
        items = ((k, v) for k, v in items if k not in UNINTERESTING_LOGRECORD_KEYS)
        items = ((k, v) for k, v in items if isinstance(v, DOCUMENTED_JSON_TYPES))
        data.update(items)

        return json.dumps(data, sort_keys=True)

    def formatTime(self, record, datefmt=None):
        if datefmt:
            # If caller explicitly passed a time.strftime() format, use it as
            # directed. Convert to gmtime() or localtime() according to our
            # converter attribute.
            return time.strftime(datefmt, self.converter(record.created))
        else:
            # If caller did not pass datefmt, use datetime.isoformat() to
            # include microseconds, which time.strftime() cannot support
            # because time.struct_time() has no field for fractional seconds.
            return datetime.fromtimestamp(record.created).isoformat() + 'Z'

    def formatException(self, exc_info):
        return self._fmt_exc(exc_info)

    @staticmethod
    def _fmt_exc_traceback(exc_info):
        _, _, exc_trace = exc_info
        return ''.join(traceback.format_tb(exc_trace, 10))

    @staticmethod
    def _fmt_exc_cgitb(exc_info):
        # cgitb.Hook writes its output to the file-like object provided to its
        # constructor. As we don't want to accumulate successive formatted
        # exceptions, we need a new StringIO instance every time. (There is no
        # method to clear a StringIO instance.) But as there is also no method
        # to replace the stream used by a Hook instance, we must therefore
        # instantiate a new Hook every time.
        stream = StringIO()
        hook = cgitb.Hook(file=stream, format='text')
        hook.handle(exc_info)
        return stream.getvalue()
