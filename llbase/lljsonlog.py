from __future__ import absolute_import

from datetime import datetime
import json
import logging
import traceback

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
#                 '()': 'lljsonlog.JsonFormatter',
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
UNINTERESTING_LOGRECORD_KEYS = {'args', 'created', 'exc_info', 'exc_text', 'filename', 'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs', 'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated', 'thread', 'threadName'}
"""Uninteresting data found in a `logging.LogRecord` instance."""

class JsonFormatter(logging.Formatter):

    """A `logging.Formatter` that formats records as JSON objects."""

    def format(self, record):
        data = {
            'name': record.name,  # logger name
            'level': record.levelname,
            'msg': record.getMessage(),
            'time': datetime.fromtimestamp(record.created).isoformat() + 'Z',
        }
        if record.exc_info:
            exc_type, exc, exc_trace = record.exc_info
            data.update({
                'error_type': exc_type.__name__,
                'error_message': unicode(exc),
                'traceback': '\n'.join(traceback.format_tb(exc_trace, 10)),
            })

        # Include any 'extra' data.
        data.update({k: v for k, v in record.__dict__.items() if k not in UNINTERESTING_LOGRECORD_KEYS})

        return json.dumps(data, default=repr)
