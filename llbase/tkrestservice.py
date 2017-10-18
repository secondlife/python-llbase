#!/usr/bin/python
"""\
@file   tkrestservice.py
@author Nat Goodspeed
@date   2016-10-30
@brief  Provide TkRESTService, an llrest.RESTService with Tk credentials prompts.

$LicenseInfo:firstyear=2016&license=internal$
Copyright (c) 2016, Linden Research, Inc.
$/LicenseInfo$
"""
from __future__ import absolute_import

try:
    from tkinter import Tk
    from tkinter.simpledialog import askstring
except ImportError: # Python 2
    from Tkinter import Tk
    from tkSimpleDialog import askstring

from .llrest import RESTService, RESTError
import os
import __main__                         # for filename of main script

root = None

class TkRESTService(RESTService):
    """
    TkRESTService is just like RESTService except that when authenticated is
    True but either username or password are omitted, it prompts using a Tk
    simple question dialog instead of prompting on the console.

    While it would be possible to create a specific dialog for the case in
    which both username and password are omitted, we have not (yet) taken that
    step. If so, you get two prompts in sequence.

    This TkRESTService is for use by console-based Python scripts because it
    expects there's no existing Tk root window.
    """

    def get_credentials(self):
        global root
        # only create and withdraw a dummy window on first use
        if root is None:
            root = Tk()
            # Don't show empty application window
            root.withdraw()

        # try to get filename of main script for window title -- if none,
        # use our own filename
        title = os.path.basename(getattr(__main__, "__file__", __file__))

        username, password = self.username, self.password

        if username is None:
            username = askstring(title, "%s username:" % self.name)
            if username is None:
                # user clicked Cancel
                raise RESTError(self.name, '', '000', "Prompt for username canceled")

        if password is None:
            password = askstring(title,
                                 "%s password for '%s':" % (self.name, username),
                                 show='*')
            if password is None:
                # user clicked Cancel
                raise RESTError(self.name, '', '000', "Prompt for password canceled")

        return (username, password)
