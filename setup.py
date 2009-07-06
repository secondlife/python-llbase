#!/usr/bin/env python

import os.path
from distutils.core import setup, Extension

PACKAGE_NAME = 'llbase'
LLBASE_VERSION = '0.1.0'
LLBASE_SOURCE = 'src'
CLASSIFIERS = """\
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: MIT
Programming Language :: Python
Programming Language :: C
Topic :: Software Development
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Microsoft :: Windows
Operating System :: Unix
"""

sources = [os.path.join(LLBASE_SOURCE, "cllsd.c")]
cllsd_ext = Extension(PACKAGE_NAME + '._cllsd', sources)

setup(
    name=PACKAGE_NAME,
    version=LLBASE_VERSION,
    description='Base Linden Lab Pythoon modules',
    #author='',
    #author_email='',
    #url='http://bitbucket.org/phoenix_linden/llbase/',
    platforms=["any"],
    package_dir={PACKAGE_NAME:LLBASE_SOURCE},
    packages=[PACKAGE_NAME],
    license='MIT',
    classifiers=filter(None, CLASSIFIERS.split("\n")),
    requires=['eventlet', 'elementtree'],
    ext_modules=[cllsd_ext],
    )
